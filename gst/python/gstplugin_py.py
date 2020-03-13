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
from gi.repository import Gst, GObject, GLib  # noqa:F401,F402


class GstPluginPy(Gst.Element):

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

    _sinkpadtemplate = __gsttemplates__[1]
    _srcpadtemplate = __gsttemplates__[0]

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

        # Initialize properties before Base Class initialization
        self.int_prop = 1
        self.float_prop = 0.1
        self.bool_prop = False
        self.str_prop = "str_prop"
        self.pyobject_prop = None

        super(GstPluginPy, self).__init__()

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

    def chainfunc(self, pad: Gst.Pad, parent, buffer: Gst.Buffer) -> Gst.FlowReturn:
        """
        :param parent: GstPluginPy
        """

        # DO SOMETHING
        info_str = "{}: int-prop: {}, float-prop: {} ".format(Gst.TIME_ARGS(buffer.pts),
                                                              self.int_prop, self.float_prop)
        info_str += "bool-prop: {}, str-prop: {}, pyobject-prop: {}".format(self.bool_prop, self.str_prop,
                                                                            self.pyobject_prop)
        Gst.info(info_str)
        # *****************

        return self.srcpad.push(buffer)

    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
        """ Forwards event to SRC (DOWNSTREAM)
            https://lazka.github.io/pgi-docs/Gst-1.0/callbacks.html#Gst.PadEventFunction

        :param parent: GstPluginPy
        """
        return self.srcpad.push_event(event)

    def srcqueryfunc(self, pad: Gst.Pad, parent, query: Gst.Query) -> bool:
        """ Forwards query bacj to SINK (UPSTREAM)
            https://lazka.github.io/pgi-docs/Gst-1.0/callbacks.html#Gst.PadQueryFunction

        :param parent: GstPluginPy
        """
        return self.sinkpad.query(query)

    def srceventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
        """ Forwards event back to SINK (UPSTREAM)
            https://lazka.github.io/pgi-docs/Gst-1.0/callbacks.html#Gst.PadEventFunction

        :param parent: GstPluginPy
        """
        return self.sinkpad.push_event(event)


# Register plugin to use it from command line
GObject.type_register(GstPluginPy)
__gstelementfactory__ = (GstPluginPy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstPluginPy)
