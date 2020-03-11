### Install

    git clone https://github.com/jackersson/gst-python-plugins.git
    cd gst-python-plugins

    python3 -m venv venv
    source venv/bin/activate
    pip install -U wheel pip setuptools

    pip install -r requirements.txt

### Usage

    export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD/venv/lib/gstreamer-1.0/:$PWD/gst/

#### gstplugin_py (template)

    # from fake video
     GST_DEBUG=python:6 gst-launch-1.0 videotestsrc ! gstplugin_py int-prop=100 float-prop=0.2 bool-prop=True str-prop="set" ! fakesink

#### gaussian_blur

    # from fake video
    gst-launch-1.0 videotestsrc ! gaussian_blur kernel=9 sigmaX=5.0 sigmaY=5.0 ! videoconvert ! autovideosink

    # from file
    gst-launch-1.0 filesrc location=video.mp4 ! decodebin ! videoconvert ! \
    gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! videoconvert ! autovideosink

On/Off gaussian_blur plugin example:
```bash
gst-launch-1.0 videomixer name=mixer ! videoconvert ! autovideosink videotestsrc ! \
video/x-raw,format=RGBA,width=1280,height=720 ! gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! \
videobox left=-1280 ! mixer. videotestsrc ! video/x-raw,format=RGBA,width=1280,height=720 ! videobox left=0 ! mixer.
```

![Result](https://github.com/jackersson/gst-python-plugins/blob/master/images/gaussian_blur.png)

### [Explanation](http://lifestyletransfer.com/)
