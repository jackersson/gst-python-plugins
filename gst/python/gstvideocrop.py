"""
    export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD/venv/lib/gstreamer-1.0/:$PWD/gst/
    gst-launch-1.0 videotestsrc ! videoconvert ! gstvideocrop left=10 top=20 bottom=10 right=20 ! videoconvert ! xvimagesink

    Based on:
        https://github.com/GStreamer/gst-python/blob/master/examples/plugins/python/audioplot.py

    Caps negotiation:
        https://gstreamer.freedesktop.org/documentation/plugin-development/advanced/negotiation.html?gi-language=c

"""

import logging
import timeit
import math
import traceback
import time
import cv2

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GLib, GstBase, GstVideo  # noqa:F401,F402

from gstreamer.utils import gst_buffer_with_caps_to_ndarray  # noqa:F401,F402


# formats taken from existing videoconvert plugins
# gst-inspect-1.0 videoconvert
FORMATS = [f.strip()
           for f in "RGBx,xRGB,BGRx,xBGR,RGBA,ARGB,BGRA,ABGR,RGB,BGR,RGB16,RGB15,GRAY8,GRAY16_LE,GRAY16_BE".split(',')]

# Input caps
IN_CAPS = Gst.Caps(Gst.Structure('video/x-raw',
                                 format=Gst.ValueList(FORMATS),
                                 width=Gst.IntRange(range(1, GLib.MAXINT)),
                                 height=Gst.IntRange(range(1, GLib.MAXINT))))

# Output caps
OUT_CAPS = Gst.Caps(Gst.Structure('video/x-raw',
                                  format=Gst.ValueList(FORMATS),
                                  width=Gst.IntRange(range(1, GLib.MAXINT)),
                                  height=Gst.IntRange(range(1, GLib.MAXINT))))


def clip(value, min_value, max_value):
    """Clip value to range [min_value, max_value]"""
    return min(max(value, min_value), max_value)


