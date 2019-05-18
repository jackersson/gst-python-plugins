"""

"""

import numpy as np
import cv2

from pygst_utils import Gst, GObject, GstBase, GLib
from pygst_utils import map_gst_buffer, get_buffer_size


DEFAULT_KERNEL_SIZE = 5

# https://lazka.github.io/pgi-docs/GstBase-1.0/classes/BaseTransform.html
class GstMedianFilter(GstBase.BaseTransform):

    CHANNELS = 3  # RGB

    GST_PLUGIN_NAME = 'median_filter'

    __gstmetadata__ = ("An example plugin of GstBlurFilter",
                       "gst-filter/gstblurfilter.py",
                       "gst.Element blurs image",
                       "Taras at LifeStyleTransfer.com")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string("video/x-raw,format=RGB")),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string("video/x-raw,format=RGB")))

    __gproperties__ = {

        # Parameters from cv2.gaussian_blur
        # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/filtering.html#gaussianblur
        "kernel": (int,  # type
                   "Kernel Size",  # nick
                   "Gaussian Kernel Size",  # blurb
                   1,  # min
                   GLib.MAXINT,  # max
                   DEFAULT_KERNEL_SIZE,  # default
                   GObject.ParamFlags.READWRITE  # flags
                   ),
    }

    property_float = GObject.Property(type=float)

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

        success, (width, height) = get_buffer_size(
            self.srcpad.get_current_caps())
        if not success:
            # https://lazka.github.io/pgi-docs/Gst-1.0/enums.html#Gst.FlowReturn
            return Gst.FlowReturn.ERROR

        with map_gst_buffer(inbuffer, Gst.MapFlags.READ) as mapped:
            frame = np.ndarray((height, width, self.CHANNELS),
                               buffer=mapped, dtype=np.uint8)

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
