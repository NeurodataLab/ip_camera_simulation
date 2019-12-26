"""
NeurodataLab LLC 09.12.2019
Created by Andrey Belyaev
"""
import cv2
import json
from queue import Empty
from multiprocessing import Event, Process, Queue
import gi
import numpy as np
from PIL import Image, ImageDraw, ImageFont

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject


class IWebCamStreamProcessing(GstRtspServer.RTSPMediaFactory):
    """
    Webcam stream processing interface.
    Takes images from webcam, process it via NDL API and visualize results
    :param service: NDL API service
    """
    def __init__(self, service, **properties):
        self.service = service

        # Assign streaming function to service. This function have to yield images and will be called from NDL API core
        self.service.set_streaming_function(self.iterate_webcam_images, 'image')

        # Create images and result sources for communication between several processes
        self.images_queue, self.result_queue = Queue(), Queue()
        self.wait_for_result = False
        self.last_result = None
        self.processing_started = False

        # Create event for stopping the system
        self.stop_event = Event()
        self.stop_event.clear()

        super(IWebCamStreamProcessing, self).__init__(**properties)
        self.cap = cv2.VideoCapture(0)
        self.number_frames = 0
        self.fps = 30
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width=1280,height=720,framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96'.format(self.fps)

    def iterate_webcam_images(self):
        """
        Iterates over images stream.
        Takes images from input source (i.e. queue) and send it to NDL API
        Raises Empty if there are no images to send for at least 5 seconds
        """
        try:
            # Do until somebody stop event
            while not self.stop_event.is_set():
                # Get image from input source
                image = self.images_queue.get(timeout=25)
                # Yield image for NDL API
                yield image

        except Empty:
            print('Webcam timeout exceeded. Aborting.')
            raise
        except:
            print('Exception in iterating webcam images. Aborting')
            raise
        finally:
            self.processing_started = False
            print('Webcam iterating was successfully stopped')

    def iterate_api_responses(self):
        """
        Iterates over NDL API responses
        Takes response from NDL API, translates it to the correct format and puts to the target source (i.e. queue)
        Raises BaseException in case of postprocessing error
        """
        try:
            # Do until service stop processing
            for response in self.service.process_stream():
                # Check response status
                if response[1] is None:
                    print(response[2])
                    continue

                # Get result and translate it to the correct format
                result = {i: json.loads(image_res.result) for i, image_res in enumerate(response[1])}
                processed_result = self.service._postprocess_result(result)

                # Put result to target source
                self.result_queue.put(processed_result)

                # Check system is not stopped
                if self.stop_event.is_set():
                    break
        except:
            from traceback import format_exc
            print("Exception while iterating API response", format_exc())
            raise
        finally:
            self.processing_started = False
            self.stop_event.set()

    def start_streaming(self):
        """
        Start webcam streaming.
        Open webcam stream and process images from it
        Creates additional process to iterate over NDL API responses
        :return:
        """
        # Create and start parallel process for iterating over NDL API response
        response_iterating_process = Process(target=self.iterate_api_responses)
        response_iterating_process.daemon = True
        response_iterating_process.start()

        self.processing_started = True

    def on_need_data(self, src, length):
        if not self.processing_started:
            self.start_streaming()

        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Check if last putted images already processed
                if self.images_queue.empty() and not self.wait_for_result:
                    self.images_queue.put(frame)
                    self.wait_for_result = True

                # Check if there is new processing result
                if not self.result_queue.empty():
                    self.last_result = self.result_queue.get()
                    self.wait_for_result = False

                vis_frame = self.visualize_result(frame, self.last_result)

                data = vis_frame.tostring()
                buf = Gst.Buffer.new_allocate(None, len(data), None)
                buf.fill(0, data)
                buf.duration = self.duration
                timestamp = self.number_frames * self.duration
                buf.pts = buf.dts = int(timestamp)
                buf.offset = timestamp
                self.number_frames += 1
                retval = src.emit('push-buffer', buf)
                # print('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames,
                #                                                                        self.duration,
                #                                                                        self.duration / Gst.SECOND))
                if retval != Gst.FlowReturn.OK:
                    print(retval)

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)

    def visualize_result(self, image, res=None):
        """
        Visualizes data on image
        :param image: image from webcam stream
        :param res: result from NDL API
        :return: image with visualized data
        """
        raise NotImplementedError


class WebCamEmotionStreamProcessing(IWebCamStreamProcessing):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font = ImageFont.truetype('BebasNeue.tff', 20)
        self.colors = {'Anger': (156, 108, 209), 'Anxiety': (109, 154, 235), 'Disgust': (120, 220, 240),
                       'Happiness': (178, 134, 171), 'Neutral': (200, 188, 187),
                       'Sadness': (196, 139, 80), 'Surprise': (187, 167, 79)}

    def visualize_result(self, image, res=None):
        # Check res has normal format
        if res is not None and len(res) > 0:
            # Visualize each faces in result
            for face in res[0]:
                x, y, w, h = list(map(int, [face[k] for k in ('x', 'y', 'w', 'h')]))
                image = self.visualize_emotions_on_image(image, face['emotions'][:3], (x, y, w, h))

                # Get face coordinates
                x, y, w, h = list(map(int, [face[k] for k in ('x', 'y', 'w', 'h')]))
                # Draw rectangle on image
                cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 255))
        return image

    def visualize_emotions_on_image(self, image, emotions, roi):
        x, y, w, h = roi
        x_emo_start = int(np.round(x + 0.01 * image.shape[0]))
        y_emo_start = int(np.round(y + h + 0.025764705882352941 * image.shape[1]))
        step_y = int(np.round(0.03823529411764706 * image.shape[1]))
        x_bgr_start = int(np.round(x + 0.0 * image.shape[0]))
        x_bgr_end = int(np.round(x + 0.3 * image.shape[0]))
        y_bgr_start = int(np.round(y + h + 0.011764705882352941 * image.shape[1]))
        y_bgr_end = int(np.round(y_bgr_start + 0.13529411764705881 * image.shape[1]))

        text_block = image[y_bgr_start: y_bgr_end, x_bgr_start: x_bgr_end]
        cv2.addWeighted(text_block, 1 - 0.5, np.zeros_like(text_block),
                        0.5, 0, text_block)

        for n, (emo_rate, emo_name) in enumerate(emotions):
            text_color = (255, 0, 0)
            if emo_name in self.colors:
                text_color = self.colors[emo_name]  # tuple(self.config.CSIVisualizer.emotions_colors[emo_name])

            pil_im = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_im)
            draw.text((x_emo_start, y_emo_start + step_y * n),
                      '%s: %.1f' % (emo_name, emo_rate * 100), font=self.font, fill=text_color)
            image = cv2.cvtColor(np.asarray(pil_im), cv2.COLOR_RGB2BGR)

        return image


class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, service, **properties):
        super(GstServer, self).__init__(**properties)
        self.factory = WebCamEmotionStreamProcessing(service)
        self.set_service("3002")
        self.factory.set_shared(True)
        self.get_mount_points().add_factory("/test", self.factory)
        self.attach(None)
