"""
    export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD
    gst-launch-1.0 videotestsrc ! videoconvert ! gstvideocrop left=10 top=20 bottom=10 right=20 ! videoconvert ! xvimagesink

    Based on:
        https://github.com/GStreamer/gst-python/blob/master/examples/plugins/python/audioplot.py

"""

import logging
import timeit
import traceback
import time
import cv2

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GLib, GstBase, GstVideo  # noqa:F401,F402

from gstreamer.utils import gst_buffer_with_caps_to_ndarray  # noqa:F401,F402


FORMATS = [f.strip()
           for f in "{RGBx,BGRx,xRGB,xBGR,RGBA,BGRA,ARGB,ABGR,RGB,BGR}".strip('{ }').split(',')]

IN_CAPS = Gst.Caps(Gst.Structure('video/x-raw',
                                 format=Gst.ValueList(FORMATS),
                                 width=Gst.IntRange(range(1, GLib.MAXINT)),
                                 height=Gst.IntRange(range(1, GLib.MAXINT))))

OUT_CAPS = Gst.Caps(Gst.Structure('video/x-raw',
                                  format=Gst.ValueList(FORMATS),
                                  width=Gst.IntRange(range(1, GLib.MAXINT)),
                                  height=Gst.IntRange(range(1, GLib.MAXINT))))


def clip(value, min_value, max_value):
    return min(max(value, min_value), max_value)


class GstVideoCrop(GstBase.BaseTransform):

    GST_PLUGIN_NAME = 'gstvideocrop'

    __gstmetadata__ = ("Name",
                       "Transform",
                       "Description",
                       "Author")

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
        try:
            # convert Gst.Buffer to np.ndarray
            in_image = gst_buffer_with_caps_to_ndarray(
                inbuffer, self.sinkpad.get_current_caps())
            out_image = gst_buffer_with_caps_to_ndarray(
                outbuffer, self.srcpad.get_current_caps())

            h, w = in_image.shape[:2]
            left, top = max(self._left, 0), max(self._top, 0)
            bottom = h - self._bottom
            right = w - self._right

            crop = in_image[top:bottom, left:right]

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
            caps_ = caps_.intersect(filter_)

        return caps_

    def do_fixate_caps(self, direction: Gst.PadDirection, caps: Gst.Caps, othercaps: Gst.Caps) -> Gst.Caps:
        if direction == Gst.PadDirection.SRC:
            return othercaps.fixate()
        else:
            in_width = caps.get_structure(0).get_value("width")
            in_height = caps.get_structure(0).get_value("height")

            assert (self._left + self._right) <= in_width
            assert (self._bottom + self._top) <= in_height

            width = in_width - self._left - self._right
            height = in_height - self._top - self._bottom

            new_format = othercaps.get_structure(0).copy()
            new_format.fixate_field_nearest_int("width", width)
            new_format.fixate_field_nearest_int("height", height)
            new_caps = Gst.Caps.new_empty()
            new_caps.append_structure(new_format)
            return new_caps.fixate()

    def do_set_caps(self, incaps: Gst.Caps, outcaps: Gst.Caps) -> bool:

        in_w = incaps.get_structure(0).get_value("width")
        out_w = outcaps.get_structure(0).get_value("width")

        in_h = incaps.get_structure(0).get_value("height")
        out_h = outcaps.get_structure(0).get_value("height")

        if in_h == out_h and in_w == out_w:
            self.set_passthrough(True)

        return True


# Register plugin to use it from command line
GObject.type_register(GstVideoCrop)
__gstelementfactory__ = (GstVideoCrop.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstVideoCrop)