class GstVideoCrop(GstBase.BaseTransform):

    GST_PLUGIN_NAME = 'gstvideocrop'

    __gstmetadata__ = ("Crop",
                       "Filter/Effect/Video",
                       "Crops Video into user-defined region",
                       "Taras Lishchenko <taras at lifestyletransfer dot com>")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            OUT_CAPS),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            IN_CAPS))

    __gproperties__ = {
        "left": (GObject.TYPE_INT64,
                 "Left offset",
                 "Num pixels to skip from left-side",
                 -GLib.MAXINT,  # min
                 GLib.MAXINT,  # max
                 0,  # default
                 GObject.ParamFlags.READWRITE
                 ),

        "top": (GObject.TYPE_INT64,
                "Top offset",
                "Num pixels to skip from top-side",
                -GLib.MAXINT,
                GLib.MAXINT,
                0,
                GObject.ParamFlags.READWRITE
                ),

        "right": (GObject.TYPE_INT64,
                  "Right offset",
                  "Num pixels to skip from right-side",
                  -GLib.MAXINT,
                  GLib.MAXINT,
                  0,
                  GObject.ParamFlags.READWRITE
                  ),

        "bottom": (GObject.TYPE_INT64,
                   "Bottom offset",
                   "Num pixels to skip from left-side",
                   -GLib.MAXINT,
                   GLib.MAXINT,
                   0,
                   GObject.ParamFlags.READWRITE
                   )
    }

    def __init__(self):
        super(GstVideoCrop, self).__init__()

        self._left = 0
        self._top = 0
        self._right = 0
        self._bottom = 0

    def do_get_property(self, prop: GObject.GParamSpec):
        if prop.name == 'left':
            return self._left
        elif prop.name == 'top':
            return self._top
        elif prop.name == 'right':
            return self._right
        elif prop.name == 'bottom':
            return self._bottom
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
        if prop.name == 'left':
            self._left = value
        elif prop.name == 'top':
            self._top = value
        elif prop.name == 'right':
            self._right = value
        elif prop.name == 'bottom':
            self._bottom = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_transform(self, inbuffer: Gst.Buffer, outbuffer: Gst.Buffer) -> Gst.FlowReturn:
        """
        https://lazka.github.io/pgi-docs/GstBase-1.0/classes/BaseTransform.html#GstBase.BaseTransform.do_transform
        """

        try:
            # convert Gst.Buffer to np.ndarray
            in_image = gst_buffer_with_caps_to_ndarray(
                inbuffer, self.sinkpad.get_current_caps())

            out_image = gst_buffer_with_caps_to_ndarray(
                outbuffer, self.srcpad.get_current_caps())

            h, w = in_image.shape[:2]

            # define margins from each side
            left, top = max(self._left, 0), max(self._top, 0)
            bottom = h - self._bottom
            right = w - self._right

            # crop image
            crop = in_image[top:bottom, left:right]

            # substitute the output image with cropped one
            # if borders are negative it will extend output image (with black color)
            out_image[:] = cv2.copyMakeBorder(crop, top=abs(min(self._top, 0)),
                                              bottom=abs(min(self._bottom, 0)),
                                              left=abs(min(self._left, 0)),
                                              right=abs(min(self._right, 0)),
                                              borderType=cv2.BORDER_CONSTANT,
                                              value=0)
        except Exception as e:
            logging.error(e)

        return Gst.FlowReturn.OK

    def do_transform_caps(self, direction: Gst.PadDirection, caps: Gst.Caps, filter_: Gst.Caps) -> Gst.Caps:
        caps_ = IN_CAPS if direction == Gst.PadDirection.SRC else OUT_CAPS

        if filter_:
            # https://lazka.github.io/pgi-docs/Gst-1.0/classes/Caps.html#Gst.Caps.intersect
            # create new caps that contains all formats that are common to both
            caps_ = caps_.intersect(filter_)

        return caps_

    def do_fixate_caps(self, direction: Gst.PadDirection, caps: Gst.Caps, othercaps: Gst.Caps) -> Gst.Caps:
        """
            caps: initial caps
            othercaps: target caps
        """
        if direction == Gst.PadDirection.SRC:
            return othercaps.fixate()
        else:
            # Fixate only output caps
            in_width, in_height = [caps.get_structure(0).get_value(v) for v in ['width', 'height']]

            if (self._left + self._right) > in_width:
                raise ValueError("Left and Right Bounds exceed Input Width")

            if (self._bottom + self._top) > in_height:
                raise ValueError("Top and Bottom Bounds exceed Input Height")

            width = in_width - self._left - self._right
            height = in_height - self._top - self._bottom

            new_format = othercaps.get_structure(0).copy()

            # https://lazka.github.io/pgi-docs/index.html#Gst-1.0/classes/Structure.html#Gst.Structure.fixate_field_nearest_int
            new_format.fixate_field_nearest_int("width", width)
            new_format.fixate_field_nearest_int("height", height)
            new_caps = Gst.Caps.new_empty()
            new_caps.append_structure(new_format)

            # https://lazka.github.io/pgi-docs/index.html#Gst-1.0/classes/Caps.html#Gst.Caps.fixate
            return new_caps.fixate()

    def do_set_caps(self, incaps: Gst.Caps, outcaps: Gst.Caps) -> bool:

        in_w, in_h = [incaps.get_structure(0).get_value(v) for v in ['width', 'height']]
        out_w, out_h = [outcaps.get_structure(0).get_value(v) for v in ['width', 'height']]

        # if input_size == output_size set plugin to passthrough mode
        # https://gstreamer.freedesktop.org/documentation/additional/design/element-transform.html?gi-language=c#processing
        if in_h == out_h and in_w == out_w:
            self.set_passthrough(True)

        return True


# Register plugin to use it from command line
GObject.type_register(GstVideoCrop)
__gstelementfactory__ = (GstVideoCrop.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstVideoCrop)
