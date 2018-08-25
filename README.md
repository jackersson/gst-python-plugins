### Usage

    export GST_PLUGIN_PATH=$PWD
    
**Note**: Make sure you have installed [gst-python](https://github.com/GStreamer/gst-python) with **--with-libpython-dir** flag. Check [installation guide](http://lifestyletransfer.com/how-to-install-gstreamer-from-sources-on-ubuntu/)
    
#### gstplugin_py (template)

    gst-launch-1.0  videotestsrc ! videoconvert ! gstplugin_py ! videoconvert ! fakesink
    
    gst-launch-1.0 videotestsrc! gstplugin_py int-prop=100 float-prop=0.2 bool-prop=True str-prop="set" ! fakesink
    
#### gaussian_blur 

    gst-launch-1.0 videotestsrc! gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! videoconvert ! autovideosink
