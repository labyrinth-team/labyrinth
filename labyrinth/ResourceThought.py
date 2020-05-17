# ResourceThought.py
# This file is part of Labyrinth
#
# Copyright (C) 2008 - Labyrinth-Dev-Team
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

from gi.repository import Gtk, Gdk, Pango

import os
import webbrowser
import gettext
_ = gettext.gettext

import utils
import BaseThought, TextThought
import prefs
import UndoManager

class ResourceThought (TextThought.TextThought):
    def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color):
        super (ResourceThought, self).__init__(coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color, "res_thought")

        self.uri = ""

        # TODO: we should handle such things with a singleton
        # FIXME: convert from glade to gtkbuilder
        self.glade = gtk.glade.XML(utils.get_data_file_name('labyrinth.xml'))
        self.dialog = self.glade.get_widget('ResourceChooserDialog')
        self.dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK)

        if not loading:
            self.process_uri_dialog()

        self.all_okay = True

    def process_uri_dialog(self, initial=True):
        res = self.dialog.run()
        self.dialog.hide()

        if res == Gtk.ResponseType.OK:
            # FIXME: validate input
            self.uri = self.glade.get_widget('urlEntry').get_text()
            if initial:
                self.add_text(self.uri)
            self.rebuild_byte_table()

    def process_button_down (self, event, mode, transformed):
        modifiers = Gtk.accelerator_get_default_mod_mask ()
        if event.type == Gdk.EventType.BUTTON_PRESS and not self.editing:
            self.emit ("select_thought", event.state & modifiers)
        if event.button == 1 and mode == BaseThought.MODE_EDITING and event.type == Gdk.EventType._2BUTTON_PRESS:
            if self.uri.find("http://") == -1:
                webbrowser.open("http://" + self.uri)
            else:
                webbrowser.open(self.uri)
        elif event.button == 3:
            self.emit ("popup_requested", event, 1)

    def update_save (self):
        super(ResourceThought, self).update_save()
        self.element.setAttribute ("uri", self.uri)

    def load (self, node):
        super(ResourceThought, self).load(node)
        self.uri = node.getAttribute ("uri")
        self.glade.get_widget('urlEntry').set_text(self.uri)

    def draw (self, context):
        if not self.layout:
            self.recalc_edges ()
        if not self.editing:
            if not self.ul or not self.lr:
                print("Warning: Trying to draw unfinished box "+str(self.identity)+". Aborting.")
                return
            utils.draw_thought_extended (context, self.ul, self.lr, \
                    self.am_selected, self.am_primary, self.background_color, False, True)
        else:
            ux, uy = self.ul
            if prefs.get_direction() == Gtk.TextDirection.LTR:
                context.move_to (ux, uy+5)
                context.line_to (ux, uy)
                context.line_to (ux+5, uy)
            else:
                lx = self.lr[0]
                context.move_to (lx, uy+5)
                context.line_to (lx, uy)
                context.line_to (lx-5, uy)
            context.stroke ()

        (textx, texty) = (self.text_location[0], self.text_location[1])
        r, g, b = utils.gtk_to_cairo_color(self.foreground_color)
        context.set_source_rgb (r, g, b)
        context.move_to (textx, texty)
        context.show_layout (self.layout)
        if self.editing:
            if self.preedit:
                (strong, weak) = self.layout.get_cursor_pos (self.index + self.preedit[2])
            else:
                (strong, weak) = self.layout.get_cursor_pos (self.index)
            (startx, starty, curx,cury) = strong
            startx /= Pango.SCALE
            starty /= Pango.SCALE
            curx /= Pango.SCALE
            cury /= Pango.SCALE
            context.move_to (textx + startx, texty + starty)
            context.line_to (textx + startx, texty + starty + cury)
            context.stroke ()
        context.set_source_rgb (0,0,0)
        context.stroke ()

    def get_popup_menu_items(self):
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_EDIT, Gtk.IconSize.MENU)
        edit_item = Gtk.ImageMenuItem(_('Edit Text'))
        edit_item.set_image(image)
        edit_item.connect('activate', self.edit_cb)
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_NETWORK, Gtk.IconSize.MENU)
        uri_item = Gtk.ImageMenuItem(_('Edit URI'))
        uri_item.set_image(image)
        uri_item.connect('activate', self.edit_uri_cb)
        return [edit_item, uri_item]

    def edit_cb(self, widget):
        self.emit ("begin_editing")

    def edit_uri_cb(self, widget):
        self.process_uri_dialog(False)
