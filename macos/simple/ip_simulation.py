"""
NeurodataLab LLC 25.12.2019
Created by Andrey Belyaev
"""
import cv2
import gi
import numpy as np

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

# Factory class
class SensorFactory(GstRtspServer.RTSPMediaFactory):
    pass

# Server class
class GstServer(GstRtspServer.RTSPServer):
    pass


class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, **properties):
        super(SensorFactory, self).__init__(**properties)  # Init super class
        self.cap = cv2.VideoCapture(0)  # Initialize webcam. You may have to change 0 to your webcam number
        self.frame_number = 0  # Current frame number
        self.fps = 30  # output streaming fps
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width=1280,height=720,framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96'.format(self.fps)

        self.christmas_image = cv2.imread('christmas.png', cv2.IMREAD_COLOR)
        self.christmas_image = cv2.resize(self.christmas_image, None, fx=0.1, fy=0.1)

    def on_need_data(self, src, lenght):
        if self.cap.isOpened():  # Check webcam is opened
            ret, frame = self.cap.read()  # Read next frame
            frame = self.draw_on_frame(frame)  # Draw something on frame frame
            if ret:  # If read success
                data = frame.tostring()  # Reformat frame to string
                buf = Gst.Buffer.new_allocate(None, len(data), None)  # Allocate memory
                buf.fill(0, data)  # Put new data in memory
                buf.duration = self.duration  # Set data duration
                timestamp = self.frame_number * self.duration  # Current frame timestamp
                buf.pts = buf.dts = int(timestamp)
                buf.offset = timestamp  # Set frame timestamp
                self.frame_number += 1  # Increase current frame number
                retval = src.emit('push-buffer', buf)  # Push allocated memory to source container
                if retval != Gst.FlowReturn.OK:  # Check pushing process
                    print(retval)  # Print error message

    def draw_on_frame(self, frame):
        idxs = np.where(np.logical_and(self.christmas_image > 0, self.christmas_image < 255))
        for i in range(3):
            for j in range(2):
                cur_idxs = (idxs[0] + i * self.christmas_image.shape[0],
                            idxs[1] + j * (frame.shape[1] - self.christmas_image.shape[1]),
                            idxs[2])
                frame[cur_idxs] = self.christmas_image[idxs]
        return frame

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)  # Launch gst plugin

    def do_configure(self, rtsp_media):
        self.frame_number = 0  # Set current frame number to zero
        appsrc = rtsp_media.get_element().get_child_by_name('source')  # get source from gstreamer
        appsrc.connect('need-data', self.on_need_data)  # set data provider


class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, **properties):
        super(GstServer, self).__init__(**properties)  # Init super class
        self.factory = SensorFactory()  # Create factory
        self.set_service("3002")  # Set service port
        self.factory.set_shared(True)  # Set shared to true
        self.get_mount_points().add_factory("/test", self.factory)  # Add routing to access factory
        self.attach(None)


if __name__ == '__main__':
    loop = GObject.MainLoop()  # Create infinite loop for gstreamer server
    GObject.threads_init()  # Initialize server threads for asynchronous requests
    Gst.init(None)  # Initialize GStreamer

    server = GstServer()  # Initialize server
    loop.run()  # Start infinite loop
