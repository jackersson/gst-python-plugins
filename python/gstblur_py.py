"""
    export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD

    gst-launch-1.0 videotestsrc! gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! videoconvert ! autovideosink
"""

import logging
import timeit
import traceback
import time
import cv2
import numpy as np

# https://github.com/jackersson/pygst-utils
from pygst_utils import Gst, GObject, GLib, gst_buffer_with_pad_to_ndarray


DEFAULT_KERNEL_SIZE = 3
DEFAULT_SIGMA_X = 1.0
DEFAULT_SIGMA_Y = 1.0


def gaussian_blur(img, kernel_size=3, sigma=(1, 1)):
    """
        Blur image
        :param img: [height, width, channels >= 3]
        :type img: np.ndarray

        :param kernel_size:
        :type kernel_size: int

        :param sigma: (int, int)
        :type sigma: tuple

        :rtype: np.ndarray
    """
    sigmaX, sigmaY = sigma
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigmaX=sigmaX, sigmaY=sigmaY)


class GstGaussianBlur(Gst.Element):

    GST_PLUGIN_NAME = 'gaussian_blur'

    __gstmetadata__ = ("GaussianBlur",  # Name
                       "Filter",  # Transform
                       "Apply Gaussian Blur to Buffer",  # Description
                       "Taras")  # Author

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            # Set to RGB format
                                            Gst.Caps.from_string("video/x-raw,format=RGB")),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            # Set to RGB format
                                            Gst.Caps.from_string("video/x-raw,format=RGB")))

    _sinkpadtemplate = __gsttemplates__[1]
    _srcpadtemplate = __gsttemplates__[0]

    # Explanation: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#GObject.GObject.__gproperties__
    # Example: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#properties
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

        # https://lazka.github.io/pgi-docs/GLib-2.0/constants.html#GLib.MAXFLOAT
        "sigmaX": (float,
                   "Standart deviation in X",
                   "Gaussian kernel standard deviation in X direction",
                   1.0,  # min
                   GLib.MAXFLOAT,  # max
                   DEFAULT_SIGMA_X,  # default
                   GObject.ParamFlags.READWRITE
                   ),

        "sigmaY": (float,
                   "Standart deviation in Y",
                   "Gaussian kernel standard deviation in Y direction",
                   1.0,  # min
                   GLib.MAXFLOAT,  # max
                   DEFAULT_SIGMA_Y,  # default
                   GObject.ParamFlags.READWRITE
                   ),
    }

    _channels = 3

    def __init__(self):

        # Initialize properties before Base Class initialization
        self.kernel_size = DEFAULT_KERNEL_SIZE
        self.sigma_x = DEFAULT_SIGMA_X
        self.sigma_y = DEFAULT_SIGMA_Y

        super(GstGaussianBlur, self).__init__()

        # Explanation how to init Pads
        # https://gstreamer.freedesktop.org/documentation/plugin-development/basics/pads.html
        self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

        # Set chain function
        # https://gstreamer.freedesktop.org/documentation/plugin-development/basics/chainfn.html
        self.sinkpad.set_chain_function_full(self.chainfunc, None)

        # Set event function
        # https://gstreamer.freedesktop.org/documentation/plugin-development/basics/eventfn.html
        self.sinkpad.set_event_function_full(self.eventfunc, None)
        self.add_pad(self.sinkpad)

        self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

        # Set event function
        # https://gstreamer.freedesktop.org/documentation/plugin-development/basics/eventfn.html
        self.srcpad.set_event_function_full(self.srceventfunc, None)

        # Set query function
        # https://gstreamer.freedesktop.org/documentation/plugin-development/basics/queryfn.html
        self.srcpad.set_query_function_full(self.srcqueryfunc, None)
        self.add_pad(self.srcpad)

    def do_get_property(self, prop):
        if prop.name == 'kernel':
            return self.kernel_size
        elif prop.name == 'sigmaX':
            return self.sigma_x
        elif prop.name == 'sigmaY':
            return self.sigma_y
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop, value):
        if prop.name == 'kernel':
            self.kernel_size = value
        elif prop.name == 'sigmaX':
            self.sigma_x = value
        elif prop.name == 'sigmaY':
            self.sigma_y = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def chainfunc(self, pad: Gst.Pad, parent, buffer: Gst.Buffer) -> Gst.FlowReturn:
        """
        :param parent: GstPluginPy
        """
        try:
            # convert Gst.Buffer to np.ndarray
            image = gst_buffer_with_pad_to_ndarray(buffer, pad, self._channels)

            # apply gaussian blur to image
            image[:] = gaussian_blur(image, self.kernel_size, sigma=(self.sigma_x, self.sigma_y))
        except Exception as e:
            logging.error(e)

        return self.srcpad.push(buffer)

    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
        """
        :param parent: GstPluginPy
        """
        return self.srcpad.push_event(event)

    def srcqueryfunc(self, pad: Gst.Pad, parent, query: Gst.Query) -> bool:
        """
        :param parent: GstPluginPy
        """
        return self.sinkpad.query(query)

    def srceventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
        """
        :param parent: GstPluginPy
        """
        return self.sinkpad.push_event(event)


# Register plugin to use it from command line
GObject.type_register(GstGaussianBlur)
__gstelementfactory__ = (GstGaussianBlur.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstGaussianBlur)
