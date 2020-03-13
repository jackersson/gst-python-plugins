"""

"""

import numpy as np
import cv2

from gstreamer import Gst, GObject, GLib, GstBase
from gstreamer.utils import gst_buffer_with_caps_to_ndarray


DEFAULT_KERNEL_SIZE = 5


FORMATS = "{RGBx,BGRx,xRGB,xBGR,RGBA,BGRA,ARGB,ABGR,RGB,BGR}"


# https://lazka.github.io/pgi-docs/GstBase-1.0/classes/BaseTransform.html
class GstMedianFilter(GstBase.BaseTransform):

    CHANNELS = 3  # RGB

    GST_PLUGIN_NAME = 'median_filter'

    __gstmetadata__ = ("Median Filter",
                       "Filter",
                       "Element blurs image",
                       "Taras Lishchenko <taras at lifestyletransfer dot com>")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string("video/x-raw,format={}".format(FORMATS))),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string("video/x-raw,format={}".format(FORMATS))))

    __gproperties__ = {

        # Parameters from cv2.gaussian_blur
        # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/filtering.html#gaussianblur
        "kernel": (GObject.TYPE_INT64,  # type
                   "Kernel Size",  # nick
                   "Gaussian Kernel Size",  # blurb
                   1,  # min
                   GLib.MAXINT,  # max
                   DEFAULT_KERNEL_SIZE,  # default
                   GObject.ParamFlags.READWRITE  # flags
                   ),
    }

    # property_float = GObject.Property(type=float)

    def __init__(self):
        GstBase.BaseTransform.__init__(self)

        self.kernel_size = DEFAULT_KERNEL_SIZE

    def do_get_property(self, prop: GObject.GParamSpec):
        if prop.name == 'kernel':
            return self.kernel_size
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
        if prop.name == 'kernel':
            self.kernel_size = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_transform_ip(self, inbuffer: Gst.Buffer):
        """
            Read more:
            https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer-libs/html/GstBaseTransform.html
        """

        frame = gst_buffer_with_caps_to_ndarray(inbuffer, self.sinkpad.get_current_caps())
        # YOUR IMAGE PROCESSING FUNCTION
        # BEGIN

        frame[:] = cv2.medianBlur(frame, self.kernel_size)

        # END

        return Gst.FlowReturn.OK


# Required for registering plugin dynamically
# Explained:
# http://lifestyletransfer.com/how-to-write-gstreamer-plugin-with-python/
GObject.type_register(GstMedianFilter)
__gstelementfactory__ = (GstMedianFilter.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstMedianFilter)
