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

import xml.dom.minidom as dom
import xml.dom

class TextThought (BaseThought.BaseThought):
	
	def __init__ (self, coords=None, pango=None, ident=None, element=None, text_element=None, \
				  load=None, extended_element = None):
		super (TextThought, self).__init__()
		self.pango_context = pango
		self.text = ""
		self.index = 0
		self.end_index = 0
		self.bytes = ""
		self.bindex = 0
		self.text_location = coords
		self.lr = None
		self.editing = False
		self.am_root = False
		self.am_primary = False
		self.element = element
		self.text_element = text_element
		self.extended_element = extended_element

		# Convenience function
		self.b_f_i = self.bindex_from_index
		margin = utils.margin_required (utils.STYLE_NORMAL)
		if coords:
			self.ul = (coords[0]-margin[0], coords[1] - margin[1])
		else:
			self.ul = None
		
		if not load:
			self.identity = ident
		else:
			self.load_data (load)
			
	def begin_editing (self, im_context = None):
		if not self.editing:
			self.im = im_context
			self.editing = True
			self.lr_location = None
			if not im_context:
				print "Warning: Unable to edit thought properly.  Will almost certianly fail"
			self.commit_handle = im_context.connect ("commit", self.commit_text_cb)
			self.delete_handle = im_context.connect ("delete-surrounding", self.delete_surround_cb)
			self.surrounding_handle = im_context.connect ("retrieve-surrounding", self.get_surrounding_cb)
		

	def finish_editing (self):
		if self.editing:
			self.editing = False
			if len(self.text) == 0:
				return True
			else:
				self.update_bbox ()
			self.im.disconnect (self.commit_handle)
			self.im.disconnect (self.delete_handle)
			self.im.disconnect (self.surrounding_handle)
			self.commit_handle = 0
			self.delete_handle = 0
			self.surrounding_handle = 0
		return False
		
	def includes (self, coords, allow_resize = False, state=0):
		if not self.ul or not self.lr:
			self.update_bbox ()
		
		inside = coords[0] < self.lr[0] and coords[0] > self.ul[0] and \
		coords[1] < self.lr[1] and coords[1] > self.ul[1]
		
		if inside:
			desc = pango.FontDescription ("normal 12")
			font = self.pango_context.load_font (desc)
			layout = pango.Layout (self.pango_context)
			layout.set_text (self.text)
			x = int ((coords[0] - self.ul[0])*pango.SCALE)
			y = int ((coords[1] - self.ul[1])*pango.SCALE)
			loc = layout.xy_to_index (x, y)
			self.index = loc[0]
			if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
				self.index += loc[1]
			self.bindex = self.bindex_from_index (self.index)
			if not state & gtk.gdk.SHIFT_MASK:
				self.end_index = self.index
		else:
			delete = self.finish_editing ()
			if delete:
				self.emit ("delete_thought", None, None)
		return inside
		
	def become_primary_thought (self):
		self.am_primary = True
	
	def become_active_root (self):
		self.am_root = True
		
	def finish_active_root (self):
		self.am_root = False	
	
	def select (self):
		pass
	
	def draw (self, context):
		desc = pango.FontDescription ("normal 12")
		font = self.pango_context.load_font (desc)
		layout = pango.Layout (self.pango_context)
		layout.set_text (self.text)

		if not self.editing:
			# We should draw the entire bounding box around ourselves
			# We should also have our coordinates figured out.	If not, scream!
			if not self.ul or not self.lr:
				print "Warning: Trying to draw unfinished box "+str(self.identity)+".  Aborting."
				return

			utils.draw_thought_outline (context, self.ul, self.lr, self.am_root, self.am_primary, utils.STYLE_NORMAL)
			
		else:
			(strong, weak) = layout.get_cursor_pos (self.index)
			(startx, starty, curx,cury) = strong
			startx /= pango.SCALE
			starty /= pango.SCALE
			curx /= pango.SCALE
			cury /= pango.SCALE

			context.move_to (self.text_location[0]+startx, self.text_location[1]+starty)
			context.line_to (self.text_location[0]+startx, self.text_location[1]+starty+cury)
			context.stroke ()
			context.move_to (self.ul[0], self.ul[1]+5)
			context.line_to (self.ul[0], self.ul[1])
			context.line_to (self.ul[0]+5, self.ul[1])
			context.stroke ()
			attrs = pango.AttrList ()
			if self.index > self.end_index:
				bgsel = pango.AttrBackground (65535, 0, 0, self.end_index, self.index)
			else:
				bgsel = pango.AttrBackground (65535, 0, 0, self.index, self.end_index)
			attrs.insert (bgsel)
			layout.set_attributes(attrs)

		context.move_to (self.text_location[0], self.text_location[1])
		context.show_layout (layout)
		context.set_source_rgb (0,0,0)
		context.stroke () 
		
	def export (self, context, move_x, move_y):
		desc = pango.FontDescription ("normal 12")
		font = self.pango_context.load_font (desc)
		layout = pango.Layout (self.pango_context)
		layout.set_text (self.text)

		self.update_bbox ()
		utils.export_thought_outline (context, self.ul, self.lr, self.am_root, self.am_primary, utils.STYLE_NORMAL,
									  (move_x, move_y))

		context.move_to (self.text_location[0]+move_x, self.text_location[1]+move_y)
		context.show_layout (layout)
		context.set_source_rgb (0,0,0)
		context.stroke () 

	def update_bbox (self):
		desc = pango.FontDescription ("normal 12")
		font = self.pango_context.load_font (desc)
		layout = pango.Layout (self.pango_context)
		layout.set_text (self.text)
		
		(x,y) = layout.get_pixel_size ()
		margin = utils.margin_required (utils.STYLE_NORMAL)
		self.text_location = (self.ul[0] + margin[0], self.ul[1] + margin[1])
		self.lr = (x + self.text_location[0]+margin[2], y + self.text_location[1] + margin[3])
		
	def handle_movement (self, coords, move = True, edit_mode = False):
		if edit_mode:
			inside = coords[0] < self.lr[0] and coords[0] > self.ul[0] and \
			coords[1] < self.lr[1] and coords[1] > self.ul[1]
		
			if inside:
				desc = pango.FontDescription ("normal 12")
				font = self.pango_context.load_font (desc)
				layout = pango.Layout (self.pango_context)
				layout.set_text (self.text)
				x = int ((coords[0] - self.ul[0])*pango.SCALE)
				y = int ((coords[1] - self.ul[1])*pango.SCALE)
				loc = layout.xy_to_index (x, y)
				self.index = loc[0]
				if loc[0] >= len(self.text) -1 or self.text[loc[0]+1] == '\n':
					self.index += loc[1]
				self.bindex = self.bindex_from_index (self.index)
			else:
				delete = self.finish_editing ()
				if delete:
					self.emit ("delete_thought", None, None)
			return inside
	
		else:
			if not self.ul or not self.lr:
				print "Warning: Unable to update: Things are broken.  Returning"
				return
		
			self.ul = (coords[0], coords[1])
			self.update_bbox ()
		
	def handle_key (self, string, keysym, modifiers):
		# TODO: Handle ctrl+relavent special chars	 
		# Handle escape (finish editing)
		if string:
			self.add_text (string)

		#else:
		# Only interested (for now) in whether the "shift" key is pressed
		if modifiers & gtk.gdk.CONTROL_MASK:
			# Ignore ctrl mask for now
			return
		
		mod = modifiers & gtk.gdk.SHIFT_MASK
		
		try:
			{ gtk.keysyms.Delete   : self.delete_char		,
			  gtk.keysyms.BackSpace: self.backspace_char	,
			  gtk.keysyms.Left	   : self.move_index_back	,
			  gtk.keysyms.Right    : self.move_index_forward,
			  gtk.keysyms.Up	   : self.move_index_up		,
			  gtk.keysyms.Down	   : self.move_index_down	,
			  gtk.keysyms.Home	   : self.move_index_home	,
			  gtk.keysyms.End	   : self.move_index_end	}[keysym](mod)
		except:
			return False
		self.bindex = self.bindex_from_index (self.index)
		self.emit ("title_changed", self.text, 65)
		return True
		
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
			bright = self.bytes[self.b_f_i (self.end_indes):]
		else:
			left = self.text[:self.index]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i(self.index)]
			bright = self.bytes[self.b_f_i(self.index):]
		self.text = left + string + right
		self.index += len (string)
		self.bytes = bleft + str(len(string)) + bright
		self.bindex += 1
		self.end_index = self.index
		
	def delete_char (self, mod):
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
			right = self.text[self.index+int(self.bytes[self.bindex]):]
			bleft = self.bytes[:self.b_f_i(self.index)]
			bright = self.bytes[self.b_f_i(self.index)+1:]
		self.text = left+right
		self.bytes = bleft+bright
		self.end_index = self.index

	def backspace_char (self, mod):
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
			left = self.text[:self.index-int(self.bytes[self.bindex-1])]
			right = self.text[self.index:]
			bleft = self.bytes[:self.b_f_i(self.index)-1]
			bright = self.bytes[self.b_f_i(self.index):]
			self.index-=int(self.bytes[self.bindex-1])
		self.text = left+right
		self.bytes = bleft+bright
		self.end_index = self.index
		
		if self.index < 0:
			self.index = 0
			
	def move_index_back (self, mod):
		if self.index <= 0:
			return
		self.index-=int(self.bytes[self.bindex-1])
		if not mod:
			self.end_index = self.index
		
	def move_index_forward (self, mod):
		if self.index >= len(self.text):
			return
		self.index+=int(self.bytes[self.bindex])
		if not mod:
			self.end_index = self.index
		
	def move_index_up (self, mod):
		tmp = self.text.decode ()
		lines = tmp.splitlines ()
		if len (lines) == 1:
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
			return
		loc = 0
		line = 0
		for i in lines:
			loc += len (i)+1
			if loc > self.bindex:
				break
			line += 1
		if line >= len (lines)-1:
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

	def find_connection (self, other, export = False):
		if not export and (self.editing or other.editing):
			return (None, None)
		elif export:
			self.update_bbox ()
			other.update_bbox ()

		xfrom = self.ul[0]-((self.ul[0]-self.lr[0]) / 2.)
		yfrom = self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)
		xto = other.ul[0]-((other.ul[0]-other.lr[0]) / 2.)
		yto = other.ul[1]-((other.ul[1]-other.lr[1]) / 2.)

		return ((xfrom, yfrom), (xto, yto))
			
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
		if self.am_root:
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


	def load_data (self, node):
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
		if node.hasAttribute ("current_root"):
			self.am_root = True
		else:
			self.am_root = False
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

		# Build the Byte table
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
		self.update_bbox ()
		
	def load_add_parent (self, parent):
		self.parents.append (parent)

	def want_movement (self):
		return self.editing

	def get_max_area (self):
		self.update_bbox ()
		return (self.ul[0],self.ul[1],self.lr[0],self.lr[1])

	def commit_text_cb (self, context, string):
		self.add_text (string)
		self.emit ("title_changed", self.text, 65)
		self.emit ("update_view", True)

	# I don't know if these signals are required.  I've yet to come across
	# them while testing.  Nevertheless, I'm going to hook them up for now
		
	def delete_surround_cb (self, context, offset, n_chars):
		del_index = offset
		del_end = del_index + nchars
		del_bindex = self.bindex_from_index (del_index)
		del_bend = self.bindex_from_index (del_end)
		if del_index > del_end:
			left = self.text[:del_end]
			right = self.text[del_index:]
			bleft = self.bytes[:del_bend]
			bright = self.bytes[del_bindex:]
		elif del_index < del_end:
			left = self.text[:del_index]
			right = self.text[del_end:]
			bleft = self.bytes[:del_bindex]
			bright = self.bytes[del_end:]
		else:
			left = self.text[:del_index]
			right = self.text[del_index+int(self.bytes[del_bindex]):]
			bleft = self.bytes[:del_bindex]
			bright = self.bytes[del_bindex+1:]
		self.text = left+right
		self.bytes = bleft+bright
		# FIXME:
		# If this ever gets called, the self.index might be off.
		# How should the index be altered (or should it?)
		self.index = del_begin
		self.bindex = del_bindex
		self.end_index = self.index
		self.emit ("update_view", True)
	
	
	def get_surrounding_cb (self, context):
		self.im.set_surroundings (self.text, -1, self.bindex)

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


