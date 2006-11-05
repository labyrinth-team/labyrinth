#! /usr/bin/env python
# Thoughts.py
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
import gobject
import Links
import utils
import BaseThought
import prefs
import UndoManager

import xml.dom.minidom as dom
import xml.dom

class TextThought (BaseThought.BaseThought):
	def __init__ (self, coords, pango_context, thought_number, save, undo, loading):
		super (TextThought, self).__init__(save, "thought", undo)

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

	def recalc_edges (self):
		desc = pango.FontDescription ("normal 12")
		font = self.pango_context.load_font (desc)
		del self.layout
		del self.attrlist
		self.attrlist = pango.AttrList ()
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
			it = ins_style.get_iterator ()
			while it:
				for att in it.get_attrs ():
					att.start_index += self.index
					att.end_index += self.index
					self.attrlist.insert (att)
				if not it.next ():
					it = None
		else:
			show_text = self.text
		self.layout = pango.Layout (self.pango_context)
		self.layout.set_text (show_text)
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
			self.index = self.end_index
		elif self.index < self.end_index:
			left = self.text[:self.index]
			right = self.text[self.end_index:]
			bleft = self.bytes[:self.b_f_i (self.index)]
			bright = self.bytes[self.b_f_i (self.end_index):]
		else:
			left = self.text[:self.index]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i(self.index)]
			bright = self.bytes[self.b_f_i(self.index):]
		self.text = left + string + right
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.INSERT_LETTER, self.undo_text_action,
							self.bindex, string, len(string)))
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
			utils.draw_thought_outline (context, self.ul, self.lr, self.am_selected, self.am_primary, utils.STYLE_NORMAL)

		else:
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
			if prefs.get_direction() == gtk.TEXT_DIR_LTR:
				context.move_to (self.ul[0], self.ul[1]+5)
				context.line_to (self.ul[0], self.ul[1])
				context.line_to (self.ul[0]+5, self.ul[1])
			else:
				context.move_to (self.lr[0], self.ul[1]+5)
				context.line_to (self.lr[0], self.ul[1])
				context.line_to (self.lr[0]-5, self.ul[1])
			context.stroke ()
		if self.index > self.end_index:
			bgsel = pango.AttrBackground (65535, 0, 0, self.end_index, self.index)
		else:
			bgsel = pango.AttrBackground (65535, 0, 0, self.index, self.end_index)
		self.attrlist.insert (bgsel)
		self.layout.set_attributes(self.attrlist)

		context.move_to (self.text_location[0], self.text_location[1])
		context.show_layout (self.layout)
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
		if (event.state & modifiers) & gtk.gdk.CONTROL_MASK:
			if not self.editing:
				handled = False
			elif event.keyval == gtk.keysyms.a:
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
		else:
			handled = False
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
			bytes = action.args[3]
		else:
			real_mode = mode
			bytes = None
		self.bindex = action.args[0]
		self.index = self.index_from_bindex (self.bindex)
		self.end_index = self.index
		if real_mode == UndoManager.UNDO:
			self.end_index = self.index + action.args[2]
			self.delete_char ()
		else:
			self.add_text (action.text)
			self.rebuild_byte_table ()
			self.bindex = self.b_f_i (self.index)
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
			self.index = self.end_index
		elif self.index < self.end_index:
			left = self.text[:self.index]
			right = self.text[self.end_index:]
			local_text = self.text[self.index:self.end_index]
			bleft = self.bytes[:self.b_f_i (self.index)]
			bright = self.bytes[self.b_f_i (self.end_index):]
			local_bytes = self.bytes[self.b_f_i (self.index):self.b_f_i (self.end_index)]
		else:
			left = self.text[:self.index]
			right = self.text[self.index+int(self.bytes[self.bindex]):]
			local_text = self.text[self.index:self.index+int(self.bytes[self.bindex])]
			bleft = self.bytes[:self.b_f_i(self.index)]
			bright = self.bytes[self.b_f_i(self.index)+1:]
			local_bytes = self.bytes[self.b_f_i(self.index)]
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
							self.b_f_i (self.index), local_text, len(local_text), local_bytes))
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
			self.index = self.end_index
		elif self.index < self.end_index:
			left = self.text[:self.index]
			right = self.text[self.end_index:]
			bleft = self.bytes[:self.b_f_i (self.index)]
			bright = self.bytes[self.b_f_i (self.end_index):]
			local_text = self.text[self.index:self.end_index]
			local_bytes = self.bytes[self.b_f_i (self.index):self.b_f_i (self.end_index)]
		else:
			left = self.text[:self.index-int(self.bytes[self.bindex-1])]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i(self.index)-1]
			bright = self.bytes[self.b_f_i(self.index):]
			local_text = self.text[self.index-int(self.bytes[self.bindex-1]):self.index]
			local_bytes = self.bytes[self.b_f_i(self.index)-1]
			self.index-=int(self.bytes[self.bindex-1])
		self.text = left+right
		self.bytes = bleft+bright
		self.end_index = self.index
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
							self.b_f_i (self.index), local_text, len(local_text), local_bytes))
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

	def process_button_down (self, event, mode):
		modifiers = gtk.accelerator_get_default_mod_mask ()

		if event.button == 1:
			if event.type == gtk.gdk.BUTTON_PRESS and not self.editing:
				self.emit ("select_thought", event.state & modifiers)
			elif event.type == gtk.gdk.BUTTON_PRESS and self.editing:
				x = int ((event.x - self.ul[0])*pango.SCALE)
				y = int ((event.y - self.ul[1])*pango.SCALE)
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
			x = int ((event.x - self.ul[0])*pango.SCALE)
			y = int ((event.y - self.ul[1])*pango.SCALE)
			loc = self.layout.xy_to_index (x, y)
			self.index = loc[0]
			if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
				self.index += loc[1]
			self.bindex = self.bindex_from_index (self.index)
			self.end_index = self.index
			clip = gtk.Clipboard (selection="PRIMARY")
			self.paste_text (clip)
		elif event.button == 3:
			self.emit ("popup_requested", (event.x, event.y), 1)
		self.emit ("update_view")

	def process_button_release (self, event, unending_link, mode):
		if unending_link:
			unending_link.set_child (self)
			self.emit ("claim_unending_link")

	def selection_changed (self):
		if self.index > self.end_index:
			self.emit ("text_selection_changed", self.end_index, self.index, self.text[self.end_index:self.index])
		else:
			self.emit ("text_selection_changed", self.index, self.end_index, self.text[self.index:self.end_index])

	def handle_motion (self, event, mode):
		if event.state & gtk.gdk.BUTTON1_MASK and self.editing:
			if event.x < self.lr[0] and event.x > self.ul[0] and \
			   event.y < self.lr[1] and event.y > self.ul[1]:
				x = int ((event.x - self.ul[0])*pango.SCALE)
				y = int ((event.y - self.ul[1])*pango.SCALE)
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
		elif event.state & gtk.gdk.BUTTON1_MASK and not self.editing and mode == BaseThought.MODE_EDITING:
			self.emit ("create_link", \
			 (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
		self.emit ("update_view")

	def export (self, context, move_x, move_y):
		utils.export_thought_outline (context, self.ul, self.lr, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
									  (move_x, move_y))

		context.move_to (self.text_location[0]+move_x, self.text_location[1]+move_y)
		context.show_layout (self.layout)
		context.set_source_rgb (0,0,0)
		context.stroke ()

	def update_save (self):
		self.text_element.replaceWholeText (self.text)
		text = self.extended_buffer.get_text ()
		if text:
			self.extended_element.replaceWholeText (text)
		else:
			self.extended_element.replaceWholeText ("LABYRINTH_AUTOGEN_TEXT_REMOVE")
		self.element.setAttribute ("cursor", str(self.index))
		self.element.setAttribute ("selection_end", str(self.end_index))
		self.element.setAttribute ("ul-coords", str(self.ul))
		self.element.setAttribute ("lr-coords", str(self.lr))
		self.element.setAttribute ("identity", str(self.identity))
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
					if str(tmp[current:current+blen].encode()) == str(self.text[z]):
						self.bytes += str(blen)
						current+=(blen-1)
						break
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
				for m in n.childNodes:
					if m.nodeType == m.TEXT_NODE:
						text = m.data
						if text != "LABYRINTH_AUTOGEN_TEXT_REMOVE":
							self.extended_buffer.set_text (text)
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
		left = self.text[:offset]
		right = self.text[offset+n_chars:]
		local_text = self.text[offset:offset+n_chars]
		self.text = left+right
		self.rebuild_byte_table ()
		if self.index > len(self.text):
			self.index = len(self.text)
		self.recalc_edges ()
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_text_action,
							self.b_f_i (offset), local_text, len(local_text), local_bytes))
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
