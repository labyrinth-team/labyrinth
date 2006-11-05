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
import UndoManager

STYLE_CONTINUE=0
STYLE_END=1
STYLE_BEGIN=2
ndraw =0

MODE_EDITING = 0
MODE_IMAGE = 1
MODE_DRAW = 2

UNDO_RESIZE = 0
UNDO_DRAW = 1

class DrawingThought (BaseThought.ResizableThought):
	class DrawingPoint (object):
		def __init__ (self, coords, style=STYLE_CONTINUE):
			self.x = coords[0]
			self.y = coords[1]
			self.style = style
		def move_by (self, x, y):
			self.x += x
			self.y += y

	def __init__ (self, coords, pango_context, thought_number, save, undo, loading):
		global ndraw
		super (DrawingThought, self).__init__(save, "drawing_thought", undo)
		ndraw+=1
		self.identity = thought_number
		self.want_move = False
		self.points = []
		self.text = _("Drawing #%d" % ndraw)
		if not loading:
			margin = utils.margin_required (utils.STYLE_NORMAL)
			self.ul = (coords[0]-margin[0], coords[1]-margin[1])
			self.lr = (coords[0]+100+margin[2], coords[1]+100+margin[3])
			self.min_x = coords[0]+90
			self.max_x = coords[0]+15
			self.min_y = coords[1]+90
			self.max_y = coords[1]+15
			self.width = 100
			self.height = 100

		self.all_okay = True

	def draw (self, context):
		utils.draw_thought_outline (context, self.ul, self.lr, self.am_selected, self.am_primary, utils.STYLE_NORMAL)
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

	def want_motion (self):
		return self.want_move

	def recalc_edges (self):
		self.lr = (self.ul[0]+self.width, self.ul[1]+self.height)

	def undo_resize (self, action, mode):
		self.undo.block ()
		if mode == UndoManager.UNDO:
			choose = 0
		else:
			choose = 1
		self.ul = action.args[choose][0]
		self.width = action.args[choose][1]
		self.height = action.args[choose][2]
		self.recalc_edges ()
		self.emit ("update_links")
		self.emit ("update_view")
		self.undo.unblock ()

	def undo_drawing (self, action, mode):
		self.undo.block ()
		if mode == UndoManager.UNDO:
			choose = 1
			for p in action.args[0]:
				self.points.remove (p)
		else:
			choose = 2
			for p in action.args[0]:
				self.points.append (p)
		self.ul = action.args[choose][0]
		self.width = action.args[choose][1]
		self.height = action.args[choose][2]
		self.recalc_edges ()
		self.emit ("update_links")
		self.emit ("update_view")
		self.undo.unblock ()

	def process_button_down (self, event, mode):
		modifiers = gtk.accelerator_get_default_mod_mask ()
		self.button_down = True
		if event.button == 1:
			if event.type == gtk.gdk.BUTTON_PRESS:
				self.emit ("select_thought", event.state & modifiers)
				self.emit ("update_view")
			if mode == MODE_EDITING and self.resizing != self.RESIZE_NONE:
				self.want_move = True
				self.drawing = False
				self.orig_size = (self.ul, self.width, self.height)
				return True
			elif mode == MODE_DRAW:
				self.want_move = True
				self.drawing = True
				self.orig_size = (self.ul, self.width, self.height)
				self.ins_points = []
				return True
		elif event.button == 3:
			self.emit ("popup_requested", (event.x, event.y), 1)
		self.emit ("update_view")


	def process_button_release (self, event, unending_link, mode):
		self.button_down = False
		if unending_link:
			unending_link.set_child (self)
			self.emit ("claim_unending_link")
		if len(self.points) > 0:
			self.points[-1].style=STYLE_END
		self.emit ("update_view")
		if self.want_move and not self.drawing:
			self.undo.add_undo (UndoManager.UndoAction (self, UNDO_RESIZE, self.undo_resize, \
														self.orig_size, (self.ul, self.width, self.height)))
		elif self.want_move:
			self.undo.add_undo (UndoManager.UndoAction (self, UNDO_DRAW, self.undo_drawing, \
														self.ins_points, self.orig_size, \
														(self.ul, self.width, self.height)))
			self.want_move = False

	def handle_motion (self, event, mode):
		if (self.resizing == self.RESIZE_NONE or not self.want_move or not event.state & gtk.gdk.BUTTON1_MASK) \
		   and mode != MODE_DRAW:
			if not event.state & gtk.gdk.BUTTON1_MASK or mode != MODE_EDITING:
				return False
			else:
				self.emit ("create_link", \
				 (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
		diffx = event.x - self.motion_coords[0]
		diffy = event.y - self.motion_coords[1]
		change = (len(self.points) == 0)
		tmp = self.motion_coords
		self.motion_coords = (event.x, event.y)
		if self.resizing != self.RESIZE_NONE:
			if self.resizing == self.RESIZE_LEFT:
				if self.ul[0] + diffx > self.min_x:
					self.motion_coords = tmp
					return True
				self.ul = (self.ul[0]+diffx, self.ul[1])
				if change:
					self.max_x += diffx
			elif self.resizing == self.RESIZE_RIGHT:
				if self.lr[0] + diffx < self.max_x:
					self.motion_coords = tmp
					return True
				self.lr = (self.lr[0]+diffx, self.lr[1])
				if change:
					self.min_x += diffx
			elif self.resizing == self.RESIZE_TOP:
				if self.ul[1] + diffy > self.min_y:
					self.motion_coords = tmp
					return True
				self.ul = (self.ul[0], self.ul[1]+diffy)
				if change:
					self.max_y += diffy
			elif self.resizing == self.RESIZE_BOTTOM:
				if self.lr[1] + diffy < self.max_y:
					self.motion_coords = tmp
					return True
				self.lr = (self.lr[0], self.lr[1]+diffy)
				if change:
					self.min_y += diffy
			elif self.resizing == self.RESIZE_UL:
				if self.ul[1] + diffy > self.min_y or self.ul[0] + diffx > self.min_x:
					self.motion_coords = tmp
					return True
				self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
				if change:
					self.max_x += diffx
					self.max_y += diffy
			elif self.resizing == self.RESIZE_UR:
				if self.ul[1] + diffy > self.min_y or self.lr[0] + diffx < self.max_x:
					self.motion_coords = tmp
					return True
				self.ul = (self.ul[0], self.ul[1]+diffy)
				self.lr = (self.lr[0]+diffx, self.lr[1])
				if change:
					self.min_x += diffx
					self.max_y += diffy
			elif self.resizing == self.RESIZE_LL:
				if self.lr[1] + diffy < self.max_y or self.ul[0] + diffx > self.min_x:
					self.motion_coords = tmp
					return True
				self.ul = (self.ul[0]+diffx, self.ul[1])
				self.lr = (self.lr[0], self.lr[1]+diffy)
				if change:
					self.max_x += diffx
					self.min_y += diffy
			elif self.resizing == self.RESIZE_LR:
				if self.lr[1] + diffy < self.max_y:
					self.motion_coords = tmp
					return True
				if self.lr[0] + diffx < self.max_x:
					self.motion_coords = tmp
					return True
				self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
				if change:
					self.min_x += diffx
					self.min_y += diffy
			self.width = self.lr[0] - self.ul[0]
			self.height = self.lr[1] - self.ul[1]
			self.emit ("update_links")
			self.emit ("update_view")
			return True

		elif mode == MODE_DRAW and (event.state & gtk.gdk.BUTTON1_MASK):
			if event.x < self.ul[0]+5:
				self.ul = (event.x-5, self.ul[1])
			elif event.x > self.lr[0]-5:
				self.lr = (event.x+5, self.lr[1])
			if event.y < self.ul[1]+5:
				self.ul = (self.ul[0], event.y-5)
			elif event.y > self.lr[1]-5:
				self.lr = (self.lr[0], event.y+5)

			if event.x < self.min_x:
				self.min_x = event.x-10
			elif event.x > self.max_x:
				self.max_x = event.x+5
			if event.y < self.min_y:
				self.min_y = event.y-10
			elif event.y > self.max_y:
				self.max_y = event.y+5
			self.width = self.lr[0] - self.ul[0]
			self.height = self.lr[1] - self.ul[1]
			if len(self.points) == 0 or self.points[-1].style == STYLE_END:
				p = self.DrawingPoint (event.get_coords(), STYLE_BEGIN)
			else:
				p = self.DrawingPoint (event.get_coords(), STYLE_CONTINUE)
			self.points.append (p)
			self.ins_points.append (p)
		self.emit ("update_links")
		self.emit ("update_view")
		return True

	def move_by (self, x, y):
		self.ul = (self.ul[0]+x, self.ul[1]+y)
		self.min_x += x
		self.min_y += y
		self.max_x += x
		self.max_y += y
		for p in self.points:
			p.move_by (x,y)
		self.recalc_edges ()
		self.emit ("update_links")

	def update_save (self):
		next = self.element.firstChild
		while next:
			m = next.nextSibling
			if next.nodeName == "point":
				self.element.removeChild (next)
				next.unlink ()
			next = m
		text = self.extended_buffer.get_text ()
		if text:
			self.extended_element.replaceWholeText (text)
		else:
			self.extended_element.replaceWholeText ("LABYRINTH_AUTOGEN_TEXT_REMOVE")
		self.element.setAttribute ("ul-coords", str(self.ul))
		self.element.setAttribute ("lr-coords", str(self.lr))
		self.element.setAttribute ("identity", str(self.identity))
		self.element.setAttribute ("min_x", str(self.min_x))
		self.element.setAttribute ("min_y", str(self.min_y))
		self.element.setAttribute ("max_x", str(self.max_x))
		self.element.setAttribute ("max_y", str(self.max_y))

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
		for p in self.points:
			elem = doc.createElement ("point")
			self.element.appendChild (elem)
			elem.setAttribute ("coords", str((p.x,p.y)))
			elem.setAttribute ("type", str(p.style))
		return

	def load (self, node):
		tmp = node.getAttribute ("ul-coords")
		self.ul = utils.parse_coords (tmp)
		tmp = node.getAttribute ("lr-coords")
		self.lr = utils.parse_coords (tmp)
		self.identity = int (node.getAttribute ("identity"))
		self.min_x = float(node.getAttribute ("min_x"))
		self.min_y = float(node.getAttribute ("min_y"))
		self.max_x = float(node.getAttribute ("max_x"))
		self.max_y = float(node.getAttribute ("max_y"))

		self.width = self.lr[0] - self.ul[0]
		self.height = self.lr[1] - self.ul[1]

		if node.hasAttribute ("current_root"):
			self.am_selected = True
		else:
			self.am_selected = False
		if node.hasAttribute ("primary_root"):
			self.am_primary = True
		else:
			self.am_primary = False

		for n in node.childNodes:
			if n.nodeName == "Extended":
				for m in n.childNodes:
					if m.nodeType == m.TEXT_NODE:
						text = m.data
						if text != "LABYRINTH_AUTOGEN_TEXT_REMOVE":
							self.extended_buffer.set_text (text)
			elif n.nodeName == "point":
				style = int (n.getAttribute ("type"))
				tmp = n.getAttribute ("coords")
				c = utils.parse_coords (tmp)
				self.points.append (self.DrawingPoint (c, style))
			else:
				print "Unknown node type: "+str(n.nodeName)

	def export (self, context, move_x, move_y):
		utils.export_thought_outline (context, self.ul, self.lr, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
									  (move_x, move_y))
		cwidth = context.get_line_width ()
		context.set_line_width (1)
		if len (self.points) > 0:
			for p in self.points:
				if p.style == STYLE_BEGIN:
					context.move_to (p.x+move_x, p.y+move_y)
				else:
					context.line_to (p.x+move_x,p.y+move_y)

		context.set_line_width (cwidth)
		context.stroke ()
		return

	def includes (self, coords, mode):
		if not self.ul or not self.lr:
			return False

		if self.want_move and mode == MODE_DRAW:
			self.emit ("change_mouse_cursor", gtk.gdk.PENCIL)
			return True

		inside = (coords[0] < self.lr[0] + self.sensitive) and \
				 (coords[0] > self.ul[0] - self.sensitive) and \
			     (coords[1] < self.lr[1] + self.sensitive) and \
			     (coords[1] > self.ul[1] - self.sensitive)

		self.resizing = self.RESIZE_NONE
		self.motion_coords = coords


		if inside and (mode != MODE_EDITING or self.button_down):
			if mode == MODE_DRAW:
				self.emit ("change_mouse_cursor", gtk.gdk.PENCIL)
			else:
				self.emit ("change_mouse_cursor", gtk.gdk.LEFT_PTR)
			return inside

		if inside:
			# 2 cases: 1. The click was within the main area
			#		   2. The click was near the border
			# In the first case, we handle as normal
			# In the second case, we want to intercept all the fun thats
			# going to happen so we can resize the thought
			if abs (coords[0] - self.ul[0]) < self.sensitive:
				# its near the top edge somewhere
				if abs (coords[1] - self.ul[1]) < self.sensitive:
				# Its in the ul corner
					self.resizing = self.RESIZE_UL
					self.emit ("change_mouse_cursor", gtk.gdk.TOP_LEFT_CORNER)
				elif abs (coords[1] - self.lr[1]) < self.sensitive:
				# Its in the ll corner
					self.resizing = self.RESIZE_LL
					self.emit ("change_mouse_cursor", gtk.gdk.BOTTOM_LEFT_CORNER)
				elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
				#anywhere else along the left edge
					self.resizing = self.RESIZE_LEFT
					self.emit ("change_mouse_cursor", gtk.gdk.LEFT_SIDE)
			elif abs (coords[0] - self.lr[0]) < self.sensitive:
				if abs (coords[1] - self.ul[1]) < self.sensitive:
				# Its in the UR corner
					self.resizing = self.RESIZE_UR
					self.emit ("change_mouse_cursor", gtk.gdk.TOP_RIGHT_CORNER)
				elif abs (coords[1] - self.lr[1]) < self.sensitive:
				# Its in the lr corner
					self.resizing = self.RESIZE_LR
					self.emit ("change_mouse_cursor", gtk.gdk.BOTTOM_RIGHT_CORNER)
				elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
				#anywhere else along the right edge
					self.resizing = self.RESIZE_RIGHT
					self.emit ("change_mouse_cursor", gtk.gdk.RIGHT_SIDE)
			elif abs (coords[1] - self.ul[1]) < self.sensitive and \
				 (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
				# Along the top edge somewhere
					self.resizing = self.RESIZE_TOP
					self.emit ("change_mouse_cursor", gtk.gdk.TOP_SIDE)
			elif abs (coords[1] - self.lr[1]) < self.sensitive and \
				 (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
				# Along the bottom edge somewhere
					self.resizing = self.RESIZE_BOTTOM
					self.emit ("change_mouse_cursor", gtk.gdk.BOTTOM_SIDE)
			else:
				self.emit ("change_mouse_cursor", gtk.gdk.LEFT_PTR)
		self.want_move = (self.resizing != self.RESIZE_NONE)
		return inside
