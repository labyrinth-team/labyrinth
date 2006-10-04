# DrawingThought.py
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

import gtk
import xml.dom.minidom as dom
import xml.dom
import gettext
_ = gettext.gettext

import BaseThought
import utils

STYLE_CONTINUE=0
STYLE_END=1
STYLE_BEGIN=2
ndraw =0

class DrawingPoint (object):
	def __init__ (self, coords, style=STYLE_CONTINUE):
		# As this is only really used for drawing and
		# cairo wants indiviual points, we split coords here
		self.x = coords[0]
		self.y = coords[1]
		self.style=style
	def move_by (self, x, y):
		self.x += x
		self.y += y

class DrawingThought (BaseThought.ResizableThought):
	def __init__ (self, coords=None, ident=None, element=None, load=None):
		global ndraw
		super (DrawingThought, self).__init__()
		ndraw+=1
		self.element = element
		self.points = []
		self.text = _("Drawing #%d" %ndraw)
		if not load:
			self.ul = (coords[0]-5, coords[1]-5)
			self.identity = ident
			self.lr = (coords[0]+100, coords[1]+100)
			self.min_x = coords[0]+90
			self.max_x = coords[0]+15
			self.min_y = coords[1]+90
			self.max_y = coords[1]+15
			self.emit ("title_changed", self.text, 65)
		else:
			self.load_data (load)

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
	
	def handle_movement (self, coords, move=True):

		diffx = coords[0] - self.motion_coords[0]
		diffy = coords[1] - self.motion_coords[1]
		change = (len(self.points) == 0)
		tmp = self.motion_coords
		self.motion_coords = coords
		
		if self.resizing != self.MOTION_NONE:
			if self.resizing == self.MOTION_LEFT:
				if self.ul[0] + diffx > self.min_x:
					self.motion_coords = tmp
					return
				self.ul = (self.ul[0]+diffx, self.ul[1])
				if change:
					self.max_x += diffx
			elif self.resizing == self.MOTION_RIGHT:
				if self.lr[0] + diffx < self.max_x:
					self.motion_coords = tmp
					return
				self.lr = (self.lr[0]+diffx, self.lr[1])
				if change:
					self.min_x += diffx
			elif self.resizing == self.MOTION_TOP:
				if self.ul[1] + diffy > self.min_y:
					self.motion_coords = tmp
					return
				self.ul = (self.ul[0], self.ul[1]+diffy)
				if change:
					self.max_y += diffy
			elif self.resizing == self.MOTION_BOTTOM:
				if self.lr[1] + diffy < self.max_y:
					self.motion_coords = tmp
					return
				self.lr = (self.lr[0], self.lr[1]+diffy)
				if change:
					self.min_y += diffy
			elif self.resizing == self.MOTION_UL:
				if self.ul[1] + diffy > self.min_y or self.ul[0] + diffx > self.min_x:
					self.motion_coords = tmp
					return
				self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
				if change:
					self.max_x += diffx
					self.max_y += diffy
			elif self.resizing == self.MOTION_UR:
				if self.ul[1] + diffy > self.min_y or self.lr[0] + diffx < self.max_x:
					self.motion_coords = tmp
					return
				self.ul = (self.ul[0], self.ul[1]+diffy)
				self.lr = (self.lr[0]+diffx, self.lr[1])
				if change:
					self.min_x += diffx
					self.max_y += diffy
			elif self.resizing == self.MOTION_LL:
				if self.lr[1] + diffy < self.max_y or self.ul[0] + diffx > self.min_x:
					self.motion_coords = tmp
					return
				self.ul = (self.ul[0]+diffx, self.ul[1])
				self.lr = (self.lr[0], self.lr[1]+diffy)
				if change:
					self.max_x += diffx
					self.min_y += diffy
			elif self.resizing == self.MOTION_LR:
				if self.lr[1] + diffy < self.max_y:
					self.motion_coords = tmp
					return
				if self.lr[0] + diffx < self.max_x:
					self.motion_coords = tmp
					return
				self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
				if change:
					self.min_x += diffx
					self.min_y += diffy
			return
		if move:
			tmp = self.motion_coords
			self.motion_coords = coords
			# Actually, we have to move the entire thing
			self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
			self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
			self.min_x += diffx
			self.min_y += diffy
			self.max_x += diffx
			self.max_y += diffy
			for p in self.points:
				p.move_by (diffx, diffy)
			return
			
		if coords[0] < self.ul[0]:
			self.ul = (coords[0]-5, self.ul[1])
		elif coords[0] > self.lr[0]:
			self.lr = (coords[0]+5, self.lr[1])
		if coords[1] < self.ul[1]:
			self.ul = (self.ul[0], coords[1]-5)
		elif coords[1] > self.lr[1]:
			self.lr = (self.lr[0], coords[1]+5)

		if coords[0] < self.min_x:
			self.min_x = coords[0]-10
		elif coords[0] > self.max_x:
			self.max_x = coords[0]+5
		if coords[1] < self.min_y:
			self.min_y = coords[1]-10
		elif coords[1] > self.max_y:
			self.max_y = coords[1]+5

		if len(self.points) == 0 or self.points[-1].style == STYLE_END:
			self.points.append (DrawingPoint (coords, STYLE_BEGIN))
		else:
			self.points.append (DrawingPoint (coords, STYLE_CONTINUE))
		
	def handle_key (self, string, keysym):
		# Since we can't handle text in an drawing node, we ignore it.
		return False	
	
	def finish_motion (self):
		if len(self.points) > 0:
			self.points[-1].style=STYLE_END
		self.motion = self.MOTION_NONE
		self.emit ("change_cursor", gtk.gdk.LEFT_PTR, None)
		return
	
	def want_movement (self):
		return True
		
	def draw (self, context):
		context.move_to (self.ul[0], self.ul[1]+10)
		context.line_to (self.ul[0], self.lr[1]-10)
		context.curve_to (self.ul[0], self.lr[1], self.ul[0], self.lr[1], self.ul[0]+10, self.lr[1])
		context.line_to (self.lr[0]-10, self.lr[1])
		context.curve_to (self.lr[0], self.lr[1], self.lr[0], self.lr[1], self.lr[0], self.lr[1]-10)
		context.line_to (self.lr[0], self.ul[1]+10)
		context.curve_to (self.lr[0], self.ul[1], self.lr[0], self.ul[1], self.lr[0]-10, self.ul[1])
		context.line_to (self.ul[0]+10, self.ul[1])
		context.curve_to (self.ul[0], self.ul[1], self.ul[0], self.ul[1], self.ul[0], self.ul[1]+10)

		context.set_source_rgb (1.0,1.0,1.0)
		if self.am_root:
			context.set_source_rgb (0.0,0.9,0.9)
		elif self.am_primary:
			context.set_source_rgb (1.0,0.5,0.5)
		context.fill_preserve ()
		context.set_source_rgb (0,0,0)
		cwidth = context.get_line_width ()
		context.set_line_width (1)
		if len (self.points) > 0:
			for p in self.points:
				if p.style == STYLE_BEGIN:
					context.move_to (p.x, p.y)
				else:
					context.line_to (p.x,p.y)		
		
		context.set_line_width (cwidth)
		context.stroke ()
		return
	
	def find_connection (self, other):
		if self.editing or other.editing:
			return (None, None)
		xfrom = self.ul[0]-((self.ul[0]-self.lr[0]) / 2.)
		yfrom = self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)
		xto = other.ul[0]-((other.ul[0]-other.lr[0]) / 2.)
		yto = other.ul[1]-((other.ul[1]-other.lr[1]) / 2.)

		return ((xfrom, yfrom), (xto, yto))
		
	def update_save (self):
		next = self.element.firstChild
		while next:
			m = next.nextSibling
			self.element.removeChild (next)
			next.unlink ()
			next = m
			
		self.element.setAttribute ("ul-coords", str(self.ul))
		self.element.setAttribute ("lr-coords", str(self.lr))
		self.element.setAttribute ("identity", str(self.identity))
		self.element.setAttribute ("min_x", str(self.min_x))
		self.element.setAttribute ("min_y", str(self.min_y))
		self.element.setAttribute ("max_x", str(self.max_x))
		self.element.setAttribute ("max_y", str(self.max_y))
		
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
		doc = self.element.ownerDocument
		for p in self.points:
			elem = doc.createElement ("point")
			self.element.appendChild (elem)
			elem.setAttribute ("coords", str((p.x,p.y)))
			elem.setAttribute ("type", str(p.style))
		return
		
	def load_data (self, node):
		tmp = node.getAttribute ("ul-coords")
		self.ul = utils.parse_coords (tmp)
		tmp = node.getAttribute ("lr-coords")
		self.lr = utils.parse_coords (tmp)
		self.identity = int (node.getAttribute ("identity"))
		self.min_x = float(node.getAttribute ("min_x"))
		self.min_y = float(node.getAttribute ("min_y"))
		self.max_x = float(node.getAttribute ("max_x"))
		self.max_y = float(node.getAttribute ("max_y"))

		if node.hasAttribute ("current_root"):
			self.am_root = True
		else:
			self.am_root = False
		if node.hasAttribute ("primary_root"):
			self.am_primary = True
		else:
			self.am_primary = False
			
		for n in node.childNodes:
			if n.nodeName != "point":
				print "Unknown node type: "+str(n.nodeName)
				continue
			style = int (n.getAttribute ("type"))
			tmp = n.getAttribute ("coords")
			c = utils.parse_coords (tmp)
			self.points.append (DrawingPoint (c, style))
