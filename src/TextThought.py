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

import xml.dom

class TextThought (BaseThought.BaseThought):
	
	def __init__ (self, coords=None, pango=None, ident=None, element=None, text_element=None, load=None):
		super (TextThought, self).__init__()
		self.pango_context = pango
		self.text = ""
		self.index = 0
		self.ul = coords
		self.lr = None
		self.editing = True
		self.am_root = False
		self.am_primary = False
		self.element = element
		self.text_element = text_element
		
		if not load:
			self.identity = ident
		else:
			self.load_data (load)
			
	def begin_editing (self):
		self.editing = True
		self.lr_location = None

	def finish_editing (self):
		if self.editing:
			self.editing = False
			if len(self.text) == 0:
				return True
			else:
				self.update_bbox ()
		return False
		
	def includes (self, coords, allow_resize = False):
		if not self.ul or not self.lr:
			return False
		else:
			return coords[0] < self.lr[0] and coords[0] > self.ul[0] and \
			coords[1] < self.lr[1] and coords[1] > self.ul[1]
		
	def become_primary_thought (self):
		self.am_primary = True
	
	def become_active_root (self):
		self.am_root = True
		
	def finish_active_root (self):
		self.am_root = False	
	
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
			context.move_to (self.ul[0]-5, self.ul[1]-5)
			context.line_to (self.ul[0]-5, self.lr[1])
			context.line_to (self.lr[0], self.lr[1])
			context.line_to (self.lr[0], self.ul[1]-5)
			context.line_to (self.ul[0]-5, self.ul[1]-5)
			if self.am_root:
				context.set_source_rgb (0.0,0.9,0.9)
			elif self.am_primary:
				context.set_source_rgb (1.0,0.5,0.5)
			else:
				context.set_source_rgb (1.0,1.0,1.0)
			context.fill_preserve ()
			context.set_source_rgb (0,0,0)
			context.stroke ()
		else:
			(strong, weak) = layout.get_cursor_pos (self.index)
			(startx, starty, curx,cury) = strong
			startx /= pango.SCALE
			starty /= pango.SCALE
			curx /= pango.SCALE
			cury /= pango.SCALE

			context.move_to (self.ul[0]+startx, self.ul[1]+starty)
			context.line_to (self.ul[0]+startx, self.ul[1]+starty+cury)
			context.stroke ()
			context.move_to (self.ul[0]-5, self.ul[1]+5)
			context.line_to (self.ul[0]-5, self.ul[1]-5)
			context.line_to (self.ul[0]+5, self.ul[1]-5)
			context.stroke ()

		context.move_to (self.ul[0], self.ul[1])
		context.show_layout (layout)
		context.set_source_rgb (0,0,0)
		context.stroke () 

	def update_bbox (self):
		desc = pango.FontDescription ("normal 12")
		font = self.pango_context.load_font (desc)
		layout = pango.Layout (self.pango_context)
		layout.set_text (self.text)
		
		(x,y) = layout.get_pixel_size ()
		self.lr = (x + self.ul[0]+5, y + self.ul[1] + 5)
		
	def handle_movement (self, coords):
		if not self.ul or not self.lr:
			print "Warning: Unable to update: Things are broken.  Returning"
			return
		
		self.ul = (coords[0], coords[1])
		self.update_bbox ()
		
	def handle_key (self, string, keysym):
		if not self.editing:
			self.begin_editing ()		 
		if string:
			self.add_text (string)

		else:
			try:
				{ gtk.keysyms.Delete   : self.delete_char		,
				  gtk.keysyms.BackSpace: self.backspace_char	,
				  gtk.keysyms.Left	   : self.move_index_back	,
				  gtk.keysyms.Right    : self.move_index_forward,
				  gtk.keysyms.Up	   : self.move_index_up		,
				  gtk.keysyms.Down	   : self.move_index_down	,
				  gtk.keysyms.Home	   : self.move_index_home	,
				  gtk.keysyms.End	   : self.move_index_end	}[keysym]()
			except:
				return False
		self.emit ("title_changed", self.text, 65)
		return True
		
	def add_text (self, string):
		left = self.text[:self.index]
		right = self.text[self.index:]
		self.text = left + string + right
		self.index += len (string)
		
	def delete_char (self):
		left = self.text[:self.index]
		right = self.text[self.index+1:]
		self.text = left+right
		
	def backspace_char (self):
		left = self.text[:self.index-1]
		right = self.text[self.index:]
		self.text = left+right
		self.index-=1
		if self.index < 0:
			self.index = 0
			
	def move_index_back (self):
		if self.index <= 0:
			return
		self.index-=1
		
	def move_index_forward (self):
		if self.index >= len(self.text):
			return
		self.index+=1
		
	def move_index_up (self):
		lines = self.text.splitlines ()
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
			self.index -= len (lines[-1])+1
			return
		dist = self.index - loc -1
		self.index = loc
		if dist < len (lines[line]):
			self.index -= (len (lines[line]) - dist)
		else:
			self.index -= 1
	
	def move_index_down (self):
		lines = self.text.splitlines ()
		if len (lines) == 1:
			return
		loc = 0
		line = 0
		for i in lines:
			loc += len (i)+1
			if loc > self.index:
				break
			line += 1
		if line >= len (lines)-1:
			return
		dist = self.index - (loc - len (lines[line]))+1
		self.index = loc
		if dist > len (lines[line+1]):
			self.index += len (lines[line+1])
		else:
			self.index += dist	  
			
	def move_index_home (self):
		lines = self.text.splitlines ()
		loc = 0
		line = 0
		for i in lines:
			loc += len (i) + 1
			if loc > self.index:
				self.index = loc-len (i) - 1
				return
			line += 1
			
	def move_index_end (self):
		lines = self.text.splitlines ()
		loc = 0
		line = 0
		for i in lines:
			loc += len (i)+1
			if loc > self.index:
				self.index = loc-1
				return
			line += 1

	def find_connection (self, other):
		'''Should find the closest distance between us and our child.
		   In reality, we just calculate which corners are closest and return them'''
		if self.editing or other.editing:
			return (None, None)


		xfrom = self.ul[0]-((self.ul[0]-self.lr[0]) / 2.)
		yfrom = self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)
		xto = other.ul[0]-((other.ul[0]-other.lr[0]) / 2.)
		yto = other.ul[1]-((other.ul[1]-other.lr[1]) / 2.)

		return ((xfrom, yfrom), (xto, yto))
			
	def update_save (self):
		self.text_element.replaceWholeText (self.text)
		self.element.setAttribute ("cursor", str(self.index))
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
			else:
				print "Unknown: "+n.nodeName
		
	def load_add_parent (self, parent):
		self.parents.append (parent)


