# ImageThought.py
# This file is part of labyrinth
#
# Copyright (C) 2006 - Don Scorgie <DonScorgie@Blueyonder.co.uk>
#
# labyrinth is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# labyrinth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import gtk

import BaseThought


class ImageThought (BaseThought.ResizableThought):
	def __init__ (self, filename=None, coords=None, ident=None, element=None, load=None):
		super (ImageThought, self).__init__()
		self.element = element
		self.ul = (coords[0]-5, coords[1]-5)
		
		self.element = element
		
		if not load:
			self.identity = ident
		else:
			self.load_data (load)
		self.okay = self.load_image (filename)
		
	def load_image (self, filename):
		if not filename:
			print "Error: Filename not given!!!!"
			return False
			
		try:
			self.orig_pic = gtk.gdk.pixbuf_new_from_file (filename)
		except:
			return False
		self.width = self.orig_pic.get_width ()
		self.height = self.orig_pic.get_height ()
		
		self.lr = (self.ul[0]+self.width+5, self.ul[1]+self.height+5)
		self.pic = self.orig_pic
		self.text = filename
		self.emit ("title_changed", self.text, 65)
		return True

	def draw (self, context):
		context.move_to (self.ul[0], self.ul[1])
		context.line_to (self.ul[0], self.lr[1])
		context.line_to (self.lr[0], self.lr[1])
		context.line_to (self.lr[0], self.ul[1])
		context.line_to (self.ul[0], self.ul[1])

		context.set_source_rgb (1.0,1.0,1.0)
		if self.am_root:
			context.set_source_rgb (0.0,0.9,0.9)
		elif self.am_primary:
			context.set_source_rgb (1.0,0.5,0.5)
		context.fill_preserve ()
		context.set_source_rgb (0,0,0)
		context.stroke ()
		
		context.set_source_pixbuf (self.pic, self.ul[0]+5, self.ul[1]+5)
		context.rectangle (self.ul[0], self.ul[1], self.width, self.height)
		context.fill ()
		context.set_source_rgb (0,0,0)
		
		return
		
	def handle_movement (self, coords):
		diffx = coords[0] - self.motion_coords[0]
		diffy = coords[1] - self.motion_coords[1]
		
		tmp = self.motion_coords
		self.motion_coords = coords
		if self.resizing == self.MOTION_NONE:
			# Actually, we have to move the entire thing
			self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
			self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
			return
		elif self.resizing == self.MOTION_LEFT:
			if self.width - diffx < 10:
				self.motion_coords = tmp
				return
			self.ul = (self.ul[0]+diffx, self.ul[1])
			self.width -= diffx
		elif self.resizing == self.MOTION_RIGHT:
			if self.width + diffx < 10:
				self.motion_coords = tmp
				return
			self.lr = (self.lr[0]+diffx, self.lr[1])
			self.width += diffx
		elif self.resizing == self.MOTION_TOP:
			if self.height - diffy < 10:
				self.motion_coords = tmp
				return
			self.ul = (self.ul[0], self.ul[1]+diffy)
			self.height -= diffy
		elif self.resizing == self.MOTION_BOTTOM:
			if self.height + diffy < 10:
				self.motion_coords = tmp
				return
			self.lr = (self.lr[0], self.lr[1]+diffy)
			self.height += diffy
		elif self.resizing == self.MOTION_UL:
			if self.height - diffy < 10 or self.width - diffx < 10:
				self.motion_coords = tmp
				return
			self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
			self.width -= diffx
			self.height -= diffy
		elif self.resizing == self.MOTION_UR:
			if self.height - diffy < 10 or self.width + diffx < 10:
				self.motion_coords = tmp
				return
			self.ul = (self.ul[0], self.ul[1]+diffy)
			self.lr = (self.lr[0]+diffx, self.lr[1])
			self.width += diffx
			self.height -= diffy
		elif self.resizing == self.MOTION_LL:
			if self.height + diffy < 10 or self.width - diffx < 10:
				self.motion_coords = tmp
				return
			self.ul = (self.ul[0]+diffx, self.ul[1])
			self.lr = (self.lr[0], self.lr[1]+diffy)
			self.width -= diffx
			self.height += diffy
		elif self.resizing == self.MOTION_LR:
			if self.height + diffy < 0:
				self.motion_coords = tmp
				return
			if self.width + diffx < 10:
				self.motion_coords = tmp
				return
			self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
			self.width += diffx
			self.height += diffy
		
		self.pic = self.orig_pic.scale_simple (self.width, self.height, gtk.gdk.INTERP_NEAREST)
		
		return
			
	def finish_motion (self):
		# Up till now, we've been using the fastest interp.  Here, its made best
		# Yes, it makes quite a big difference actually
		self.pic = self.orig_pic.scale_simple (int (self.width), int (self.height), gtk.gdk.INTERP_HYPER)
	
		self.resizing = self.MOTION_NONE
		return	
	
	def handle_key (self):
		# Since we can't handle text in an image node, we ignore it
		return False
		
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
		
	def begin_editing (self):
		return
	
	def finish_editing (self):
		return
	
	def become_active_root (self):
		self.am_root = True
		return
		
	def finish_active_root (self):
		self.am_root = False
		return
		
	def become_primary_thought (self):
		self.am_primary = True
		return

			
	
