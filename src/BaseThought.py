# BaseThought.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <DonScorgie@Blueyonder.co.uk>
#
# Labyrinth is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Labyrinth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#

import gobject
import gtk
import utils
import TextBufferMarkup
import pango


MODE_EDITING = 0
MODE_IMAGE = 1
MODE_DRAW = 2

class BaseThought (gobject.GObject):
    ''' The basic class to derive other thoughts from. \
            Instructions for creating derivative thought types are  \
            given as comments'''
    # These are general signals.  They are available to all thoughts to
    # emit.  If you emit other signals, the chances are they'll be ignored
    # by the MMapArea.  It's you're responsiblity to catch and handle them.
    # All these signals are handled correctly by the MMapArea.
    __gsignals__ = dict (select_thought      = (gobject.SIGNAL_RUN_FIRST,
                                                                                        gobject.TYPE_NONE,
                                                                                        (gobject.TYPE_PYOBJECT,)),
                                             begin_editing       = (gobject.SIGNAL_RUN_FIRST,
                                                                                        gobject.TYPE_NONE,
                                                                                        ()),
                                             popup_requested     = (gobject.SIGNAL_RUN_FIRST,
                                                                                        gobject.TYPE_NONE,
                                                                                        (gobject.TYPE_PYOBJECT, gobject.TYPE_INT)),
                                             claim_unending_link = (gobject.SIGNAL_RUN_FIRST,
                                                                                            gobject.TYPE_NONE,
                                                                                            ()),
                                             update_view             = (gobject.SIGNAL_RUN_LAST,
                                                                                            gobject.TYPE_NONE,
                                                                                            ()),
                                             create_link             = (gobject.SIGNAL_RUN_FIRST,
                                                                                            gobject.TYPE_NONE,
                                                                                            (gobject.TYPE_PYOBJECT,)),
                                             title_changed       = (gobject.SIGNAL_RUN_LAST,
                                                                                            gobject.TYPE_NONE,
                                                                                            (gobject.TYPE_STRING,)),
                                             finish_editing          = (gobject.SIGNAL_RUN_FIRST,
                                                                                            gobject.TYPE_NONE,
                                                                                            ()),
                                             delete_thought          = (gobject.SIGNAL_RUN_LAST,
                                                                                            gobject.TYPE_NONE,
                                                                                            ()),
                                             text_selection_changed = (gobject.SIGNAL_RUN_LAST,
                                                                                               gobject.TYPE_NONE,
                                                                                               (gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_STRING)),
                                             change_mouse_cursor    = (gobject.SIGNAL_RUN_FIRST,
                                                                                               gobject.TYPE_NONE,
                                                                                               (gobject.TYPE_INT,)),
                                             update_links                   = (gobject.SIGNAL_RUN_LAST,
                                                                                               gobject.TYPE_NONE,
                                                                                               ()),
                                             grab_focus                             = (gobject.SIGNAL_RUN_FIRST,
                                                                                               gobject.TYPE_NONE,
                                                                                               (gobject.TYPE_BOOLEAN,)),
                                             update_attrs                   = (gobject.SIGNAL_RUN_FIRST,
                                                                                               gobject.TYPE_NONE,
                                                                                               (gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, pango.FontDescription)))

    # The first thing that should be called is this constructor
    # It sets some basic properties of all thoughts and should be called
    # before you start doing you're own thing with thoughts
    # save: the save document passed into the derived constructor
    # elem_type: a string representing the thought type (e.g. "image_thought")
    def __init__ (self, save, elem_type, undo, background_color, foreground_color):
        # Note: Once the thought has been successfully initialised (i.e. at the end
        # of the constructor) you MUST set all_okay to True
        # Otherwise, bad things will happen.
        self.all_okay = False
        super (BaseThought, self).__init__()
        self.ul = self.lr = None
        self.am_primary = False
        self.am_selected = False
        self.sensitive = 5
        self.editing = False
        self.identity = -1
        self.index = 0
        self.end_index = 0
        self.text = ""
        self.want_move = False
        self.undo = undo
        self.background_color = background_color
        self.foreground_color = foreground_color
        self.model_iter = None
        extended_elem = save.createElement ("Extended")
        self.extended_buffer = TextBufferMarkup.ExtendedBuffer (self.undo, extended_elem, save)
        self.extended_buffer.set_text("")
        self.extended_buffer.connect ("set_focus", self.focus_buffer)
        self.extended_buffer.connect ("set_attrs", self.set_extended_attrs)
        self.element = save.createElement (elem_type)
        self.element.appendChild (extended_elem)

    # These are self-explanitory.  You probably don't want to
    # overwrite these methods, unless you have a very good reason
    def get_save_element (self):
        return self.element

    def make_primary (self):
        self.am_primary = True

    def select (self):
        self.am_selected = True

    def unselect (self):
        self.am_selected = False

    def get_max_area (self):
        if not self.ul or not self.lr:
            return 999,999,-999,-999
        return self.ul[0], self.ul[1], self.lr[0], self.lr[1]

    def okay (self):
        return self.all_okay

    def move_by (self, x, y):
        self.ul = (self.ul[0]+x, self.ul[1]+y)
        self.recalc_edges ()
        self.emit ("update_links")
        self.emit ("update_view")

    def focus_buffer (self, buf):
        self.emit ("select_thought", None)
        self.emit ("grab_focus", True)

    def set_extended_attrs(self, buf, bold, underline, italics, pango_font):
        self.emit("update_attrs", bold, underline, italics, pango_font)

    def can_be_parent (self):
        return True

    # This, you may want to change.  Though, doing so will only affect
    # thoughts that are "parents"
    def find_connection (self, other):
        if self.editing or other.editing:
            return None, None
        if not self.ul or not self.lr or not other.ul \
        or not other.lr:
            return None, None

        if utils.use_bezier_curves:
            if other.ul[0] > self.lr[0]:
                xfrom = self.lr[0]
                xto = other.ul[0]
            else:
                xfrom = self.ul[0]
                xto = other.lr[0]
        else:
            xfrom = self.ul[0]-((self.ul[0]-self.lr[0]) / 2.)
            xto = other.ul[0]-((other.ul[0]-other.lr[0]) / 2.)

        yfrom = self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)
        yto = other.ul[1]-((other.ul[1]-other.lr[1]) / 2.)
        return (xfrom, yfrom), (xto, yto)

    # All the rest of these should be handled within you're thought
    # type, supposing you actually want to handle them.
    # You almost certianly do want to ;)
    def process_button_down (self, event, mode, transformed):
        return False

    def process_button_release (self, event, unending_link, mode, transformed):
        return False

    def process_key_press (self, event, mode):
        return False

    def handle_motion (self, event, mode, transformed):
        pass

    def includes (self, coords, mode):
        pass

    def begin_editing (self):
        return False

    def finish_editing (self):
        pass

    def draw (self, context):
        pass

    def load (self, node):
        pass

    def update_save (self):
        pass

    def copy_text (self, clip):
        pass

    def cut_text (self, clip):
        pass

    def paste_text (self, clip):
        pass

    def export (self, context, move_x, move_y):
        pass

    def commit_text (self, im_context, string, mode):
        pass

    def want_motion (self):
        return False

    def recalc_edges (self):
        pass

    def delete_surroundings(self, imcontext, offset, n_chars, mode):
        pass

    def preedit_changed (self, imcontext, mode):
        pass

    def preedit_end (self, imcontext, mode):
        pass

    def preedit_start (self, imcontext, mode):
        pass

    def retrieve_surroundings (self, imcontext, mode):
        pass

    def set_bold (self, active):
        pass

    def get_popup_menu_items(self):
        pass


