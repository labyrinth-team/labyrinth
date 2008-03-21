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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#

import gtk
import pango
import utils
import BaseThought
import prefs
import UndoManager
import os

import xml.dom

UNDO_ADD_ATTR=64
UNDO_ADD_ATTR_SELECTION=65
UNDO_REMOVE_ATTR=66
UNDO_REMOVE_ATTR_SELECTION=67

class TextThought (BaseThought.BaseThought):
	def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color):
		super (TextThought, self).__init__(save, "thought", undo, background_color, foreground_color)

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
		self.attributes = pango.AttrList()
		self.current_attrs = []

		if prefs.get_direction () == gtk.TEXT_DIR_LTR:
			self.pango_context.set_base_dir (pango.DIRECTION_LTR)
		else:
			self.pango_context.set_base_dir (pango.DIRECTION_RTL)

		self.b_f_i = self.bindex_from_index
		margin = utils.margin_required (utils.STYLE_NORMAL)
		if coords:
			self.ul = (coords[0]-margin[0], coords[1] - margin[1])
		else:
			self.ul = None
		self.all_okay = True

	def index_from_bindex (self, bindex):
		if bindex == 0:
			return 0
		index = 0
		for x in range(bindex):
			index += int(self.bytes[x])

		return index

	def bindex_from_index (self, index):
		if index == 0:
			return 0
		bind = 0
		nbytes = 0
		for x in self.bytes:
			nbytes += int (x)
			bind+=1
			if nbytes == index:
				break
		if nbytes < index:
			bind = len(self.bytes)
		return bind

	def attrs_changed (self):
		bold = False
		italics = False
		underline = False
		del self.attrlist
		self.attrlist = pango.AttrList ()
		# TODO: splice instead of own method
		it = self.attributes.get_iterator()
		
		while 1:
			at = it.get_attrs()
			for x in at:
				self.attrlist.insert(x)
			if it.next() == False:
				break
		if self.preedit:
			ins_text = self.preedit[0]
			ins_style = self.preedit[1]
			if self.index == len(self.text):
				show_text = self.text+ins_text
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
		while(1):
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
					if x.type == pango.ATTR_WEIGHT and \
					   x.value == pango.WEIGHT_BOLD:
						bold = True
					elif x.type == pango.ATTR_STYLE and \
						 x.value == pango.STYLE_ITALIC:
						italics = True
					elif x.type == pango.ATTR_UNDERLINE and \
						 x.value == pango.UNDERLINE_SINGLE:
						underline = True
			if it.next() == False:
				break
		to_add = []
		if bold:
			to_add.append(pango.AttrWeight(pango.WEIGHT_BOLD, self.index, self.index))
		if italics:
			to_add.append(pango.AttrStyle(pango.STYLE_ITALIC, self.index, self.index))
		if underline:
			to_add.append(pango.AttrUnderline(pango.UNDERLINE_SINGLE, self.index, self.index))
		for x in self.current_attrs:
			if x.type == pango.ATTR_WEIGHT and x.value == pango.WEIGHT_BOLD:
				bold = True
				to_add.append(x)
			if x.type == pango.ATTR_STYLE and x.value == pango.STYLE_ITALIC:
				italics = True
				to_add.append(x)
			if x.type == pango.ATTR_UNDERLINE and x.value == pango.UNDERLINE_SINGLE:
				underline = True
				to_add.append(x)
		del self.current_attrs
		self.current_attrs = to_add
		self.emit("update-attrs", bold, italics, underline)
		return show_text

	def recalc_edges (self):
		del self.layout
		show_text = self.attrs_changed ()
		
		if self.index > self.end_index:
			bgsel = pango.AttrBackground (61423, 10537, 10537, self.end_index, self.index)
		else:
			bgsel = pango.AttrBackground (61423, 10537, 10537, self.index, self.end_index)
		self.attrlist.insert (bgsel)

		self.layout = pango.Layout (self.pango_context)
		self.layout.set_text (show_text)
		self.layout.set_attributes(self.attrlist)

		(x,y) = self.layout.get_pixel_size ()
		margin = utils.margin_required (utils.STYLE_NORMAL)
		if prefs.get_direction () == gtk.TEXT_DIR_LTR:
			self.text_location = (self.ul[0] + margin[0], self.ul[1] + margin[1])
			self.lr = (x + self.text_location[0]+margin[2], y + self.text_location[1] + margin[3])
		else:
			self.layout.set_alignment (pango.ALIGN_RIGHT)
			tmp1 = self.ul[1]
			if not self.lr:
				self.lr = (self.ul[0], self.ul[1] + y + margin[1] + margin[3])
			self.text_location = (self.lr[0] - margin[2] - x, self.ul[1] + margin[1])
			self.ul = (self.lr[0] - margin[0] - margin[2] - x, tmp1)

	def commit_text (self, context, string, mode):
		if not self.editing:
			self.emit ("begin_editing")
		self.add_text (string)
		self.recalc_edges ()
		self.emit ("title_changed", self.text)
		self.emit ("update_view")

	def add_text (self, string):
		if self.index > self.end_index:
			left = self.text[:self.end_index]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i (self.end_index)]
			bright = self.bytes[self.b_f_i (self.index):]
			change = self.end_index - self.index + len(string)
			old = self.index
			self.index = self.end_index
			self.end_index = old
		elif self.index < self.end_index:
			left = self.text[:self.index]
			right = self.text[self.end_index:]
			bleft = self.bytes[:self.b_f_i (self.index)]
			bright = self.bytes[self.b_f_i (self.end_index):]
			change = self.index - self.end_index + len(string)
		else:
			left = self.text[:self.index]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i(self.index)]
			bright = self.bytes[self.b_f_i(self.index):]
			change = len(string)

		it = self.attributes.get_iterator()
		changes= []
		for x in self.current_attrs:
			x.start_index = self.index
			x.end_index = self.index + len(string)
			changes.append(x)
		old_attrs = []
		while (1):
			(start,end) = it.range()
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
			if it.next() == False:
				break
		
		del self.attributes
		self.attributes = pango.AttrList()
		for x in changes:
			self.attributes.change(x)

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
			# We should also have our coordinates figured out.	If not, scream!
			if not self.ul or not self.lr:
				print "Warning: Trying to draw unfinished box "+str(self.identity)+".  Aborting."
				return
			utils.draw_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL)

		else:
			if prefs.get_direction() == gtk.TEXT_DIR_LTR:
				context.move_to (self.ul[0], self.ul[1]+5)
				context.line_to (self.ul[0], self.ul[1])
				context.line_to (self.ul[0]+5, self.ul[1])
			else:
				context.move_to (self.lr[0], self.ul[1]+5)
				context.line_to (self.lr[0], self.ul[1])
				context.line_to (self.lr[0]-5, self.ul[1])
			context.stroke ()

		context.set_source_color (self.foreground_color)
		context.move_to (self.text_location[0], self.text_location[1])
		context.show_layout (self.layout)
		if self.editing:
			if self.preedit:
				(strong, weak) = self.layout.get_cursor_pos (self.index + self.preedit[2])
			else:
				(strong, weak) = self.layout.get_cursor_pos (self.index)
			(startx, starty, curx,cury) = strong
			startx /= pango.SCALE
			starty /= pango.SCALE
			curx /= pango.SCALE
			cury /= pango.SCALE
			context.move_to (self.text_location[0]+startx, self.text_location[1]+starty)
			context.line_to (self.text_location[0]+startx, self.text_location[1]+starty+cury)
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
		if not self.ul or not self.lr:
			return False

		inside = (coords[0] < self.lr[0] + self.sensitive) and \
				 (coords[0] > self.ul[0] - self.sensitive) and \
			     (coords[1] < self.lr[1] + self.sensitive) and \
			     (coords[1] > self.ul[1] - self.sensitive)
		if inside and self.editing:
			self.emit ("change_mouse_cursor", gtk.gdk.XTERM)
		elif inside:
			self.emit ("change_mouse_cursor", gtk.gdk.LEFT_PTR)
		return inside

	def process_key_press (self, event, mode):
		modifiers = gtk.accelerator_get_default_mod_mask ()
		shift = event.state & modifiers == gtk.gdk.SHIFT_MASK
		handled = True
		clear_attrs = True
		if not self.editing:
			return False
			
		if (event.state & modifiers) & gtk.gdk.CONTROL_MASK:
			if event.keyval == gtk.keysyms.a:
				self.index = self.bindex = 0
				self.end_index = len (self.text)
		elif event.keyval == gtk.keysyms.Escape:
			self.emit ("finish_editing")
		elif event.keyval == gtk.keysyms.Left:
			if prefs.get_direction() == gtk.TEXT_DIR_LTR:
				self.move_index_back (shift)
			else:
				self.move_index_forward (shift)
		elif event.keyval == gtk.keysyms.Right:
			if prefs.get_direction() == gtk.TEXT_DIR_RTL:
				self.move_index_back (shift)
			else:
				self.move_index_forward (shift)
		elif event.keyval == gtk.keysyms.Up:
			self.move_index_up (shift)
		elif event.keyval == gtk.keysyms.Down:
			self.move_index_down (shift)
		elif event.keyval == gtk.keysyms.Home:
			if prefs.get_direction() == gtk.TEXT_DIR_LTR:
				self.move_index_home (shift)
			else:
				self.move_index_end (shift)
			self.move_index_home (shift)
		elif event.keyval == gtk.keysyms.End:
			if prefs.get_direction() == gtk.TEXT_DIR_LTR:
				self.move_index_end (shift)
			else:
				self.move_index_end (shift)
		elif event.keyval == gtk.keysyms.BackSpace and self.editing:
			self.backspace_char ()
		elif event.keyval == gtk.keysyms.Delete and self.editing:
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
		self.attributes = pango.AttrList()
		for x in attrs:		
			self.attributes.change (x)
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
			left = self.text[:self.end_index]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i (self.end_index)]
			bright = self.bytes[self.b_f_i (self.index):]
			local_text = self.text[self.end_index:self.index]
			local_bytes = self.bytes[self.b_f_i (self.end_index):self.b_f_i (self.index)]
			change = -len(local_text)
			self.index = self.end_index
			self.end_index = self.index
		elif self.index < self.end_index:
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

		changes= []
		old_attrs = []
		accounted = -change
		
		it = self.attributes.get_iterator()
		while (1):
			(start,end) = it.range()
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
			if it.next() == False:
				break
		
		del self.attributes
		self.attributes = pango.AttrList()
		for x in changes:
			self.attributes.change (x)
			
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
			left = self.text[:self.end_index]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i (self.end_index)]
			bright = self.bytes[self.b_f_i (self.index):]
			local_text = self.text[self.end_index:self.index]
			local_bytes = self.bytes[self.b_f_i (self.end_index):self.b_f_i (self.index)]
			change = -len(local_text)
			tmp = self.index
			self.index = self.end_index
			self.end_index = tmp
		elif self.index < self.end_index:
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
		while (1):
			(start,end) = it.range()
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
			if it.next() == False:
				break
		
		
		del self.attributes
		self.attributes = pango.AttrList()
		for x in changes:
			self.attributes.change (x)
			
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
		self.index-=int(self.bytes[self.bindex-1])
		if not mod:
			self.end_index = self.index

	def move_index_forward (self, mod):
		if self.index >= len(self.text):
			self.end_index = self.index
			return
		self.index+=int(self.bytes[self.bindex])
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
			line+=1
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

	def move_index_home (self, mod):
		lines = self.text.splitlines ()
		loc = 0
		line = 0
		for i in lines:
			loc += len (i) + 1
			if loc > self.index:
				self.index = loc-len (i) - 1
				if not mod:
					self.end_index = self.index
				return
			line += 1

	def move_index_end (self, mod):
		lines = self.text.splitlines ()
		loc = 0
		line = 0
		for i in lines:
			loc += len (i)+1
			if loc > self.index:
				self.index = loc-1
				if not mod:
					self.end_index = self.index
				return
			line += 1

	def process_button_down (self, event, mode, transformed):
		modifiers = gtk.accelerator_get_default_mod_mask ()

		if event.button == 1:
			if event.type == gtk.gdk.BUTTON_PRESS and not self.editing:
				self.emit ("select_thought", event.state & modifiers)
			elif event.type == gtk.gdk.BUTTON_PRESS and self.editing:
				x = int ((transformed[0] - self.ul[0])*pango.SCALE)
				y = int ((transformed[1] - self.ul[1])*pango.SCALE)
				loc = self.layout.xy_to_index (x, y)
				self.index = loc[0]
				if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
					self.index += loc[1]
				self.bindex = self.bindex_from_index (self.index)
				if not (event.state & modifiers) & gtk.gdk.SHIFT_MASK:
					self.end_index = self.index
			elif mode == BaseThought.MODE_EDITING and event.type == gtk.gdk._2BUTTON_PRESS:
				self.emit ("begin_editing")
		elif event.button == 2 and self.editing:
			x = int ((transformed[0] - self.ul[0])*pango.SCALE)
			y = int ((transformed[1] - self.ul[1])*pango.SCALE)
			loc = self.layout.xy_to_index (x, y)
			self.index = loc[0]
			if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
				self.index += loc[1]
			self.bindex = self.bindex_from_index (self.index)
			self.end_index = self.index
			if os.name != 'nt':
				clip = gtk.Clipboard (selection="PRIMARY")
				self.paste_text (clip)
		elif event.button == 3:
			self.emit ("popup_requested", (event.x, event.y), 1)
		del self.current_attrs
		self.current_attrs = []
		self.recalc_edges()
		self.emit ("update_view")

	def process_button_release (self, event, unending_link, mode, transformed):
		if unending_link:
			unending_link.set_child (self)
			self.emit ("claim_unending_link")

	def selection_changed (self):
		if self.index > self.end_index:
			self.emit ("text_selection_changed", self.end_index, self.index, self.text[self.end_index:self.index])
		else:
			self.emit ("text_selection_changed", self.index, self.end_index, self.text[self.index:self.end_index])

	def handle_motion (self, event, mode, transformed):
		if event.state & gtk.gdk.BUTTON1_MASK and self.editing:
			if transformed[0] < self.lr[0] and transformed[0] > self.ul[0] and \
			   transformed[1] < self.lr[1] and transformed[1] > self.ul[1]:
				x = int ((transformed[0] - self.ul[0])*pango.SCALE)
				y = int ((transformed[1] - self.ul[1])*pango.SCALE)
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
		elif event.state & gtk.gdk.BUTTON1_MASK and not self.editing and \
			mode == BaseThought.MODE_EDITING and not event.state & gtk.gdk.CONTROL_MASK:
			self.emit ("create_link", \
			 (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
		self.recalc_edges()
		self.emit ("update_view")

	def export (self, context, move_x, move_y):
		utils.export_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
									  (move_x, move_y))

		context.set_source_color (self.foreground_color)
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
		while(1):
			r = it.range()
			for x in it.get_attrs():
				if x.type == pango.ATTR_WEIGHT and x.value == pango.WEIGHT_BOLD:
					elem = doc.createElement ("attribute")
					self.element.appendChild (elem)
					elem.setAttribute("start", str(r[0]))
					elem.setAttribute("end", str(r[1]))
					elem.setAttribute("type", "bold")				
				elif x.type == pango.ATTR_STYLE and x.value == pango.STYLE_ITALIC:
					elem = doc.createElement ("attribute")
					self.element.appendChild (elem)
					elem.setAttribute("start", str(r[0]))
					elem.setAttribute("end", str(r[1]))
					elem.setAttribute("type", "italics")
				elif x.type == pango.ATTR_UNDERLINE and x.value == pango.UNDERLINE_SINGLE:
					elem = doc.createElement ("attribute")
					self.element.appendChild (elem)
					elem.setAttribute("start", str(r[0]))
					elem.setAttribute("end", str(r[1]))
					elem.setAttribute("type", "underline")
			if not it.next():
				break

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
			self.background_color = gtk.gdk.color_parse(tmp)
			tmp = node.getAttribute ("foreground-color")
			self.foreground_color = gtk.gdk.color_parse(tmp)
		except ValueError:
			pass

		if node.hasAttribute ("edit"):
			self.editing = True
		else:
			self.editing = False
			self.end_index = self.index
		if node.hasAttribute ("current_root"):
			self.am_selected = True
		else:
			self.am_selected = False
		if node.hasAttribute ("primary_root"):
			self.am_primary = True
		else:
			self.am_primary = False

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
					attr = pango.AttrWeight(pango.WEIGHT_BOLD, start, end)
				elif attrType == "italics":
					attr = pango.AttrStyle(pango.STYLE_ITALIC, start, end)
				elif attrType == "underline":
					attr = pango.AttrUnderline(pango.UNDERLINE_SINGLE, start, end)
				self.attributes.change(attr)
			else:
				print "Unknown: "+n.nodeName
		self.rebuild_byte_table ()
		self.recalc_edges ()

	def copy_text (self, clip):
		if self.end_index > self.index:
			clip.set_text (self.text[self.index:self.end_index])
		else:
			clip.set_text (self.text[self.end_index:self.index])


	def cut_text (self, clip):
		if self.end_index > self.index:
			clip.set_text (self.text[self.index:self.end_index])
		else:
			clip.set_text (self.text[self.end_index:self.index])
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
			
		change = old - new
		changes= []
		old_attrs = []
		accounted = -change

		index = offset
		end_index = offset - (new-orig)

		it = self.attributes.get_iterator()
		while (1):
			(start,end) = it.range()
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
			if it.next() == False:
				break
		
		del self.attributes
		self.attributes = pango.AttrList()
		for x in changes:
			self.attributes.change (x)

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

	def set_bold (self, active):
		if not self.editing:
			return
		if not active:
			tmp = []
			attr = None
			if self.index == self.end_index:
				for x in self.current_attrs:
					if x.type == pango.ATTR_WEIGHT and x.value == pango.WEIGHT_BOLD:
						attr = x
					else:
						tmp.append(x)
				self.current_attrs = tmp
				self.recalc_edges()
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR, \
														  self.undo_attr_cb,\
														  attr))
				return
			elif self.index < self.end_index:
				init = self.index
				end = self.end_index
			else:
				init = self.end_index
				end = self.index
			it = self.attributes.get_iterator()
			old_attrs = self.attributes.copy()
			
			changed = []
			while(1):
				r = it.range()
				if r[0] <= init and r[1] >= end:
					for x in it.get_attrs():
						if x.type == pango.ATTR_WEIGHT and x.value == pango.WEIGHT_BOLD:
							changed.append(pango.AttrWeight(pango.WEIGHT_BOLD, r[0], init))
							changed.append(pango.AttrWeight(pango.WEIGHT_BOLD, end, r[1]))
						else:
							changed.append(x)
				else:
					for x in it.get_attrs():
						changed.append(x)
				if not it.next():
					break
			del self.attributes
			self.attributes = pango.AttrList()
			for x in changed:
				self.attributes.change(x)
			tmp = []
			for x in self.current_attrs:
				if not (x.type == pango.ATTR_WEIGHT and x.value == pango.WEIGHT_BOLD):
					tmp.append(x)
			self.current_attrs = tmp
			self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR_SELECTION, 
													  self.undo_attr_cb,
													  old_attrs,
													  self.attributes.copy()))
		else:
			if self.index == self.end_index:
				attr = pango.AttrWeight(pango.WEIGHT_BOLD, self.index, self.end_index)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR,
														  self.undo_attr_cb,
														  attr))
				self.current_attrs.append(attr)
			elif self.index < self.end_index:
				attr = pango.AttrWeight(pango.WEIGHT_BOLD, self.index, self.end_index)
				old_attrs = self.attributes.copy()
				self.attributes.insert(attr)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION,
														  self.undo_attr_cb,
														  old_attrs,
														  self.attributes.copy()))
			else:
				attr = pango.AttrWeight(pango.WEIGHT_BOLD, self.end_index, self.index)
				old_attrs = self.attributes.copy()
				self.attributes.insert(attr)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION,
														  self.undo_attr_cb,
														  old_attrs,
														  self.attributes.copy()))
		self.recalc_edges()
			
	def set_italics (self, active):
		if not self.editing:
			return
		if not active:
			tmp = []
			attr = None
			if self.index == self.end_index:
				for x in self.current_attrs:
					if x.type == pango.ATTR_STYLE and x.value == pango.STYLE_ITALIC:
						attr = x
					else:
						tmp.append(x)
				self.current_attrs = tmp
				self.recalc_edges()
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR,
														  self.undo_attr_cb,
														  attr))
				return
			elif self.index < self.end_index:
				init = self.index
				end = self.end_index
			else:
				init = self.end_index
				end = self.index
			it = self.attributes.get_iterator()
			old_attrs = self.attributes.copy()
			
			changed = []
			while(1):
				r = it.range()
				if r[0] <= init and r[1] >= end:
					for x in it.get_attrs():
						if x.type == pango.ATTR_STYLE and x.value == pango.STYLE_ITALIC:
							changed.append(pango.AttrStyle(pango.STYLE_ITALIC, r[0], init))
							changed.append(pango.AttrStyle(pango.STYLE_ITALIC, end, r[1]))
						else:
							changed.append(x)
				else:
					for x in it.get_attrs():
						changed.append(x)
				if not it.next():
					break
			del self.attributes
			self.attributes = pango.AttrList()
			for x in changed:
				self.attributes.change(x)
			tmp = []
			for x in self.current_attrs:
				if not (x.type == pango.ATTR_STYLE and x.value == pango.STYLE_ITALIC):
					tmp.append(x)
			self.current_attrs = tmp
			self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR_SELECTION,
													  self.undo_attr_cb,
													  old_attrs,
													  self.attributes.copy()))
		else:
			if self.index == self.end_index:
				attr = pango.AttrStyle(pango.STYLE_ITALIC, self.index, self.end_index)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR,
														  self.undo_attr_cb,
														  attr))
				self.current_attrs.append(attr)
			elif self.index < self.end_index:
				attr = pango.AttrStyle(pango.STYLE_ITALIC, self.index, self.end_index)			
				old_attrs = self.attributes.copy()
				self.attributes.insert(attr)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION, \
														  self.undo_attr_cb,\
														  old_attrs,
														  self.attributes.copy()))
			else:
				attr = pango.AttrStyle(pango.STYLE_ITALIC, self.end_index, self.index)
				old_attrs = self.attributes.copy()
				self.attributes.insert(attr)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION, \
														  self.undo_attr_cb,\
														  old_attrs,
														  self.attributes.copy()))
		self.recalc_edges()		
			
	def set_underline (self, active):
		if not self.editing:
			return
		if not active:
			tmp = []
			attr = None
			if self.index == self.end_index:
				for x in self.current_attrs:
					if x.type == pango.ATTR_UNDERLINE and x.value == pango.UNDERLINE_SINGLE:
						attr = x
					else:
						tmp.append(x)
				self.current_attrs = tmp
				self.recalc_edges()
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR, \
														  self.undo_attr_cb,\
														  attr))
				return
			elif self.index < self.end_index:
				init = self.index
				end = self.end_index
			else:
				init = self.end_index
				end = self.index
			it = self.attributes.get_iterator()
			old_attrs = self.attributes.copy()
			
			changed = []
			while(1):
				r = it.range()
				if r[0] <= init and r[1] >= end:
					for x in it.get_attrs():
						if x.type == pango.ATTR_UNDERLINE and x.value == pango.UNDERLINE_SINGLE:
							changed.append(pango.AttrUnderline(pango.UNDERLINE_SINGLE, r[0], init))
							changed.append(pango.AttrUnderline(pango.UNDERLINE_SINGLE, end, r[1]))
						else:
							changed.append(x)
				else:
					for x in it.get_attrs():
						changed.append(x)
				if not it.next():
					break
			del self.attributes
			self.attributes = pango.AttrList()
			for x in changed:
				self.attributes.change(x)
			tmp = []
			for x in self.current_attrs:
				if not (x.type == pango.ATTR_UNDERLINE and x.value == pango.UNDERLINE_SINGLE):
					tmp.append(x)
			self.current_attrs = tmp
			self.undo.add_undo(UndoManager.UndoAction(self, UNDO_REMOVE_ATTR_SELECTION,
													  self.undo_attr_cb,
													  old_attrs,
													  self.attributes.copy()))
		else:
			if self.index == self.end_index:
				attr = pango.AttrUnderline(pango.UNDERLINE_SINGLE, self.index, self.end_index)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR,
														  self.undo_attr_cb,
														  attr))
				self.current_attrs.append(attr)
			elif self.index < self.end_index:
				attr = pango.AttrUnderline(pango.UNDERLINE_SINGLE, self.index, self.end_index)
				old_attrs = self.attributes.copy()
				self.attributes.insert(attr)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION,
														  self.undo_attr_cb,
														  old_attrs,
														  self.attributes.copy()))
			else:
				attr = pango.AttrUnderline(pango.UNDERLINE_SINGLE, self.end_index, self.index)
				old_attrs = self.attributes.copy()
				self.attributes.insert(attr)
				self.undo.add_undo(UndoManager.UndoAction(self, UNDO_ADD_ATTR_SELECTION,
														  self.undo_attr_cb,
														  old_attrs,
														  self.attributes.copy()))
		self.recalc_edges()					
