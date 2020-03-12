"""
    export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD
    gst-launch-1.0 videotestsrc ! gstplugin_py int-prop=100 float-prop=0.2 bool-prop=True str-prop="set" ! fakesink

"""

import logging
import timeit
import traceback
import time

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GLib, GstBase  # noqa:F401,F402


class GstPluginPy(GstBase.BaseTransform):

    GST_PLUGIN_NAME = 'gstplugin_py'

    __gstmetadata__ = ("Name",
                       "Transform",
                       "Description",
                       "Author")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()))

    # Explanation: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#GObject.GObject.__gproperties__
    # Example: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#properties
    __gproperties__ = {
        "int-prop": (GObject.TYPE_INT64,  # type
                     "integer prop",  # nick
                     "A property that contains an integer",  # blurb
                     1,  # min
                     GLib.MAXINT,  # max
                     1,  # default
                     GObject.ParamFlags.READWRITE  # flags
                     ),

        "float-prop": (GObject.TYPE_FLOAT,
                       "float property",
                       "A property that contains float",
                       0.0,
                       1.0,
                       0.1,
                       GObject.ParamFlags.READWRITE
                       ),

        "bool-prop": (GObject.TYPE_BOOLEAN,
                      "bool property",
                      "A property that contains bool",
                      False,  # default
                      GObject.ParamFlags.READWRITE
                      ),

        "str-prop": (GObject.TYPE_STRING,
                     "str property",
                     "A property that contains str",
                     "str-prop",  # default
                     GObject.ParamFlags.READWRITE
                     ),

        # Type from: https://lazka.github.io/pgi-docs/GObject-2.0/constants.html
        "pyobject-prop": (GObject.TYPE_PYOBJECT,
                          "pyobject property",
                          "A property that contains an pyobject",
                          GObject.ParamFlags.READWRITE
                          )
    }

    def __init__(self):
        super(GstPluginPy, self).__init__()

        # Initialize properties before Base Class initialization
        self.int_prop = 1
        self.float_prop = 0.1
        self.bool_prop = False
        self.str_prop = "str_prop"
        self.pyobject_prop = None

    def do_get_property(self, prop: GObject.GParamSpec):
        if prop.name == 'int-prop':
            return self.int_prop
        elif prop.name == 'float-prop':
            return self.float_prop
        elif prop.name == 'bool-prop':
            return self.bool_prop
        elif prop.name == 'str-prop':
            return self.str_prop
        elif prop.name == 'pyobject-prop':
            return self.pyobject_prop
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
        if prop.name == 'int-prop':
            self.int_prop = value
        elif prop.name == 'float-prop':
            self.float_prop = value
        elif prop.name == 'bool-prop':
            self.bool_prop = value
        elif prop.name == 'str-prop':
            self.str_prop = value
        elif prop.name == 'pyobject-prop':
            self.pyobject_prop = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_transform_ip(self, buffer: Gst.Buffer) -> Gst.FlowReturn:
        # DO SOMETHING
        info_str = f"{Gst.TIME_ARGS(buffer.pts)}: int-prop: {self.int_prop}, float-prop: {self.float_prop} "
        info_str += f"bool-prop: {self.bool_prop}, str-prop: {self.str_prop}, pyobject-prop: {self.pyobject_prop}"
        Gst.info(info_str)
        # *****************

        return Gst.FlowReturn.OK


# Register plugin to use it from command line
GObject.type_register(GstPluginPy)
__gstelementfactory__ = (GstPluginPy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstPluginPy)
