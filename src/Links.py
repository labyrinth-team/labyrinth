#! /usr/bin env python

# Link.py
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

import gobject

import TextThought
import utils
import xml.dom.minidom as dom

class Link (gobject.GObject):
	
	def __init__ (self, parent = None, child = None, element=None, from_coords = None, load=None):
		super (Link, self).__init__()
		self.parent = parent
		self.child = child
		self.end = None
		self.start = from_coords
		self.element = element
		self.strength = 2
		if load:
			self.load_data (load)
	
	def connects (self, parent, child):
		if (self.parent == parent and self.child == child) or \
			(self.child == parent and self.parent == child):
			return True
		return False
		
	def update (self):
		(self.start, self.end) = self.parent.find_connection (self.child)

	def set_new_end (self, coords):
		self.end = coords
	
	def uses (self, thought):
		if self.parent == thought or self.child == thought:
			return True
		return False	
	
	def draw (self, context):
		if not self.start or not self.end:
			return
		cwidth = context.get_line_width ()
		context.set_line_width (self.strength)
		context.move_to (self.start[0], self.start[1])
		context.line_to (self.end[0], self.end[1])
		context.stroke ()
		context.set_line_width (cwidth)
		
	def mod_strength (self, parent, child):
		if self.parent == parent:
			self.strength += 1
		else:
			self.strength -= 1
		if self.strength == 0:
			return True
		return False

	def update_save (self):
		self.element.setAttribute ("start", str(self.start))
		self.element.setAttribute ("end", str(self.end))
		self.element.setAttribute ("strength", str(self.strength))
		if self.child:
			self.element.setAttribute ("child", str(self.child.identity))
		else:
			self.element.setAttribute ("child", "None")
		if self.parent:
			self.element.setAttribute ("parent", str(self.parent.identity))
		else:
			self.element.setAttribute ("parent", "None")
		
	def load_data (self, node):
		self.parent_number = self.child_number = -1
		tmp = node.getAttribute ("end")
		if not tmp:
			print "No tmp found"
			return
		self.end = utils.parse_coords (tmp)
		tmp = node.getAttribute ("start")
		if not tmp:
			print "No start found"
			return
		self.start = utils.parse_coords (tmp)
		self.strength = int(node.getAttribute ("strength"))
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

	def set_ends (self, parent, child):
		self.parent = parent
		self.child = child
		
