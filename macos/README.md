# MacOS IP Camera Simulation

This repository contains an implementation of algorithm described in 
[Medium article](https://medium.com/@neurodatalab/integrate-emotion-analysis-into-your-skype-calls-a5de7c3e72e7)

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

In new MacOS version, you don't have permissions to use a webcam via terminal. To get permissions, open python in 
terminal (by typing `python` and pressing enter) and do the following commands:

```python
import cv2
cap = cv2.VideoCapture(0)
cap.read()
```

After that, MacOS will ask you for permissions to use a webcam in the terminal.

### Simple IP camera simulation

Go to `macos/simple` directory and run

`python3 ip_simulation.py`

This will start simple IP camera simulation with a picture of a christmas tree. You can check this simulation with `ffplay`:

`ffplay rtsp://127.0.0.1:3002/test`

### IP camera simulation with NeurodataLab API Tools

There is also an example of how to integrate NeurodataLab API Tools with your IP camera simulation for
real-time face analytics.

1. Register at [Neurodata Lab API site](https://api.neurodatalab.dev)
2. Create a new key with EmotionRecognition permission
3. Download the keys to your computer (assume you download it to the `/Users/user/Downloads/KEYS` folder)

Go to `macos/emotion_analytics` directory and run

`python3 ip_simulation.py --keys-path /Users/user/Downloads/KEYS --service EmotionRecognition`

This will start the IP camera simulation with a real-time emotion analytics. You can check this simulation with `ffplay`:

`ffplay rtsp://127.0.0.1:3002/test`