class ResizableThought (BaseThought):
    ''' A resizable thought base class.  This allows the sides and corners \
        of the thought to be dragged around.  It only provides the very basic \
        functionality.  Other stuff must be done within the derived classes'''

    # Possible types of resizing - where the user selected to resize
    RESIZE_NONE = 0
    RESIZE_LEFT = 1
    RESIZE_RIGHT = 2
    RESIZE_TOP = 3
    RESIZE_BOTTOM = 4
    RESIZE_UL = 5
    RESIZE_UR = 6
    RESIZE_LL = 7
    RESIZE_LR = 8

    def __init__ (self, save, elem_type, undo, background_color, foreground_color):
        super (ResizableThought, self).__init__(save, elem_type, undo, background_color, foreground_color)
        self.resizing = False
        self.button_down = False

    def includes (self, coords, mode):
        if not self.ul or not self.lr or not coords:
            return False

        inside = (coords[0] < self.lr[0] + self.sensitive) and \
                         (coords[0] > self.ul[0] - self.sensitive) and \
                     (coords[1] < self.lr[1] + self.sensitive) and \
                     (coords[1] > self.ul[1] - self.sensitive)

        self.resizing = self.RESIZE_NONE
        self.motion_coords = coords

        if inside and (mode != MODE_EDITING or self.button_down):
            self.emit ("change_mouse_cursor", gtk.gdk.LEFT_PTR)
            return inside

        if inside:
            # 2 cases: 1. The click was within the main area
            #                  2. The click was near the border
            # In the first case, we handle as normal
            # In the second case, we want to intercept all the fun thats
            # going to happen so we can resize the thought
            if abs (coords[0] - self.ul[0]) < self.sensitive:
                # its near the top edge somewhere
                if abs (coords[1] - self.ul[1]) < self.sensitive:
                # Its in the ul corner
                    self.resizing = self.RESIZE_UL
                    self.emit ("change_mouse_cursor", gtk.gdk.TOP_LEFT_CORNER)
                elif abs (coords[1] - self.lr[1]) < self.sensitive:
                # Its in the ll corner
                    self.resizing = self.RESIZE_LL
                    self.emit ("change_mouse_cursor", gtk.gdk.BOTTOM_LEFT_CORNER)
                elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
                #anywhere else along the left edge
                    self.resizing = self.RESIZE_LEFT
                    self.emit ("change_mouse_cursor", gtk.gdk.LEFT_SIDE)
            elif abs (coords[0] - self.lr[0]) < self.sensitive:
                if abs (coords[1] - self.ul[1]) < self.sensitive:
                # Its in the UR corner
                    self.resizing = self.RESIZE_UR
                    self.emit ("change_mouse_cursor", gtk.gdk.TOP_RIGHT_CORNER)
                elif abs (coords[1] - self.lr[1]) < self.sensitive:
                # Its in the lr corner
                    self.resizing = self.RESIZE_LR
                    self.emit ("change_mouse_cursor", gtk.gdk.BOTTOM_RIGHT_CORNER)
                elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
                #anywhere else along the right edge
                    self.resizing = self.RESIZE_RIGHT
                    self.emit ("change_mouse_cursor", gtk.gdk.RIGHT_SIDE)
            elif abs (coords[1] - self.ul[1]) < self.sensitive and \
                     (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
                # Along the top edge somewhere
                self.resizing = self.RESIZE_TOP
                self.emit ("change_mouse_cursor", gtk.gdk.TOP_SIDE)
            elif abs (coords[1] - self.lr[1]) < self.sensitive and \
                     (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
                # Along the bottom edge somewhere
                self.resizing = self.RESIZE_BOTTOM
                self.emit ("change_mouse_cursor", gtk.gdk.BOTTOM_SIDE)
            else:
                self.emit ("change_mouse_cursor", gtk.gdk.LEFT_PTR)
        self.want_move = (self.resizing != self.RESIZE_NONE)
        return inside
