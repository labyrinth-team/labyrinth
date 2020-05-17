# Link.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <Don@Scorgie.org>
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

import math
import gettext
_ = gettext.gettext

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk

import BaseThought
import utils


def norm(x, y):
    mod = math.sqrt(abs((x[0]**2 - y[0]**2) + (x[1]**2 - y[1]**2)))
    return [abs(x[0]-y[0]) / (mod), abs(x[1] - y[1]) / (mod)]

class Link (GObject.GObject):
    __gsignals__ = dict (select_link = (GObject.SignalFlags.RUN_FIRST,
                                        None,
                                        (object,)),
                         update_view = (GObject.SIGNAL_RUN_LAST,
                                        None,
                                        ()),
                         popup_requested = (GObject.SignalFlags.RUN_FIRST,
                                            None,
                                            (object, int)),
                        )

    def __init__ (self, save, parent = None, child = None, start_coords = None, end_coords = None, strength = 2):
        super (Link, self).__init__()
        self.parent = parent
        self.child = child
        self.end = end_coords
        self.start = start_coords
        self.strength = strength
        self.element = save.createElement ("link")
        self.selected = False
        self.color = utils.gtk_to_cairo_color(Gdk.color_parse("black"))

        if not self.start and parent and parent.lr:
            self.start = (parent.ul[0]-((parent.ul[0]-parent.lr[0]) / 2.), \
                                      parent.ul[1]-((parent.ul[1]-parent.lr[1]) / 2.))

        if parent and child:
            self.find_ends ()

    def get_save_element (self):
        return self.element

    def includes (self, coords, mode):
        # TODO: Change this to make link selection work.  Also needs
        # some fairly large changes in MMapArea
        if not self.start or not self.end or not coords:
            return False

        mag = (math.sqrt(((self.end[0] - self.start[0]) ** 2) + \
                     ((self.end[1] - self.start[1]) ** 2)))

        U = (((coords[0] - self.start[0]) * (self.end[0] - self.start[0])) + \
        ((coords[1] - self.start[1]) * (self.end[1] - self.start[1]))) / \
        (mag**2)

        inter = [self.start[0] + U*(self.end[0] - self.start[0]),
                         self.start[1] + U*(self.end[1] - self.start[1])]
        dist = math.sqrt(((coords[0] - inter[0]) ** 2) + \
                     ((coords[1] - inter[1]) ** 2))
        if dist < (3+self.strength) and dist > -(3+self.strength):
            if self.start[0] < self.end[0] and coords[0] > self.start[0] and coords[0] < self.end[0]:
                return True
            elif coords[0] < self.start[0] and coords[0] > self.end[0]:
                return True

        return False

    def connects (self, thought, thought2):
        return (self.parent == thought and self.child == thought2) or \
                        (self.child == thought and self.parent == thought2)

    def set_end (self, coords):
        self.end = coords

    def set_strength (self, strength):
        self.strength = strength

    def change_strength (self, thought, thought2):
        if not self.connects (thought, thought2):
            return False
        if self.parent == thought:
            self.strength += 1
        else:
            self.strength -= 1
        return self.strength != 0

    def set_child (self, child):
        self.child = child
        self.find_ends ()

    def uses (self, thought):
        return self.parent == thought or self.child == thought

    def find_ends (self):
        (self.start, self.end) = self.parent.find_connection (self.child)

    def draw (self, context):
        if not self.start or not self.end:
            return
        cwidth = context.get_line_width ()
        context.set_line_width (self.strength)
        context.move_to (self.start[0], self.start[1])

        if utils.use_bezier_curves:
            dx = self.end[0] - self.start[0]
            x2 = self.start[0] + dx / 2.0
            x3 = self.end[0] - dx / 2.0
            context.curve_to(x2, self.start[1], x3, self.end[1], self.end[0], self.end[1])
        else:
            context.line_to (self.end[0], self.end[1])

        if self.selected:
            color = utils.selected_colors["bg"]
            context.set_source_rgb (color[0], color[1], color[2])
        else:
            context.set_source_rgb (self.color[0], self.color[1], self.color[2])
        context.stroke ()
        context.set_line_width (cwidth)
        context.set_source_rgb (0.0, 0.0, 0.0)

    def export (self, context, move_x, move_y):
        rem = False
        if not self.start or not self.end:
            # Probably shouldn't do this, but its safe now
            self.start = (self.parent.ul[0]-((self.parent.ul[0]-self.parent.lr[0]) / 2.), \
                                      self.parent.ul[1]-((self.parent.ul[1]-self.parent.lr[1]) / 2.))
            self.end = (self.child.ul[0]-((self.child.ul[0]-self.child.lr[0]) / 2.), \
                                    self.child.ul[1]-((self.child.ul[1]-self.child.lr[1]) / 2.))
            rem = True
        cwidth = context.get_line_width ()
        context.set_line_width (self.strength)
        context.move_to (self.start[0]+move_x, self.start[1]+move_y)
        context.line_to (self.end[0]+move_x, self.end[1]+move_y)
        context.stroke ()
        context.set_line_width (cwidth)
        if rem:
            self.start = self.end = None

    def set_parent_child (self, parent, child):
        self.parent = parent
        self.child = child
        if self.parent and self.child:
            self.find_ends ()

    def update_save (self):
        self.element.setAttribute ("start", str(self.start))
        self.element.setAttribute ("end", str(self.end))
        self.element.setAttribute ("strength", str(self.strength))
        self.element.setAttribute ("color", str(self.color))
        if self.child:
            self.element.setAttribute ("child", str(self.child.identity))
        else:
            self.element.setAttribute ("child", "None")
        if self.parent:
            self.element.setAttribute ("parent", str(self.parent.identity))
        else:
            self.element.setAttribute ("parent", "None")

    def load (self, node):
        self.parent_number = self.child_number = -1
        tmp = node.getAttribute ("end")
        if not tmp:
            print("No tmp found")
            return
        self.end = utils.parse_coords (tmp)
        tmp = node.getAttribute ("start")
        if not tmp:
            print("No start found")
            return
        self.start = utils.parse_coords (tmp)
        self.strength = int(node.getAttribute ("strength"))
        try:
            colors = node.getAttribute ("color").split()
            self.color = (float(colors[0].strip('(,)')), float(colors[1].strip('(,)')), float(colors[2].strip('(,)')))
        except:
            pass
        if node.hasAttribute ("parent"):
            tmp = node.getAttribute ("parent")
            if tmp == "None":
                self.parent_number = -1
            else:
                self.parent_number = int (tmp)
        if node.hasAttribute ("child"):
            tmp = node.getAttribute ("child")
            if tmp == "None":
                self.child_number = -1
            else:
                self.child_number = int (tmp)

    def process_button_down (self, event, mode, transformed):
        modifiers = Gtk.accelerator_get_default_mod_mask ()
        self.button_down = True
        if event.button == 1:
            if event.type == Gdk.EventType.BUTTON_PRESS:
                self.emit ("select_link", event.state & modifiers)
                self.emit ("update_view")
        elif event.button == 3:
            self.emit ("popup_requested", event, 2)
        self.emit ("update_view")
        return False

    def process_button_release (self, event, unending_link, mode, transformed):
        return False

    def process_key_press (self, event, mode):
        if mode != BaseThought.MODE_EDITING or event.keyval == Gdk.KEY_Delete:
            return False
        if event.keyval in (Gdk.KEY_plus, Gdk.KEY_KP_Add):
            self.strength += 1
        elif event.keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract) and \
                 self.strength > 1:
            self.strength -= 1
        elif event.keyval == Gdk.KEY_Escape:
            self.unselect()
        self.emit("update_view")
        return True

    def handle_motion (self, event, mode, transformed):
        pass

    def want_motion (self):
        return False

    def select(self):
        self.selected = True

    def unselect(self):
        self.selected = False

    def move_by (self, x,y):
        pass

    def can_be_parent (self):
        return False

    def set_color_cb(self, widget):
        dialog = Gtk.ColorSelectionDialog(_('Choose Color'))
        dialog.connect('response', self.color_selection_ok_cb)
        self.color_sel = dialog.colorsel
        dialog.run()

    def color_selection_ok_cb(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            self.color = utils.gtk_to_cairo_color(self.color_sel.get_current_color())
        dialog.destroy()

    def get_popup_menu_items(self):
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_COLOR_PICKER, Gtk.IconSize.MENU)
        item = Gtk.ImageMenuItem(_('Set Color'))
        item.set_image(image)
        item.connect('activate', self.set_color_cb)
        return [item]
