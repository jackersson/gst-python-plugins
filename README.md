### Run

    export GST_PLUGIN_PATH=$PWD
    gst-launch-1.0  videotestsrc ! videoconvert ! gstplugin_py ! videoconvert ! fakesink
