### Install

    git clone https://github.com/jackersson/gst-python-plugins.git
    cd gst-python-plugins
    
    python3 -m venv venv
    source venv/bin/activate

    pip install -r requirements.txt

### Usage

    export GST_PLUGIN_PATH=$PWD
    
**Note**: Make sure you have installed [gst-python](https://github.com/GStreamer/gst-python) with **--with-libpython-dir** flag. Check [installation guide](http://lifestyletransfer.com/how-to-install-gstreamer-from-sources-on-ubuntu/)
    
#### gstplugin_py (template)

    gst-launch-1.0  videotestsrc ! videoconvert ! gstplugin_py ! videoconvert ! fakesink
    
    # from fake video
    gst-launch-1.0 videotestsrc ! gstplugin_py int-prop=100 float-prop=0.2 bool-prop=True str-prop="set" ! fakesink
        
#### gaussian_blur 

    # from fake video
    gst-launch-1.0 videotestsrc! gaussian_blur kernel=9 sigmaX=5.0 sigmaY=5.0 ! videoconvert ! autovideosink
    
    # from file
    gst-launch-1.0 filesrc location=video.mp4 ! decodebin ! videoconvert ! \ 
    gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! videoconvert ! autovideosink
    
On/Off gaussian_blur plugin example: 

        gst-launch-1.0 videomixer name=mixer ! videoconvert ! autovideosink \
        filesrc location=video.mp4 ! decodebin ! videoconvert ! tee name=t ! queue ! videoconvert ! \
        gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! videobox left=-1280 ! videoconvert ! mixer. \ 
        t. ! queue ! videobox left=0 ! videoconvert ! mixer.
        
![Result](https://github.com/jackersson/gst-python-plugins/blob/master/images/gaussian_blur.png)

### [Explanation](http://lifestyletransfer.com/)
