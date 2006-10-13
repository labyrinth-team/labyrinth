# BaseThought.py
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import gobject
import gtk
import utils

class BaseThought (gobject.GObject):
	''' the basic class to derive other thouhts from'''
	__gsignals__ = dict (delete_thought		= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
						 title_changed		= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
						 change_cursor      = (gobject.SIGNAL_RUN_FIRST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)))
	
	def __init__ (self):
		super (BaseThought, self).__init__()
		self.am_primary = False
		self.am_root = False
		self.editing = False
		self.identity = -1
		self.text = "Unknown Thought Type"
		
	def includes (self, coords, allow_resize = False):
		print "Warning: includes is not implemented for one thought type"
		return False
		
	def draw (self, context):
		print "Warning: drawing is not implemented for one thought type"
		return
		
	def handle_movement (self, coords, move=True, edit_mode = False):
		print "Warning: handle_movement is not implemented for this node type"
		return
	
	def handle_key (self, string, keysym, state):
		print "Warning: handle_key is not implemented for this node type"
		return False
		
	def find_connection (self, other):
		print "Warning: Unable to find connection for this node type"
		return (None, None)
		
	def update_save (self):
		print "Warning: Saving is not working for a node type.  This node will not be saved."
		return
		
	def load_data (self, node):
		print "Warning: Loading this type of node isn't allowed just now."
		return
		
	def begin_editing (self):
		print "Warning: Cannot edit this thought type"
		return
	
	def finish_editing (self):
		print "Warning: This node type cannot be edited"
		return
	
	def become_active_root (self):
		print "Warning: This type of node cannot become root"
		return
		
	def finish_active_root (self):
		print "Warning: This type of not isn't currently root"
		return
		
	def become_primary_thought (self):
		print "Warning: Become primary root isn't implemented for this node type"
		return

	def want_movement (self):
		return False
	
	def finish_motion (self):
		return
		
	
class ResizableThought (BaseThought):
	MOTION_NONE = 0
	MOTION_LEFT = 1
	MOTION_RIGHT = 2
	MOTION_TOP = 3
	MOTION_BOTTOM = 4
	MOTION_UL = 5
	MOTION_UR = 6
	MOTION_LL = 7
	MOTION_LR = 8
	
	def __init__ (self):
		super (ResizableThought, self).__init__()
		self.sensitive = 5
		self.resizing = False
		
	def includes (self, coords, allow_resize = False):
		self.resizing = self.MOTION_NONE
		self.motion_coords = coords
		if not self.ul or not self.lr:
			return False
		elif allow_resize:
			# 2 cases: 1. The click was within the main area
			#		   2. The click was near the border
			# In the first case, we handle as normal
			# In the second case, we want to intercept all the fun thats
			# going to happen so we can resize the thought
			if abs (coords[0] - self.ul[0]) < self.sensitive:
				# its near the top edge somewhere
				if abs (coords[1] - self.ul[1]) < self.sensitive:
				# Its in the ul corner
					self.resizing = self.MOTION_UL
					self.emit ("change_cursor", gtk.gdk.TOP_LEFT_CORNER, None)
					return True
				elif abs (coords[1] - self.lr[1]) < self.sensitive:
				# Its in the ll corner
					self.resizing = self.MOTION_LL
					self.emit ("change_cursor", gtk.gdk.BOTTOM_LEFT_CORNER, None)
					return True
				elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
				#anywhere else along the left edge
					self.resizing = self.MOTION_LEFT
					self.emit ("change_cursor", gtk.gdk.LEFT_SIDE, None)
					return True
				else:
				# Not interested
					return False
			elif abs (coords[0] - self.lr[0]) < self.sensitive:
				if abs (coords[1] - self.ul[1]) < self.sensitive:
				# Its in the UR corner
					self.resizing = self.MOTION_UR
					self.emit ("change_cursor", gtk.gdk.TOP_RIGHT_CORNER, None)
					return True
				elif abs (coords[1] - self.lr[1]) < self.sensitive:
				# Its in the lr corner
					self.resizing = self.MOTION_LR
					self.emit ("change_cursor", gtk.gdk.BOTTOM_RIGHT_CORNER, None)
					return True
				elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
				#anywhere else along the right edge
					self.resizing = self.MOTION_RIGHT
					self.emit ("change_cursor", gtk.gdk.RIGHT_SIDE, None)
					return True
				else:
				# Not interested
					return False
			elif abs (coords[1] - self.ul[1]) < self.sensitive and \
				 (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
				# Along the top edge somewhere
					self.resizing = self.MOTION_TOP
					self.emit ("change_cursor", gtk.gdk.TOP_SIDE, None)
					return True
			elif abs (coords[1] - self.lr[1]) < self.sensitive and \
				 (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
				# Along the bottom edge somewhere
					self.resizing = self.MOTION_BOTTOM
					self.emit ("change_cursor", gtk.gdk.BOTTOM_SIDE, None)
					return True
		return coords[0] < self.lr[0] and coords[0] > self.ul[0] and \
			   coords[1] < self.lr[1] and coords[1] > self.ul[1]
		
		
	def draw (self, context):
		context.move_to (self.ul[0], self.ul[1])
		context.line_to (self.ul[0], self.lr[1])
		context.line_to (self.lr[0], self.lr[1])
		context.line_to (self.lr[0], self.ul[1])
		context.line_to (self.ul[0], self.ul[1])
		context.set_source_rgb (1.0,1.0,1.0)
		context.fill_preserve ()
		context.set_source_rgb (0,0,0)
		context.stroke ()
		return
		
	def handle_movement (self, coords, edit_mode = False):
		diffx = coords[0] - self.motion_coords[0]
		diffy = coords[1] - self.motion_coords[1]
		self.motion_coords = coords
		if self.resizing == self.MOTION_NONE:
			# Actually, we have to move the entire thing
			self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
			self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
			return
		elif self.resizing == self.MOTION_LEFT:
			self.ul = (self.ul[0]+diffx, self.ul[1])
		elif self.resizing == self.MOTION_RIGHT:
			self.lr = (self.lr[0]+diffx, self.lr[1])
		elif self.resizing == self.MOTION_TOP:
			self.ul = (self.ul[0], self.ul[1]+diffy)
		elif self.resizing == self.MOTION_BOTTOM:
			self.lr = (self.lr[0], self.lr[1]+diffy)
		elif self.resizing == self.MOTION_UL:
			self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
		elif self.resizing == self.MOTION_UR:
			self.ul = (self.ul[0], self.ul[1]+diffy)
			self.lr = (self.lr[0]+diffx, self.lr[1])
		elif self.resizing == self.MOTION_LL:
			self.ul = (self.ul[0]+diffx, self.ul[1])
			self.lr = (self.lr[0], self.lr[1]+diffy)
		elif self.resizing == self.MOTION_LR:
			self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
		
		return
		
	def want_movement (self):
		return self.resizing != self.MOTION_NONE
		
	def finish_motion (self):
		self.resizing = self.MOTION_NONE
		return
