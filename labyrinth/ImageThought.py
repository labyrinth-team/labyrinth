# ImageThought.py
# This file is part of labyrinth
#
# Copyright (C) 2006 - Don Scorgie <Don@Scorgie.org>
#
# labyrinth is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# labyrinth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#

# Standard library
import os.path
import xml.dom.minidom as dom
import xml.dom
import gettext
_ = gettext.gettext

# Gtk stuff
from gi.repository import Gtk
import cairo

# Local imports
import BaseThought
import utils
import UndoManager

MODE_EDITING = 0
MODE_IMAGE = 1
MODE_DRAW = 2

UNDO_RESIZE = 0

class ImageThought (BaseThought.ResizableThought):
    def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color):
        super (ImageThought, self).__init__(save, "image_thought", undo, background_color, None)

        self.identity = thought_number
        margin = utils.margin_required (utils.STYLE_NORMAL)
        self.want_move = False
        if coords:
            self.ul = (coords[0]-margin[0], coords[1] - margin[1])
            self.pic_location = coords
        else:
            self.ul = None
        self.button_press = False

        if not loading:
            self.all_okay = self.open_image ()
        else:
            self.all_okay = True

    def open_image (self, filename = None):
        # Present a dialog for the user to choose an image here
        if not filename:
            fil = Gtk.FileFilter ()
            fil.set_name("Images")
            fil.add_pixbuf_formats ()
            dialog = Gtk.FileChooserDialog (_("Choose image to insert"), None, Gtk.FileChooserAction.OPEN, \
                                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
            dialog.add_filter (fil)
            res = dialog.run ()
            dialog.hide ()
            if res != Gtk.ResponseType.OK:
                return False
            else:
                fname = dialog.get_filename()
        else:
            fname = filename

        try:
            self.orig_pic = GdkPixbuf.Pixbuf.new_from_file (fname)
        except:
            try:
                # lets see if file was imported and is already extracted
                fname = utils.get_save_dir() + 'images/' + os.path.basename(filename)
                self.orig_pic = GdkPixbuf.Pixbuf.new_from_file (fname)
            except:
                return False

        self.filename = fname

        if not filename:
            self.width = self.orig_pic.get_width ()
            self.height = self.orig_pic.get_height ()
            margin = utils.margin_required (utils.STYLE_NORMAL)

            self.lr = (self.pic_location[0]+self.width+margin[2], self.pic_location[1]+self.height+margin[3])
            self.pic = self.orig_pic
        self.text = fname[fname.rfind('/')+1:fname.rfind('.')]
        return True

    def draw (self, context):
        if len (self.extended_buffer.get_text()) == 0:
            utils.draw_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL)
        else:
            utils.draw_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_EXTENDED_CONTENT)

        if self.pic:
            context.set_source_pixbuf (self.pic, self.pic_location[0], self.pic_location[1])
            context.rectangle (self.pic_location[0], self.pic_location[1], self.width, self.height)
            context.fill ()
        context.set_source_rgb (0,0,0)

    def export (self, context, move_x, move_y):
        utils.export_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
                                                                  (move_x, move_y))
        if self.pic:
            if hasattr(context, "set_source_pixbuf"):
                context.set_source_pixbuf (self.pic, self.pic_location[0]+move_x, self.pic_location[1]+move_y)
            elif hasattr(context, "set_source_surface"):
                pixel_array = utils.pixbuf_to_cairo (self.pic.get_pixels_array())
                image_surface = cairo.ImageSurface.create_for_data(pixel_array, cairo.FORMAT_ARGB32, self.width, self.height, -1)
                context.set_source_surface (image_surface, self.pic_location[0]+move_x, self.pic_location[1]+move_y)
            context.rectangle (self.pic_location[0]+move_x, self.pic_location[1]+move_y, self.width, self.height)
            context.fill ()
        context.set_source_rgb (0,0,0)

    def want_motion (self):
        return self.want_move

    def recalc_edges (self):
        margin = utils.margin_required (utils.STYLE_NORMAL)
        self.pic_location = (self.ul[0]+margin[0], self.ul[1]+margin[1])
        self.lr = (self.pic_location[0]+self.width+margin[2], self.pic_location[1]+self.height+margin[3])

    def recalc_position (self):
        self.recalc_edges ()

    def undo_resize (self, action, mode):
        self.undo.block ()
        if mode == UndoManager.UNDO:
            choose = 0
        else:
            choose = 1
        self.ul = action.args[choose][0]
        self.width = action.args[choose][1]
        self.height = action.args[choose][2]
        self.pic = self.orig_pic.scale_simple (int(self.width), int(self.height), GdkPixbuf.InterpType.HYPER)
        self.recalc_edges ()
        self.emit ("update_links")
        self.emit ("update_view")
        self.undo.unblock ()

    def process_button_down (self, event, mode, transformed):
        modifiers = Gtk.accelerator_get_default_mod_mask ()
        self.button_down = True
        if event.button == 1:
            if event.type == Gdk.EventType.BUTTON_PRESS:
                self.emit ("select_thought", event.state & modifiers)
                self.emit ("update_view")
            if mode == MODE_EDITING and self.resizing != self.RESIZE_NONE:
                self.orig_size = (self.ul, self.width, self.height)
                self.want_move = True
                return True
        elif event.button == 3:
            self.emit ("popup_requested", event, 1)
        self.emit ("update_view")

    def process_button_release (self, event, unending_link, mode, transformed):
        self.button_down = False
        if unending_link:
            unending_link.set_child (self)
            self.emit ("claim_unending_link")
        if self.orig_pic:
            self.pic = self.orig_pic.scale_simple (int(self.width), int(self.height), GdkPixbuf.InterpType.HYPER)
        self.emit ("update_view")
        if self.want_move:
            self.undo.add_undo (UndoManager.UndoAction (self, UNDO_RESIZE, self.undo_resize, \
                                                                                                    self.orig_size, (self.ul, self.width, self.height)))
            self.want_move = False

    def handle_motion (self, event, mode, transformed):
        if self.resizing == self.RESIZE_NONE or not self.want_move or not event.state & Gdk.ModifierType.BUTTON1_MASK:
            if not event.state & Gdk.ModifierType.BUTTON1_MASK:
                return False
            elif mode == MODE_EDITING:
                self.emit ("create_link", \
                 (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
            return True
        diffx = transformed[0] - self.motion_coords[0]
        diffy = transformed[1] - self.motion_coords[1]
        tmp = self.motion_coords
        self.motion_coords = transformed
        if self.resizing == self.RESIZE_LEFT:
            if self.width - diffx < 10:
                self.motion_coords = tmp
                return True
            self.ul = (self.ul[0]+diffx, self.ul[1])
            self.pic_location = (self.pic_location[0]+diffx, self.pic_location[1])
            self.width -= diffx
        elif self.resizing == self.RESIZE_RIGHT:
            if self.width + diffx < 10:
                self.motion_coords = tmp
                return True
            self.lr = (self.lr[0]+diffx, self.lr[1])
            self.width += diffx
        elif self.resizing == self.RESIZE_TOP:
            if self.height - diffy < 10:
                self.motion_coords = tmp
                return True
            self.ul = (self.ul[0], self.ul[1]+diffy)
            self.pic_location = (self.pic_location[0], self.pic_location[1]+diffy)
            self.height -= diffy
        elif self.resizing == self.RESIZE_BOTTOM:
            if self.height + diffy < 10:
                self.motion_coords = tmp
                return True
            self.lr = (self.lr[0], self.lr[1]+diffy)
            self.height += diffy
        elif self.resizing == self.RESIZE_UL:
            if self.height - diffy < 10 or self.width - diffx < 10:
                self.motion_coords = tmp
                return True
            self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
            self.pic_location = (self.pic_location[0]+diffx, self.pic_location[1]+diffy)
            self.width -= diffx
            self.height -= diffy
        elif self.resizing == self.RESIZE_UR:
            if self.height - diffy < 10 or self.width + diffx < 10:
                self.motion_coords = tmp
                return True
            self.ul = (self.ul[0], self.ul[1]+diffy)
            self.lr = (self.lr[0]+diffx, self.lr[1])
            self.pic_location = (self.pic_location[0], self.pic_location[1]+diffy)
            self.width += diffx
            self.height -= diffy
        elif self.resizing == self.RESIZE_LL:
            if self.height + diffy < 10 or self.width - diffx < 10:
                self.motion_coords = tmp
                return True
            self.ul = (self.ul[0]+diffx, self.ul[1])
            self.lr = (self.lr[0], self.lr[1]+diffy)
            self.pic_location = (self.pic_location[0]+diffx, self.pic_location[1])
            self.width -= diffx
            self.height += diffy
        elif self.resizing == self.RESIZE_LR:
            if self.height + diffy < 10:
                self.motion_coords = tmp
                return True
            if self.width + diffx < 10:
                self.motion_coords = tmp
                return True
            self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
            self.width += diffx
            self.height += diffy
        if self.orig_pic:
            self.pic = self.orig_pic.scale_simple (int(self.width), int(self.height), GdkPixbuf.InterpType.NEAREST)
        self.emit ("update_links")
        self.emit ("update_view")
        return True

    def update_save (self):
        text = self.extended_buffer.get_text ()
        if text:
            self.extended_buffer.update_save()
        else:
            try:
                self.element.removeChild(self.extended_buffer.element)
            except xml.dom.NotFoundErr:
                pass
        self.element.setAttribute ("ul-coords", str(self.ul))
        self.element.setAttribute ("lr-coords", str(self.lr))
        self.element.setAttribute ("identity", str(self.identity))
        self.element.setAttribute ("background-color", self.background_color.to_string())
        self.element.setAttribute ("file", str(self.filename))
        self.element.setAttribute ("image_width", str(self.width))
        self.element.setAttribute ("image_height", str(self.height))
        if self.am_selected:
            self.element.setAttribute ("current_root", "true")
        else:
            try:
                self.element.removeAttribute ("current_root")
            except xml.dom.NotFoundErr:
                pass
        if self.am_primary:
            self.element.setAttribute ("primary_root", "true")
        else:
            try:
                self.element.removeAttribute ("primary_root")
            except xml.dom.NotFoundErr:
                pass
        return

    def load (self, node):
        tmp = node.getAttribute ("ul-coords")
        self.ul = utils.parse_coords (tmp)
        tmp = node.getAttribute ("lr-coords")
        self.lr = utils.parse_coords (tmp)
        self.filename = node.getAttribute ("file")
        self.identity = int (node.getAttribute ("identity"))
        try:
            tmp = node.getAttribute ("background-color")
            self.background_color = Gdk.color_parse(tmp)
        except ValueError:
            pass
        self.width = float(node.getAttribute ("image_width"))
        self.height = float(node.getAttribute ("image_height"))
        self.am_selected = node.hasAttribute ("current_root")
        self.am_primary = node.hasAttribute ("primary_root")

        for n in node.childNodes:
            if n.nodeName == "Extended":
                self.extended_buffer.load(n)
            else:
                print("Unknown: "+n.nodeName)
        margin = utils.margin_required (utils.STYLE_NORMAL)
        self.pic_location = (self.ul[0]+margin[0], self.ul[1]+margin[1])
        self.okay = self.open_image (self.filename)
        self.lr = (self.pic_location[0]+self.width+margin[2], self.pic_location[1]+self.height+margin[3])
        if not self.okay:
            dialog = Gtk.MessageDialog (None, Gtk.DialogFlagsMODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                                                    Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE,
                                                                    _("Error loading file"))
            dialog.format_secondary_text(_("%s could not be found.  Associated thought will be empty.") % self.filename)
            dialog.run ()
            dialog.hide ()
            self.pic = None
            self.orig_pic = None
        else:
            self.pic = self.orig_pic.scale_simple (int(self.width), int(self.height), GdkPixbuf.InterpType.HYPER)
        return

    def change_image_cb(self, widget):
        self.open_image()

    def get_popup_menu_items(self):
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.MENU)
        item = Gtk.ImageMenuItem(_('Change Image'))
        item.set_image(image)
        item.connect('activate', self.change_image_cb)
        return [item]
