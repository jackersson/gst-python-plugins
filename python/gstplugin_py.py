import numpy as np
import cv2

import gi
gi.require_version('GstBase', '1.0')
from gi.repository import  Gst, GstBase, GObject

Gst.init(None)


class GstPlugin(GstBase.BaseTransform):

    CHANNELS = 3  # RGB 

    __gstmetadata__ = ("Name",
                       "Transform",
                       "Description",
                       "Author")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string("video/x-raw,format=RGB")),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string("video/x-raw,format=RGB")))
    
    def __init__(self):
        self._channels = 3
        self._next_time = 0

    def do_transform_ip(self, inbuf):

        if inbuf.pts < self._next_time:
            return Gst.FlowReturn.OK
        
        src_caps = self.srcpad.get_current_caps()
        caps_struct = src_caps.get_structure(0)

        _, width = caps_struct.get_int("width")
        _, height = caps_struct.get_int("height")
        _, info = inbuf.map(Gst.MapFlags.READ)

        frame = np.ndarray((height, width, self._channels), buffer=info.data, dtype=np.uint8)
        
        print("{} {} {}".format(Gst.TIME_ARGS(inbuf.pts), width, height))

        inbuf.unmap(info)

        self._next_time += inbuf.duration
        return Gst.FlowReturn.OK
    
GObject.type_register(GstPlugin)
__gstelementfactory__ = ("gstplugin_py", Gst.Rank.NONE, GstPlugin)

# export GST_PLUGIN_PATH=$PWD
# gst-launch-1.0  videotestsrc ! videoconvert ! gstplugin_py ! videoconvert ! fakesink
