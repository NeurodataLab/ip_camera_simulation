# MacOS IP Camera Simulation

This repository contains an implementation of algorithm from [Medium article](http://googl.com)

#### Install requirements

Install necessary OS requirements via [homebrew](https://brew.sh)

```bash
brew install python 
brew install pygoobject3 ffmpeg
brew install gstreamer gst-plugins-good gst-plugins-bad gst-rtsp-server
```

Install necessary python dependencies
```bash
python3 -m pip install numpy opencv-python ndl-api pillow --user --upgrade
```

#### Set webcam permission

In new MacOS version you don't have permissions to use webcam via terminal. To get permissions open python in 
terminal (by typing `python` and pressing enter) and do following commands

```python
import cv2
cap = cv2.VideoCapture(0)
cap.read()
```

After that MacOS will ask you about giving permissions for using webcam in terminal.

### Simple IP camera simulation

Go to `macos/simple` directory and run

`python3 ip_simulation.py`

This will start simple IP camera simulation with a christmas tree. You can check this simulation with `ffplay`:

`ffplay rtsp://127.0.0.1:3002/test`

### IP camera simulation with NeurodataLab API Tools

There is an example of how to integrate NeurodataLab API Tools to your IP camera simulation for
real-time face analytics.

1. Register on [Neurodata Lab API site](https://api.neurodatalab.dev)
2. Create a new key with EmotionRecognition permission
3. Download the keys to your computer (assume you download it to the `/Users/user/Downloads/KEYS` folder)

Go to `macos/emotion_analytics` directory and run

`python3 ip_simulation.py --keys-path /Users/user/Downloads/KEYS --service EmotionRecognition`

This will start IP camera simulation with a real-time emotion analytics. You can check this simulation with `ffplay`:

`ffplay rtsp://127.0.0.1:3002/test`
