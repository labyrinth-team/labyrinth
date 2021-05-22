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

from gi.repository import Gtk, Gdk, GObject, Pango, PangoCairo
from gi.repository import PangoAttrCast

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

# Convenience functions for working with Pango attributes:

def pango_attr_int_check(attr: Pango.Attribute, attrtype, value):
    return (attr.klass.type is attrtype) \
       and (PangoAttrCast.as_int(attr).value == value)

def pango_attr_set_range(attr: Pango.Attribute, start_idx, end_idx):
    attr.start_index = start_idx
    attr.end_index = end_idx
    return attr

def pango_iter_attrs(attrlist: Pango.AttrList):
    """Step through attributes attached to ranges in some text, yielding:

        (start, end), [attr]
    """
    ai: Pango.AttrIterator = attrlist.get_iterator()
    while True:
        yield ai.range(), ai.get_attrs()
        if not ai.next():
            break


class TextThought (BaseThought.BaseThought):
    def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color, name="thought"):
        super (TextThought, self).__init__(save, name, undo, background_color, foreground_color)

        self.index = 0  # Cursor position in bytes of UTF-8 (as Pango uses)
        self.end_index = 0  # Other end of text selection
        self.bytes = []
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
        self.attrlist = self.attributes.copy()
        
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

        for r, attr in pango_iter_attrs(self.attributes):
            found = False
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
            else: # i.e. self.index > self.end_index
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
                for x in attr:
                    if pango_attr_int_check(x, Pango.AttrType.WEIGHT, Pango.Weight.BOLD):
                        bold = True
                    elif pango_attr_int_check(x, Pango.AttrType.STYLE, Pango.Style.ITALIC):
                        italics = True
                    elif pango_attr_int_check(x, Pango.AttrType.UNDERLINE, Pango.Underline.SINGLE):
                        underline = True
                    elif x.klass.type == Pango.AttrType.FONT_DESC:
                        pango_font = PangoAttrCast.as_fontdesc(x).desc

        to_add = []
        # FIXME: Pango.AttrWeight, AttrStyle, etc. don't appear to exist.
        # Is a workaround using parse_markup possible?
        # http://gitorious.org/mypaint/mypaint/commit/edd97f1e39c9082e5e9ba037fd9b8056948b03e8?format=patch
        if bold:
            to_add.append(pango_attr_set_range(
                Pango.attr_weight_new(Pango.Weight.BOLD), self.index, self.index
            ))
        if italics:
            to_add.append(pango_attr_set_range(
                Pango.attr_style_new(Pango.Style.ITALIC), self.index, self.index
            ))
        if underline:
            to_add.append(pango_attr_set_range(
                Pango.attr_underline_new(Pango.Underline.SINGLE), self.index, self.index
            ))
        if pango_font:
            to_add.append(pango_attr_set_range(
                Pango.attr_font_desc_new(pango_font), self.index, self.index
            ))
        for x in self.current_attrs:
            if pango_attr_int_check(x, Pango.AttrType.WEIGHT, Pango.Weight.BOLD):
                bold = True
                to_add.append(x)
            elif pango_attr_int_check(x, Pango.AttrType.STYLE, Pango.Style.ITALIC):
                italics = True
                to_add.append(x)
            elif pango_attr_int_check(x, Pango.AttrType.UNDERLINE, Pango.Underline.SINGLE):
                underline = True
                to_add.append(x)
            elif x.klass.type is Pango.AttrType.FONT_DESC:
                pango_font = PangoAttrCast.as_fontdesc(x).desc
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
        # Convert Gdk.RGBA (0-1) -> Gdk.Color (0-65535):
        fillc = utils.selected_colors["fill"].to_color()
        bgsel = Pango.attr_background_new(fillc.red, fillc.green, fillc.blue)
        self.attrlist.insert(
            pango_attr_set_range(bgsel, *minmax(self.index, self.end_index))
        )

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

    def commit_text(self, context, string, mode, font_name):
        """Main pathway for entering text

        This is wired up to the IMContext commit signal (in MMapArea).
        IMContext translates keyboard events into text, including (but not only)
        where characters take multiple keystrokes to enter, e.g. with the
        compose key, Ctrl-Shift-U+1234, or CJK characters.
        """
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
        for (start, end), l in pango_iter_attrs(self.attributes):
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
        for a in changes:
            self.attributes.change(a)

        self.text = left + string + right
        self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.INSERT_LETTER, self.undo_text_action,
                                                self.bindex, string, len(string), old_attrs, changes))
        self.index += len (string)
        self.bytes = bleft + [len(string)] + bright
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
        if self.foreground_color:
            Gdk.cairo_set_source_rgba(context, self.foreground_color)
        else:
            Gdk.cairo_set_source_rgba(context, utils.default_colors["text"])
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
            # This is a fallback, and event.string is deprecated.
            # Keypresses which enter text should be handled by the IMContext,
            # resulting in a call to self.commit_text() rather than this code.
            self.add_text (event.string)
            clear_attrs = False
        else:
            handled = False
        if handled and clear_attrs:
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
        for a in attrs:
            self.attributes.change(a)
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

        for (start, end), l in pango_iter_attrs(self.attributes):
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
        for a in changes:
            self.attributes.change(a)

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
            local_bytes = [self.bytes[self.b_f_i(self.index)-1]]
            self.index-=int(self.bytes[self.bindex-1])
            change = -len(local_text)

        old_attrs = []
        changes= []
        accounted = -change

        for (start, end), l in pango_iter_attrs(self.attributes):
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
        for a in changes:
            self.attributes.change(a)

        self.text = left+right
        self.bytes = bleft+bright
        self.end_index = self.index
        self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
                                                self.b_f_i (self.index), local_text, len(local_text), local_bytes, old_attrs,
                                                changes))
        if self.index < 0:
            self.index = 0

    def _index_fix_line_end(self, ix, trailing):
        # move_cursor_visually gives us the byte offset of the start of the
        # current character, plus a flag to indicate if the cursor is after it.
        # This is not enough to find the byte offset of the cursor when the
        # trailing flag is set. It seems to set the trailing flag only at the end
        # of a line, so we find the byte offset of the end of the current line.
        if not trailing:
            return ix
        lineno, _ = self.layout.index_to_line_x(ix, trailing)
        line = self.layout.get_line_readonly(lineno)
        return line.start_index + line.length

    def move_index_back(self, mod):
        """Move cursor backwards one character"""
        new_ix, trailing = self.layout.move_cursor_visually(True, self.index, 0, -1)
        # When Pango wraps text, trailing lets you distinguish the end of one
        # line from the start of the next. Labyrinth doesn't limit the width,
        # so there's no wrapping, and we can just add trailing to the offset.
        if new_ix >= 0:  # -1 when moved backwards from the start
            self.index = self._index_fix_line_end(new_ix, trailing)
        if not mod:
            self.end_index = self.index

    def move_index_forward (self, mod):
        """Move cursor forwards one character"""
        new_ix, trailing = self.layout.move_cursor_visually(True, self.index, 0, 1)
        if new_ix != GObject.G_MAXINT:  # MAXINT when move forwards from the end
            self.index = self._index_fix_line_end(new_ix, trailing)
        if not mod:
            self.end_index = self.index

    def _shift_index_for_trailing(self, ix, trailing):
        # Pango converts screen coordinates to the byte index of a character
        # plus a flag distinguishing the leading or trailing edge. This shifts
        # the cursor to the next character if we're on the trailing edge.
        if trailing:
            ix, trail2 = self.layout.move_cursor_visually(True, ix, 0, 1)
            # At the end of a line, ix is unchanged and trail2 is set
            ix = self._index_fix_line_end(ix, trail2)
        return ix

    def move_index_up (self, mod):
        """Move cursor up one line"""
        lineno, x_pos = self.layout.index_to_line_x(self.index, False)
        if lineno > 0:
            dest_layout_line = self.layout.get_line_readonly(lineno - 1)
            within, new_ix, trailing = dest_layout_line.x_to_index(x_pos)
            self.index = self._shift_index_for_trailing(new_ix, trailing)
        if not mod:
            self.end_index = self.index

    def move_index_down (self, mod):
        """Move cursor down one line"""
        lineno, x_pos = self.layout.index_to_line_x(self.index, False)
        if lineno < (self.layout.get_line_count() - 1):
            dest_layout_line = self.layout.get_line_readonly(lineno + 1)
            within, new_ix, trailing = dest_layout_line.x_to_index(x_pos)
            self.index = self._shift_index_for_trailing(new_ix, trailing)
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
                _ok, ix, trailing = self.layout.xy_to_index (x, y)
                self.index = ix
                if ix >= len(self.text) -1 or self.text[ix+1] == '\n':
                    self.index += trailing
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
            _ok, ix, trailing = self.layout.xy_to_index(x, y)
            self.index = ix
            if ix >= len(self.text) - 1 or self.text[ix + 1] == '\n':
                self.index += trailing
            self.bindex = self.bindex_from_index (self.index)
            self.end_index = self.index
            if os.name != 'nt':
                clip = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
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
                _ok, ix, trailing = self.layout.xy_to_index(x, y)
                self.index = ix
                if ix >= len(self.text) - 1 or self.text[ix + 1] == '\n':
                    self.index += trailing
                self.bindex = self.bindex_from_index (self.index)
                self.selection_changed ()
            elif mode == BaseThought.MODE_EDITING:
                self.emit ("finish_editing")
                self.emit ("create_link", (
                    self.ul[0]-((self.ul[0]-self.lr[0]) / 2.),
                    self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)
                ))
                return True
        elif event.state & Gdk.ModifierType.BUTTON1_MASK and not self.editing and \
                mode == BaseThought.MODE_EDITING and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.emit ("create_link", (
                self.ul[0]-((self.ul[0]-self.lr[0]) / 2.),
                self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)
            ))
        self.recalc_edges()
        self.emit ("update_view")

    def export (self, context, move_x, move_y):
        utils.export_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
                                      (move_x, move_y))

        Gdk.cairo_set_source_rgba(context, self.foreground_color)
        context.move_to (self.text_location[0]+move_x, self.text_location[1]+move_y)
        PangoCairo.show_layout(context, self.layout)
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
            self.element.setAttribute("primary_root", "true")
        else:
            try:
                self.element.removeAttribute("primary_root")
            except xml.dom.NotFoundErr:
                pass

        doc = self.element.ownerDocument
        for (start, end), attrs in pango_iter_attrs(self.attributes):
            for x in attrs:
                elem = doc.createElement ("attribute")
                elem.setAttribute("start", str(start))
                elem.setAttribute("end", str(end))
                self.element.appendChild (elem)
                if pango_attr_int_check(x, Pango.AttrType.WEIGHT, Pango.Weight.BOLD):
                    elem.setAttribute("type", "bold")
                elif pango_attr_int_check(x, Pango.AttrType.STYLE, Pango.Style.ITALIC):
                    elem.setAttribute("type", "italics")
                elif pango_attr_int_check(x, Pango.AttrType.UNDERLINE, Pango.Underline.SINGLE):
                    elem.setAttribute("type", "underline")
                elif x.klass.type is Pango.AttrType.FONT_DESC:
                    elem.setAttribute("type", "font")
                    desc = PangoAttrCast.as_fontdesc(x).desc
                    elem.setAttribute("value", desc.to_string ())

    def rebuild_byte_table (self):
        # Build the Byte table
        self.bytes = [len(c.encode('utf-8')) for c in self.text]
        self.bindex = self.b_f_i (self.index)

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
            self.background_color = Gdk.RGBA()  # default: white
            self.background_color.parse(node.getAttribute("background-color"))
            self.foreground_color = Gdk.RGBA(0., 0., 0.)  # default: black
            self.foreground_color.parse(node.getAttribute("foreground-color"))
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
                    attr = Pango.attr_weight_new(Pango.Weight.BOLD)
                elif attrType == "italics":
                    attr = Pango.attr_style_new(Pango.Style.ITALIC)
                elif attrType == "underline":
                    attr = Pango.attr_underline_new(Pango.Underline.SINGLE)
                elif attrType == "font":
                    font_name = str(n.getAttribute("value"))
                    pango_font = Pango.FontDescription (font_name)
                    attr = Pango.attr_font_desc_new(pango_font)
                else:
                    raise ValueError(
                        "Unexpected attribute type: {!r}".format(attrType)
                    )
                self.attributes.change(pango_attr_set_range(attr, start, end))
            else:
                print("Unknown: " + n.nodeName)
        self.rebuild_byte_table ()
        self.recalc_edges ()

    def copy_text (self, clip):
        start, end = minmax(self.index, self.end_index)
        sel = self.text[start:end]
        clip.set_text(sel, len(sel.encode('utf-8')))

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

        change    = orig - new
        changes   = []
        old_attrs = []
        accounted = -change
        index     = offset
        end_index = offset - (new-orig)

        for (start, end), l in pango_iter_attrs(self.attributes):
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
        for a in changes:
            self.attributes.change(a)

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

    def create_attribute(self, attribute: str, start, end, reset=False) -> Pango.Attribute:
        if attribute == 'bold':
            val = Pango.Weight.NORMAL if reset else Pango.Weight.BOLD
            attr = Pango.attr_weight_new(val)
        elif attribute == 'italic':
            val = Pango.Style.NORMAL if reset else Pango.Style.ITALIC
            attr = Pango.attr_style_new(val)
        elif attribute == 'underline':
            val = Pango.Underline.NONE if reset else Pango.Underline.SINGLE
            attr = Pango.attr_underline_new(val)
        else:
            raise ValueError("Unexpected attribute: {!r}".format(attribute))

        return pango_attr_set_range(attr, start, end)

    def set_attribute(self, active, attribute):
        if not self.editing:
            return

        if attribute == 'bold':
            ptype, pvalue = (Pango.AttrType.WEIGHT, Pango.Weight.BOLD)
        elif attribute == 'italic':
            ptype, pvalue = (Pango.AttrType.STYLE, Pango.Style.ITALIC)
        elif attribute == 'underline':
            ptype, pvalue = (Pango.AttrType.UNDERLINE, Pango.Underline.SINGLE)
        else:
            raise ValueError("Unexpected attribute: {!r}".format(attribute))

        index, end_index = (self.index, self.end_index)
        init, end = minmax(index, end_index)

        if not active:
            attr = self.create_attribute(attribute, init, end, reset=True)
            if index == end_index:
                self.current_attrs.append(attr)
            else:
                self.attributes.change(attr)
            
            
            if index == end_index:
                tmp = []
                attr = None
                for x in self.current_attrs:
                    if pango_attr_int_check(x, ptype, pvalue):
                        attr = x
                    else:
                        tmp.append(x)
                self.current_attrs = tmp
                self.recalc_edges()
                self.undo.add_undo(UndoManager.UndoAction(
                    self, UNDO_REMOVE_ATTR, self.undo_attr_cb, attr
                ))
                return

            old_attrs = self.attributes.copy()
            changed = []
            # If we have removed the middle section of a style, split it into
            # before and after sections.
            for r, attrs in pango_iter_attrs(self.attributes):
                if r[0] <= init and r[1] >= end:
                    for x in attrs:
                        if pango_attr_int_check(x, ptype, pvalue):
                            changed.append(self.create_attribute(attribute, r[0], init))
                            changed.append(self.create_attribute(attribute, end, r[1]))
                        else:
                            changed.append(x)
                else:
                    changed.extend(attrs)

            del self.attributes
            self.attributes = Pango.AttrList()
            for a in changed:
                self.attributes.change(a)
            self.current_attrs = [ x for x in self.current_attrs if pango_attr_int_check(x, ptype, pvalue) ]
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
                self.current_attrs.append(attr)
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