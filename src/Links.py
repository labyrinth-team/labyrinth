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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#

import gobject
import gtk

import BaseThought
import utils
import math

def norm(x, y):
	mod = math.sqrt(abs((x[0]**2 - y[0]**2) + (x[1]**2 - y[1]**2)))
	return [abs(x[0]-y[0]) / (mod), abs(x[1] - y[1]) / (mod)]

class Link (gobject.GObject):
	__gsignals__ = dict (select_link         = (gobject.SIGNAL_RUN_FIRST,
											    gobject.TYPE_NONE,
											    (gobject.TYPE_PYOBJECT,)),						 
						 update_view		 = (gobject.SIGNAL_RUN_LAST,
						 						gobject.TYPE_NONE,
						 						()),
						 popup_requested     = (gobject.SIGNAL_RUN_FIRST,
						 					    gobject.TYPE_NONE,
						 					    (gobject.TYPE_PYOBJECT, gobject.TYPE_INT)))
	def __init__ (self, save, parent = None, child = None, start_coords = None, end_coords = None, strength = 2):
		super (Link, self).__init__()
		self.parent = parent
		self.child = child
		self.end = end_coords
		self.start = start_coords
		self.strength = strength
		self.element = save.createElement ("link")
		self.selected = False

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
		if self.strength == 0:
			return False
		return True

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

		#dx = self.start[0] - self.end[0]
		#dy = self.start[1] - self.end[1]
		#x2 = self.end[0] + (dx * 2 / 3)
		#y2 = self.end[1] + (dy / 3)
		#x3 = self.end[0] + (dx / 3)
		#y3 = self.end[1] + (dy * 2 / 3)
		#context.curve_to(x2,y2, x3, y3, self.end[0], self.end[1])
		context.line_to (self.end[0], self.end[1])

		context.stroke ()
		context.set_line_width (cwidth)

		if self.selected:
			st_norm = norm(self.start, self.end)
			start_x1 = self.start[0] + st_norm[1]*(5+self.strength)
			start_x2 = self.start[0] - st_norm[1]*(5+self.strength)
			start_y1 = self.start[1] - st_norm[0]*(5+self.strength)
			start_y2 = self.start[1] + st_norm[0]*(5+self.strength)
			end_x1 = self.end[0] + st_norm[1]*(5+self.strength)
			end_x2 = self.end[0] - st_norm[1]*(5+self.strength)
			end_y1 = self.end[1] - st_norm[0]*(5+self.strength)
			end_y2 = self.end[1] + st_norm[0]*(5+self.strength)
		
			context.set_line_width(0.3)

			context.move_to (start_x1, start_y1)
			context.line_to (start_x2, start_y2)
			context.line_to (end_x2, end_y2)
			context.line_to (end_x1, end_y1)
			context.line_to (start_x1, start_y1)
			
			context.stroke()
			context.set_line_width(cwidth)

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
				
	def process_button_down (self, event, mode, transformed):
		modifiers = gtk.accelerator_get_default_mod_mask ()
		self.button_down = True
		if event.button == 1:
			if event.type == gtk.gdk.BUTTON_PRESS:
				self.emit ("select_link", event.state & modifiers)
				self.emit ("update_view")
		elif event.button == 3:
			self.emit ("popup_requested", (event.x, event.y), 2)
		self.emit ("update_view")
		return False

	def process_button_release (self, event, unending_link, mode, transformed):
		return False

	def process_key_press (self, event, mode):
		handled = False
		if mode != BaseThought.MODE_EDITING:
			return handled
		if event.keyval == gtk.keysyms.plus or \
		   event.keyval == gtk.keysyms.KP_Add:
			self.strength += 1
			handled = True
		elif (event.keyval == gtk.keysyms.minus or \
			  event.keyval == gtk.keysyms.KP_Subtract) and \
			 self.strength > 1:
			self.strength -= 1
			handled = True
		self.emit("update_view")
		return handled

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
