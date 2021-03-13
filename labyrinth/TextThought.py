#! /usr/bin/env python
# Thoughts.py
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

from gi.repository import Gtk, Gdk, Pango, PangoCairo

import os
import xml.dom

from . import utils
from . import BaseThought
from . import UndoManager
from . import prefs

UNDO_ADD_ATTR=64
UNDO_ADD_ATTR_SELECTION=65
UNDO_REMOVE_ATTR=66
UNDO_REMOVE_ATTR_SELECTION=67

def minmax(a, b):
    return (min(a, b), max(a, b))

class TextThought (BaseThought.BaseThought):
    def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color, name="thought"):
        super (TextThought, self).__init__(save, name, undo, background_color, foreground_color)

        self.index = 0
        self.end_index = 0
        self.bytes = ""
        self.bindex = 0
        self.text_location = coords
        self.text_element = save.createTextNode ("GOOBAH")
        self.element.appendChild (self.text_element)
        self.layout = None
        self.identity = thought_number
        self.pango_context = pango_context
        self.moving = False
        self.preedit = None
        self.attrlist = None
        self.attributes = Pango.AttrList()
        self.current_attrs = []

        if prefs.get_direction() == Gtk.TextDirection.LTR:
            self.pango_context.set_base_dir(Pango.Direction.LTR)
        else:
            self.pango_context.set_base_dir(Pango.Direction.RTL)

        self.b_f_i = self.bindex_from_index
        margin = utils.margin_required (utils.STYLE_NORMAL)
        if coords:
            self.ul = (coords[0]-margin[0], coords[1] - margin[1])
        else:
            self.ul = None
        self.all_okay = True

    def index_from_bindex (self, bindex):
        index = 0
        if bindex > 0:
            index = sum([ int(self.bytes[i]) for i in range(bindex) ])
        return index

    def bindex_from_index (self, index):
        if index == 0:
            return 0
        bind = 0
        nbytes = 0
        for x in self.bytes:
            nbytes += int (x)
            bind += 1
            if nbytes == index:
                break
        if nbytes < index:
            bind = len(self.bytes)
        return bind

    def attrs_changed (self):
        bold = False
        italics = False
        underline = False
        pango_font = None
        del self.attrlist
        self.attrlist = Pango.AttrList()
        # TODO: splice instead of own method
        it = self.attributes.get_iterator()

        while it.next():
            at = it.get_attrs()
            for x in at:
                self.attrlist.insert(x)

        if self.preedit:
            ins_text = self.preedit[0]
            ins_style = self.preedit[1]
            if self.index == len(self.text):
                show_text = self.text + ins_text
            elif self.index == 0:
                show_text = ins_text + self.text
            else:
                split1 = self.text[:self.index]
                split2 = self.text[self.index:]
                show_text = split1 + ins_text + split2
            self.attrlist.splice(ins_style, self.index, len(ins_text))
        else:
            show_text = self.text

        it = self.attributes.get_iterator()
        while it.next():
            found = False
            r = it.range()
            if self.index == self.end_index:
                if r[0] <= self.index and r[1] > self.index:
                    found = True
            elif self.index < self.end_index:
                if r[0] > self.end_index:
                    break
                if self.index == self.end_index and \
                        r[0] < self.index and \
                        r[1] > self.index:
                    found = True
                elif self.index != self.end_index and r[0] <= self.index and \
                   r[1] >= self.end_index:
                    # We got a winner!
                    found = True
            else:
                if r[0] > self.index:
                    break
                if self.index == self.end_index and \
                        r[0] < self.index and \
                        r[1] > self.index:
                    found = True
                elif self.index != self.end_index and r[0] <= self.end_index and \
                   r[1] >= self.index:
                    # We got another winner!
                    found = True

            if found:
                # FIXME: the it.get() seems to crash python
                # through pango.
                attr = it.get_attrs()
                for x in attr:
                    if x.type == Pango.AttrType.WEIGHT and \
                       x.value == Pango.Weight.BOLD:
                        bold = True
                    elif x.type == Pango.AttrType.STYLE and \
                             x.value == Pango.Style.ITALIC:
                        italics = True
                    elif x.type == Pango.AttrType.UNDERLINE and \
                             x.value == Pango.Underline.SINGLE:
                        underline = True
                    elif x.type == Pango.AttrType.FONT_DESC:
                        pango_font = x.desc

        to_add = []
        # FIXME: Pango.AttrWeight, AttrStyle, etc. don't appear to exist.
        # Is a workaround using parse_markup possible?
        # http://gitorious.org/mypaint/mypaint/commit/edd97f1e39c9082e5e9ba037fd9b8056948b03e8?format=patch
        if bold:
            to_add.append(Pango.AttrWeight(Pango.Weight.BOLD, self.index, self.index))
        if italics:
            to_add.append(Pango.AttrStyle(Pango.Style.ITALIC, self.index, self.index))
        if underline:
            to_add.append(Pango.AttrUnderline(Pango.Underline.SINGLE, self.index, self.index))
        if pango_font:
            to_add.append(Pango.AttrFontDesc(pango_font, self.index, self.index))
        for x in self.current_attrs:
            if x.klass.type == Pango.AttrType.WEIGHT and x.value == Pango.Weight.BOLD:
                bold = True
                to_add.append(x)
            if x.klass.type == Pango.AttrType.STYLE and x.value == Pango.Style.ITALIC:
                italics = True
                to_add.append(x)
            if x.klass.type == Pango.AttrType.UNDERLINE and x.value == Pango.Underline.SINGLE:
                underline = True
                to_add.append(x)
            if x.klass.type == Pango.AttrType.FONT_DESC:
                pango_font = x.desc
                to_add.append(x)
        del self.current_attrs
        self.current_attrs = to_add
        self.emit("update-attrs", bold, italics, underline, pango_font)
        return show_text

    def recalc_edges (self):
        if not hasattr(self, 'layout'):
            return

        del self.layout

        show_text = self.attrs_changed ()
        r,g,b = utils.selected_colors["fill"]
        r *= 65536
        g *= 65536
        b *= 65536
        bgsel = Pango.attr_background_new(int(r), int(g), int(b))
        bgsel.start_index = min(self.index, self.end_index)
        bgsel.end_index = max(self.index, self.end_index)
        self.attrlist.insert (bgsel)

        self.layout = Pango.Layout(self.pango_context)
        self.layout.set_text (show_text)
        self.layout.set_attributes(self.attrlist)
        self.recalc_position ()

    def recalc_position (self):
        if self.layout is None:
            self.recalc_edges()

        (x,y) = self.layout.get_pixel_size ()
        margin = utils.margin_required (utils.STYLE_NORMAL)
        if prefs.get_direction () == Gtk.TextDirection.LTR:
            self.text_location = (self.ul[0] + margin[0], self.ul[1] + margin[1])
            self.lr = (x + self.text_location[0]+margin[2], y + self.text_location[1] + margin[3])
        else:
            self.layout.set_alignment (Pango.Alignment.RIGHT)
            tmp1 = self.ul[1]
            if not self.lr:
                self.lr = (self.ul[0], self.ul[1] + y + margin[1] + margin[3])
            self.text_location = (self.lr[0] - margin[2] - x, self.ul[1] + margin[1])
            self.ul = (self.lr[0] - margin[0] - margin[2] - x, tmp1)

    def commit_text (self, context, string, mode, font_name):
        if not self.editing:
            self.emit ("begin_editing")
        self.set_font(font_name)
        self.add_text (string)
        self.recalc_edges ()
        self.emit ("title_changed", self.text)
        self.emit ("update_view")

    def add_text (self, string):
        if self.index > self.end_index:
            self.index, self.end_index = self.end_index, self.index

        left = self.text[:self.index]
        right = self.text[self.end_index:]
        bleft = self.bytes[:self.b_f_i (self.index)]
        bright = self.bytes[self.b_f_i (self.end_index):]
        change = self.index - self.end_index + len(string)

        changes = []
        for x in self.current_attrs:
            x.start_index = self.index
            x.end_index = self.index + len(string)
            changes.append(x)

        old_attrs = []
        it = self.attributes.get_iterator()
        while it.next():
            start, end = it.range()
            l = it.get_attrs()
            if start <= self.index:
                if end > self.end_index:
                    # Inside range
                    for x in l:
                        old_attrs.append(x.copy())
                        x.end_index += change
                        changes.append(x)
                else:
                    for x in l:
                        old_attrs.append(x.copy())
                        changes.append(x)
            else:
                if end > self.end_index:
                    for x in l:
                        old_attrs.append(x.copy())
                        x.end_index += change
                        x.start_index += change
                        changes.append(x)
                else:
                    for x in l:
                        old_attrs.append(x.copy())
                        changes.append(x)

        del self.attributes
        self.attributes = Pango.AttrList()
        map (lambda x : self.attributes.change(x), changes)

        self.text = left + string + right
        self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.INSERT_LETTER, self.undo_text_action,
                                                self.bindex, string, len(string), old_attrs, changes))
        self.index += len (string)
        self.bytes = bleft + str(len(string)) + bright
        self.bindex = self.b_f_i (self.index)
        self.end_index = self.index

    def draw (self, context):
        if not self.layout:
            self.recalc_edges ()
        if not self.editing:
            # We should draw the entire bounding box around ourselves
            # We should also have our coordinates figured out.      If not, scream!
            if not self.ul or not self.lr:
                print("Warning: Trying to draw unfinished box "+str(self.identity)+". Aborting.")
                return
            style = utils.STYLE_EXTENDED_CONTENT
            if len (self.extended_buffer.get_text()) == 0:
                style = utils.STYLE_NORMAL
            utils.draw_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, style)
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

        textx, texty = (self.text_location[0], self.text_location[1])
        if (self.foreground_color):
            r, g, b = utils.gtk_to_cairo_color(self.foreground_color)
        else:
            r, g ,b = utils.gtk_to_cairo_color(utils.default_colors["text"])
        context.set_source_rgb (r, g, b)
        context.move_to (textx, texty)
        PangoCairo.show_layout(context, self.layout)
        if self.editing:
            if self.preedit:
                strong, weak = self.layout.get_cursor_pos (self.index + self.preedit[2])
            else:
                strong, weak = self.layout.get_cursor_pos (self.index)
            startx, starty, curx, cury = strong.x, strong.y, strong.width, strong.height
            startx /= Pango.SCALE
            starty /= Pango.SCALE
            curx /= Pango.SCALE
            cury /= Pango.SCALE
            context.move_to (textx + startx, texty + starty)
            context.line_to (textx + startx, texty + starty + cury)
            context.stroke ()
        context.set_source_rgb (0,0,0)
        context.stroke ()

    def begin_editing (self):
        self.editing = True
        self.emit ("update_links")
        return True

    def finish_editing (self):
        if not self.editing:
            return
        self.editing = False
        self.end_index = self.index
        self.emit ("update_links")
        self.recalc_edges ()
        if len (self.text) == 0:
            self.emit ("delete_thought")

    def includes (self, coords, mode):
        if not self.ul or not self.lr or not coords:
            return False

        inside = (coords[0] < self.lr[0] + self.sensitive) and \
                 (coords[0] > self.ul[0] - self.sensitive) and \
                 (coords[1] < self.lr[1] + self.sensitive) and \
                 (coords[1] > self.ul[1] - self.sensitive)
        if inside and self.editing:
            self.emit ("change_mouse_cursor", Gdk.CursorType.XTERM)
        elif inside:
            self.emit ("change_mouse_cursor", Gdk.CursorType.LEFT_PTR)
        return inside

    def process_key_press (self, event, mode):
        modifiers = Gtk.accelerator_get_default_mod_mask ()
        shift = event.state & modifiers == Gdk.ModifierType.SHIFT_MASK
        handled = True
        clear_attrs = True
        if not self.editing:
            return False

        if (event.state & modifiers) & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_a:
                self.index = self.bindex = 0
                self.end_index = len (self.text)
        elif event.keyval == Gdk.KEY_Escape:
            self.emit ("finish_editing")
        elif event.keyval == Gdk.KEY_Left:
            if prefs.get_direction() == Gtk.TextDirection.LTR:
                self.move_index_back (shift)
            else:
                self.move_index_forward (shift)
        elif event.keyval == Gdk.KEY_Right:
            if prefs.get_direction() == Gtk.TextDirection.RTL:
                self.move_index_back (shift)
            else:
                self.move_index_forward (shift)
        elif event.keyval == Gdk.KEY_Up:
            self.move_index_up (shift)
        elif event.keyval == Gdk.KEY_Down:
            self.move_index_down (shift)
        elif event.keyval == Gdk.KEY_Home:
            if prefs.get_direction() == Gtk.TextDirection.LTR:
                self.move_index_horizontal (shift, True)        # move home
            else:
                self.move_index_horizontal (shift)                      # move end
            self.move_index_horizontal (shift, True)                # move home
        elif event.keyval == Gdk.KEY_End:
            self.move_index_horizontal (shift)                      # move
        elif event.keyval == Gdk.KEY_BackSpace and self.editing:
            self.backspace_char ()
        elif event.keyval == Gdk.KEY_Delete and self.editing:
            self.delete_char ()
        elif len (event.string) != 0:
            self.add_text (event.string)
            clear_attrs = False
        else:
            handled = False
        if clear_attrs:
            del self.current_attrs
            self.current_attrs = []
        self.recalc_edges ()
        self.selection_changed ()
        self.emit ("title_changed", self.text)
        self.bindex = self.bindex_from_index (self.index)
        self.emit ("update_view")
        return handled

    def undo_text_action (self, action, mode):
        self.undo.block ()
        if action.undo_type == UndoManager.DELETE_LETTER or action.undo_type == UndoManager.DELETE_WORD:
            real_mode = not mode
            attrslist = [action.args[5], action.args[4]]
        else:
            real_mode = mode
            attrslist = [action.args[3], action.args[4]]
        self.bindex = action.args[0]
        self.index = self.index_from_bindex (self.bindex)
        self.end_index = self.index
        if real_mode == UndoManager.UNDO:
            attrs = attrslist[0]
            self.end_index = self.index + action.args[2]
            self.delete_char ()
        else:
            attrs = attrslist[1]
            self.add_text (action.text)
            self.rebuild_byte_table ()
            self.bindex = self.b_f_i (self.index)

        del self.attributes
        self.attributes = Pango.AttrList()
        map(lambda a : self.attributes.change(a), attrs)
        self.recalc_edges ()
        self.emit ("begin_editing")
        self.emit ("title_changed", self.text)
        self.emit ("update_view")
        self.emit ("grab_focus", False)
        self.undo.unblock ()

    def delete_char (self):
        if self.index == self.end_index == len (self.text):
            return
        if self.index > self.end_index:
            self.index, self.end_index = self.end_index, self.index
        if self.index != self.end_index:
            left = self.text[:self.index]
            right = self.text[self.end_index:]
            local_text = self.text[self.index:self.end_index]
            bleft = self.bytes[:self.b_f_i (self.index)]
            bright = self.bytes[self.b_f_i (self.end_index):]
            local_bytes = self.bytes[self.b_f_i (self.index):self.b_f_i (self.end_index)]
            change = -len(local_text)
        else:
            left = self.text[:self.index]
            right = self.text[self.index+int(self.bytes[self.bindex]):]
            local_text = self.text[self.index:self.index+int(self.bytes[self.bindex])]
            bleft = self.bytes[:self.b_f_i(self.index)]
            bright = self.bytes[self.b_f_i(self.index)+1:]
            local_bytes = self.bytes[self.b_f_i(self.index)]
            change = -len(local_text)

        changes = []
        old_attrs = []
        accounted = -change

        it = self.attributes.get_iterator()
        while it.next():
            start, end = it.range()
            l = it.get_attrs()
            if end <= self.index:
                for x in l:
                    changes.append(x)
            elif start < self.index and end <= self.end_index:
                # partial ending
                for x in l:
                    old_attrs.append(x.copy())
                    accounted -= (x.end_index - self.index)
                    x.end_index -= (x.end_index - self.index)
                    changes.append(x)
            elif start <= self.index and end >= self.end_index:
                # Swallow whole
                accounted -= (end - start)
                for x in l:
                    old_attrs.append(x.copy())
                    x.end_index += change
                    changes.append(x)
            elif start < self.end_index and end > self.end_index:
                # partial beginning
                for x in l:
                    old_attrs.append(x.copy())
                    accounted -= (x.start_index - self.index)
                    x.start_index = self.index
                    x.end_index = x.start_index + (end - start) - accounted
                    changes.append(x)
            else:
                # Past
                for x in l:
                    old_attrs.append(x.copy())
                    x.start_index += change
                    x.end_index += change
                    changes.append(x)

        del self.attributes
        self.attributes = Pango.AttrList()
        map(lambda a : self.attributes.change(a), changes)

        self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
                                                self.b_f_i (self.index), local_text, len(local_text), local_bytes, old_attrs,
                                                changes))
        self.text = left+right
        self.bytes = bleft+bright
        self.end_index = self.index

    def backspace_char (self):
        if self.index == self.end_index == 0:
            return
        if self.index > self.end_index:
            self.index, self.end_index = self.end_index, self.index
        if self.index != self.end_index:
            left = self.text[:self.index]
            right = self.text[self.end_index:]
            bleft = self.bytes[:self.b_f_i (self.index)]
            bright = self.bytes[self.b_f_i (self.end_index):]
            local_text = self.text[self.index:self.end_index]
            local_bytes = self.bytes[self.b_f_i (self.index):self.b_f_i (self.end_index)]
            change = -len(local_text)
        else:
            left = self.text[:self.index-int(self.bytes[self.bindex-1])]
            right = self.text[self.index:]
            bleft = self.bytes[:self.b_f_i(self.index)-1]
            bright = self.bytes[self.b_f_i(self.index):]
            local_text = self.text[self.index-int(self.bytes[self.bindex-1]):self.index]
            local_bytes = self.bytes[self.b_f_i(self.index)-1]
            self.index-=int(self.bytes[self.bindex-1])
            change = -len(local_text)

        old_attrs = []
        changes= []
        accounted = -change

        it = self.attributes.get_iterator()
        while it.next():
            start, end = it.range()
            l = it.get_attrs()
            if end <= self.index:
                for x in l:
                    old_attrs.append(x.copy())
                    changes.append(x)
            elif start < self.index and end <= self.end_index:
                # partial ending
                for x in l:
                    old_attrs.append(x.copy())
                    accounted -= (x.end_index - self.index)
                    x.end_index -= (x.end_index - self.index)
                    changes.append(x)
            elif start <= self.index and end >= self.end_index:
                # Swallow whole
                accounted -= (end - start)
                for x in l:
                    old_attrs.append(x.copy())
                    x.end_index += change
                    changes.append(x)
            elif start < self.end_index and end > self.end_index:
                # partial beginning
                for x in l:
                    old_attrs.append(x.copy())
                    accounted -= (x.start_index - self.index)
                    x.start_index = self.index
                    x.end_index = x.start_index + (end - start) - accounted
                    changes.append(x)
            else:
                # Past
                for x in l:
                    old_attrs.append(x.copy())
                    x.start_index += change
                    x.end_index += change
                    changes.append(x)

        del self.attributes
        self.attributes = Pango.AttrList()
        map (lambda a : self.attributes.change(a), changes)

        self.text = left+right
        self.bytes = bleft+bright
        self.end_index = self.index
        self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
                                                self.b_f_i (self.index), local_text, len(local_text), local_bytes, old_attrs,
                                                changes))
        if self.index < 0:
            self.index = 0

    def move_index_back (self, mod):
        if self.index <= 0:
            self.end_index = self.index
            return
        self.index -= int(self.bytes[self.bindex-1])
        if not mod:
            self.end_index = self.index

    def move_index_forward (self, mod):
        if self.index >= len(self.text):
            self.end_index = self.index
            return
        self.index += int(self.bytes[self.bindex])
        if not mod:
            self.end_index = self.index

    def move_index_up (self, mod):
        tmp = self.text.decode ()
        lines = tmp.splitlines ()
        if len (lines) == 1:
            self.end_index = self.index
            return
        loc = 0
        line = 0
        for i in lines:
            loc += len (i)+1
            if loc > self.index:
                loc -= len (i)+1
                line -= 1
                break
            line += 1
        if line == -1:
            self.end_index = self.index
            return
        elif line >= len (lines):
            self.bindex -= len (lines[-1])+1
            self.index = self.index_from_bindex (self.bindex)
            if not mod:
                self.end_index = self.index
            return
        dist = self.bindex - loc -1
        self.bindex = loc
        if dist < len (lines[line]):
            self.bindex -= (len (lines[line]) - dist)
        else:
            self.bindex -= 1
        if self.bindex < 0:
            self.bindex = 0
        self.index = self.index_from_bindex (self.bindex)
        if not mod:
            self.end_index = self.index

    def move_index_down (self, mod):
        tmp = self.text.decode ()
        lines = tmp.splitlines ()
        if len (lines) == 1:
            self.end_index = self.index
            return
        loc = 0
        line = 0
        for i in lines:
            loc += len (i)+1
            if loc > self.bindex:
                break
            line += 1
        if line >= len (lines)-1:
            self.end_index = self.index
            return
        dist = self.bindex - (loc - len (lines[line]))+1
        self.bindex = loc
        if dist > len (lines[line+1]):
            self.bindex += len (lines[line+1])
        else:
            self.bindex += dist
        self.index = self.index_from_bindex (self.bindex)
        if not mod:
            self.end_index = self.index

    def move_index_horizontal(self, mod, home=False):
        lines = self.text.splitlines ()
        loc = 0
        line = 0
        for i in lines:
            loc += len (i) + 1
            if loc > self.index:
                self.index = loc - 1
                if home:
                    self.index -= len(i)
                if not mod:
                    self.end_index = self.index
                return
            line += 1

    def process_button_down (self, event, mode, transformed):
        modifiers = Gtk.accelerator_get_default_mod_mask ()

        if event.button == 1:
            if event.type == Gdk.EventType.BUTTON_PRESS and not self.editing:
                self.emit ("select_thought", event.state & modifiers)
            elif event.type == Gdk.EventType.BUTTON_PRESS and self.editing:
                x = int ((transformed[0] - self.ul[0])*Pango.SCALE)
                y = int ((transformed[1] - self.ul[1])*Pango.SCALE)
                loc = self.layout.xy_to_index (x, y)
                self.index = loc[0]
                if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
                    self.index += loc[1]
                self.bindex = self.bindex_from_index (self.index)
                if not (event.state & modifiers) & Gdk.ModifierType.SHIFT_MASK:
                    self.end_index = self.index
            elif mode == BaseThought.MODE_EDITING and event.type == Gdk.EventType._2BUTTON_PRESS:
                if self.editing:
                    self.move_index_horizontal(False)       # go to the end
                    self.index = 0                                          # and mark all
                else:
                    self.emit ("begin_editing")
        elif event.button == 2 and self.editing:
            x = int ((transformed[0] - self.ul[0])*Pango.SCALE)
            y = int ((transformed[1] - self.ul[1])*Pango.SCALE)
            loc = self.layout.xy_to_index (x, y)
            self.index = loc[0]
            if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
                self.index += loc[1]
            self.bindex = self.bindex_from_index (self.index)
            self.end_index = self.index
            if os.name != 'nt':
                clip = Gtk.Clipboard (selection="PRIMARY")
                self.paste_text (clip)
        elif event.button == 3:
            self.emit ("popup_requested", event, 1)

        del self.current_attrs
        self.current_attrs = []
        self.recalc_edges()
        self.emit ("update_view")

    def process_button_release (self, event, unending_link, mode, transformed):
        if unending_link:
            unending_link.set_child (self)
            self.emit ("claim_unending_link")

    def selection_changed (self):
        start, end = minmax(self.index, self.end_index)
        self.emit ("text_selection_changed", start, end, self.text[start:end])

    def handle_motion (self, event, mode, transformed):
        if event.state & Gdk.ModifierType.BUTTON1_MASK and self.editing:
            if transformed[0] < self.lr[0] and transformed[0] > self.ul[0] and \
               transformed[1] < self.lr[1] and transformed[1] > self.ul[1]:
                x = int ((transformed[0] - self.ul[0])*Pango.SCALE)
                y = int ((transformed[1] - self.ul[1])*Pango.SCALE)
                loc = self.layout.xy_to_index (x, y)
                self.index = loc[0]
                if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
                    self.index += loc[1]
                self.bindex = self.bindex_from_index (self.index)
                self.selection_changed ()
            elif mode == BaseThought.MODE_EDITING:
                self.emit ("finish_editing")
                self.emit ("create_link", \
                 (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
                return True
        elif event.state & Gdk.ModifierType.BUTTON1_MASK and not self.editing and \
                mode == BaseThought.MODE_EDITING and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.emit ("create_link", \
             (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
        self.recalc_edges()
        self.emit ("update_view")

    def export (self, context, move_x, move_y):
        utils.export_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
                                      (move_x, move_y))

        r,g,b = utils.gtk_to_cairo_color (self.foreground_color)
        context.set_source_rgb (r, g, b)
        context.move_to (self.text_location[0]+move_x, self.text_location[1]+move_y)
        context.show_layout (self.layout)
        context.set_source_rgb (0,0,0)
        context.stroke ()

    def update_save (self):
        next = self.element.firstChild
        while next:
            m = next.nextSibling
            if next.nodeName == "attribute":
                self.element.removeChild (next)
                next.unlink ()
            next = m

        if self.text_element.parentNode is not None:
            self.text_element.replaceWholeText (self.text)
        text = self.extended_buffer.get_text ()
        if text:
            self.extended_buffer.update_save()
        else:
            try:
                self.element.removeChild(self.extended_buffer.element)
            except xml.dom.NotFoundErr:
                pass
        self.element.setAttribute ("cursor", str(self.index))
        self.element.setAttribute ("selection_end", str(self.end_index))
        self.element.setAttribute ("ul-coords", str(self.ul))
        self.element.setAttribute ("lr-coords", str(self.lr))
        self.element.setAttribute ("identity", str(self.identity))
        self.element.setAttribute ("background-color", self.background_color.to_string())
        self.element.setAttribute ("foreground-color", self.foreground_color.to_string())
        if self.editing:
            self.element.setAttribute ("edit", "true")
        else:
            try:
                self.element.removeAttribute ("edit")
            except xml.dom.NotFoundErr:
                pass
        if self.am_selected:
            self.element.setAttribute ("current_root", "true")
        else:
            try:
                self.element.removeAttribute ("current_root")
            except xml.dom.NotFoundErr:
                pass
        if self.am_primary:
            self.element.setAttribute ("primary_root", "true");
        else:
            try:
                self.element.removeAttribute ("primary_root")
            except xml.dom.NotFoundErr:
                pass

        doc = self.element.ownerDocument
        it = self.attributes.get_iterator()
        while it.next():
            r = it.range()
            for x in it.get_attrs():
                elem = doc.createElement ("attribute")
                elem.setAttribute("start", str(r[0]))
                elem.setAttribute("end", str(r[1]))
                self.element.appendChild (elem)
                if x.type == Pango.AttrType.WEIGHT and x.value == Pango.Weight.BOLD:
                    elem.setAttribute("type", "bold")
                elif x.type == Pango.AttrType.STYLE and x.value == Pango.Style.ITALIC:
                    elem.setAttribute("type", "italics")
                elif x.type == Pango.AttrType.UNDERLINE and x.value == Pango.Underline.SINGLE:
                    elem.setAttribute("type", "underline")
                elif x.type == Pango.AttrType.FONT_DESC:
                    elem.setAttribute("type", "font")
                    elem.setAttribute("value", x.desc.to_string ())

    def rebuild_byte_table (self):
        # Build the Byte table
        del self.bytes
        self.bytes = ''
        tmp = self.text.encode ("utf-8")
        current = 0
        for z in range(len(self.text)):
            if str(self.text[z]) == str(tmp[current]):
                self.bytes += '1'
            else:
                blen = 2
                while 1:
                    try:
                        if str(tmp[current:current+blen].encode()) == str(self.text[z]):
                            self.bytes += str(blen)
                            current+=(blen-1)
                            break
                        blen += 1
                    except:
                        blen += 1
            current+=1
        self.bindex = self.b_f_i (self.index)
        self.text = tmp

    def load (self, node):
        self.index = int (node.getAttribute ("cursor"))
        if node.hasAttribute ("selection_end"):
            self.end_index = int (node.getAttribute ("selection_end"))
        else:
            self.end_index = self.index
        tmp = node.getAttribute ("ul-coords")
        self.ul = utils.parse_coords (tmp)
        tmp = node.getAttribute ("lr-coords")
        self.lr = utils.parse_coords (tmp)
        self.identity = int (node.getAttribute ("identity"))
        try:
            tmp = node.getAttribute ("background-color")
            self.background_color = Gdk.color_parse(tmp)
            tmp = node.getAttribute ("foreground-color")
            self.foreground_color = Gdk.color_parse(tmp)
        except ValueError:
            pass

        if node.hasAttribute ("edit"):
            self.editing = True
        else:
            self.editing = False
            self.end_index = self.index

        self.am_selected = node.hasAttribute ("current_root")
        self.am_primary = node.hasAttribute ("primary_root")

        for n in node.childNodes:
            if n.nodeType == n.TEXT_NODE:
                self.text = n.data
            elif n.nodeName == "Extended":
                self.extended_buffer.load(n)
            elif n.nodeName == "attribute":
                attrType = n.getAttribute("type")
                start = int(n.getAttribute("start"))
                end = int(n.getAttribute("end"))

                if attrType == "bold":
                    attr = Pango.AttrWeight(Pango.Weight.BOLD, start, end)
                elif attrType == "italics":
                    attr = Pango.AttrStyle(Pango.Style.ITALIC, start, end)
                elif attrType == "underline":
                    attr = Pango.AttrUnderline(Pango.Underline.SINGLE, start, end)
                elif attrType == "font":
                    font_name = str(n.getAttribute("value"))
                    pango_font = Pango.FontDescription (font_name)
                    attr = Pango.AttrFontDesc (pango_font, start, end)
                self.attributes.change(attr)
            else:
                print("Unknown: " + n.nodeName)
        self.rebuild_byte_table ()
        self.recalc_edges ()

    def copy_text (self, clip):
        start, end = minmax(self.index, self.end_index)
        clip.set_text (self.text[start:end])

    def cut_text (self, clip):
        self.copy_text (clip)
        self.delete_char ()
        self.recalc_edges ()
        self.emit ("title_changed", self.text)
        self.bindex = self.bindex_from_index (self.index)
        self.emit ("update_view")

    def paste_text (self, clip):
        text = clip.wait_for_text()
        if not text:
            return
        self.add_text (text)
        self.rebuild_byte_table ()
        self.recalc_edges ()
        self.emit ("title_changed", self.text)
        self.bindex = self.bindex_from_index (self.index)
        self.emit ("update_view")

    def delete_surroundings(self, imcontext, offset, n_chars, mode):
        # TODO: Add in Attr stuff
        orig = len(self.text)
        left = self.text[:offset]
        right = self.text[offset+n_chars:]
        local_text = self.text[offset:offset+n_chars]
        self.text = left+right
        self.rebuild_byte_table ()
        new = len(self.text)
        if self.index > len(self.text):
            self.index = len(self.text)

        change    = old - new
        changes   = []
        old_attrs = []
        accounted = -change
        index     = offset
        end_index = offset - (new-orig)

        it = self.attributes.get_iterator()
        while it.next():
            start, end = it.range()
            l = it.get_attrs()
            if end <= start:
                for x in l:
                    changes.append(x)
            elif start < index and end <= end_index:
                # partial ending
                for x in l:
                    old_attrs.append(x.copy())
                    accounted -= (x.end_index - index)
                    x.end_index -= (x.end_index - index)
                    changes.append(x)
            elif start <= index and end >= end_index:
                # Swallow whole
                accounted -= (end - start)
                for x in l:
                    old_attrs.append(x.copy())
                    x.end_index += change
                    changes.append(x)
            elif start < end_index and end > end_index:
                # partial beginning
                for x in l:
                    old_attrs.append(x.copy())
                    accounted -= (x.start_index - index)
                    x.start_index = index
                    x.end_index = x.start_index + (end - start) - accounted
                    changes.append(x)
            else:
                # Past
                for x in l:
                    old_attrs.append(x.copy())
                    x.start_index += change
                    x.end_index += change
                    changes.append(x)

        del self.attributes
        self.attributes = Pango.AttrList()
        map(lambda x : self.attributes.change(x), changes)

        self.recalc_edges ()
        self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
                                                self.b_f_i (offset), local_text, len(local_text), local_bytes, old_attrs, changes))
        self.emit ("title_changed", self.text)
        self.bindex = self.bindex_from_index (self.index)
        self.emit ("update_view")

    def preedit_changed (self, imcontext, mode):
        self.preedit = imcontext.get_preedit_string ()
        if self.preedit[0] == '':
            self.preedit = None
        self.recalc_edges ()
        self.emit ("update_view")

    def retrieve_surroundings (self, imcontext, mode):
        imcontext.set_surrounding (self.text, -1, self.bindex)
        return True

    def undo_attr_cb(self, action, mode):
        self.undo.block()
        if mode == UndoManager.UNDO:
            if action.undo_type == UNDO_REMOVE_ATTR:
                self.current_attrs.append(action.args[0])
            elif action.undo_type == UNDO_ADD_ATTR:
                self.current_attrs.remove(action.args[0])
            elif action.undo_type == UNDO_REMOVE_ATTR_SELECTION:
                self.attributes = action.args[0].copy()
            elif action.undo_type == UNDO_ADD_ATTR_SELECTION:
                self.attributes = action.args[0].copy()
        else:
            if action.undo_type == UNDO_REMOVE_ATTR:
                self.current_attrs.remove(action.args[0])
            elif action.undo_type == UNDO_ADD_ATTR:
                self.current_attrs.append(action.args[0])
            elif action.undo_type == UNDO_REMOVE_ATTR_SELECTION:
                self.attributes = action.args[1].copy()
            elif action.undo_type == UNDO_ADD_ATTR_SELECTION:
                self.attributes = action.args[1].copy()
        self.recalc_edges()
        self.emit("update_view")
        self.undo.unblock()

    def create_attribute(self, attribute, start, end):
        if attribute == 'bold':
            return Pango.AttrWeight(Pango.Weight.BOLD, start, end)
        elif attribute == 'italic':
            return Pango.AttrStyle(Pango.Style.ITALIC, start, end)
        elif attribute == 'underline':
            return Pango.AttrUnderline(Pango.Underline.SINGLE, start, end)

    def set_attribute(self, active, attribute):
        if not self.editing:
            return

        if attribute == 'bold':
            pstyle, ptype, pvalue = (Pango.Weight.NORMAL, Pango.AttrType.WEIGHT, Pango.Weight.BOLD)
        elif attribute == 'italic':
            pstyle, ptype, pvalue = (Pango.Style.NORMAL, Pango.AttrType.ATTR_STYLE, Pango.Style.ITALIC)
        elif attribute == 'underline':
            pstyle, ptype, pvalue = (Pango.Underline.NONE, Pango.AttrType.UNDERLINE, Pango.Underline.SINGLE)

        index, end_index = (self.index, self.end_index)
        init, end = minmax(index, end_index)

        if not active:
            attr = Pango.AttrStyle(pstyle, init, end)
            if index == end_index:
                self.current_attrs.change(attr)
            else:
                self.attributes.change(attr)

            tmp = []
            attr = None
            if index == end_index:
                for x in self.current_attrs:
                    if x.type == ptype and x.value == pvalue:
                        attr = x
                    else:
                        tmp.append(x)
                self.current_attrs = tmp
                self.recalc_edges()
                self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR, \
                                                          self.undo_attr_cb,\
                                                          attr))
                return

            it = self.attributes.get_iterator()
            old_attrs = self.attributes.copy()
            changed = []

            while it.next():
                r = it.range()
                if r[0] <= init and r[1] >= end:
                    for x in it.get_attrs():
                        if x.type == ptype and x.value == pvalue:
                            changed.append(self.create_attribute(attribute, r[0], init))
                            changed.append(self.create_attribute(attribute, end, r[1]))
                        else:
                            changed.append(x)
                else:
                    map(lambda x : changed.append(x), it.get_attrs())

            del self.attributes
            self.attributes = Pango.AttrList()
            map(lambda x : self.attributes.change(x), changed)
            self.current_attrs = [ x for x in self.current_attrs if x.type == ptype and x.value == pvalue ]
            self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR_SELECTION,
                                                      self.undo_attr_cb,
                                                      old_attrs,
                                                      self.attributes.copy()))
        else:
            if index == end_index:
                attr = self.create_attribute(attribute, index, end_index)
                self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR,
                                                          self.undo_attr_cb,
                                                          attr))
                self.current_attrs.change(attr)
            else:
                attr = self.create_attribute(attribute, init, end)
                old_attrs = self.attributes.copy()
                self.attributes.change(attr)
                self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION,
                                                          self.undo_attr_cb,
                                                          old_attrs,
                                                          self.attributes.copy()))
        self.recalc_edges()

    def set_bold (self, active):
        self.set_attribute(active, 'bold')

    def set_italics (self, active):
        self.set_attribute(active, 'italic')

    def set_underline (self, active):
        self.set_attribute(active, 'underline')

    def set_font (self, font_name):
        if not self.editing:
            return
        start, end = minmax(self.index, self.end_index)

        pango_font = Pango.FontDescription (font_name)
        attr = Pango.attr_font_desc_new(pango_font)
        attr.start_index = start
        attr.end_index = end

        if start == end:
            self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR,
                                                      self.undo_attr_cb, 
                                                      attr))
            self.current_attrs.append(attr)
        else:
            old_attrs = self.attributes.copy()
            self.attributes.change(attr)
            self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION,
                                                      self.undo_attr_cb, 
                                                      old_attrs, 
                                                      self.attributes.copy()))
        self.recalc_edges()

    def get_popup_menu_items(self):
        return []
