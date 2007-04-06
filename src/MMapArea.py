#! /usr/bin/env python
# MMapArea.py
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

import time
import gtk
import pango
import gobject
import gettext
import copy
import cairo
_ = gettext.gettext

import xml.dom.minidom as dom

import Links
import TextThought
import ImageThought
import DrawingThought
import UndoManager

MODE_EDITING = 0
MODE_IMAGE = 1
MODE_DRAW = 2
# Until all references of MODE_MOVING are removed...
MODE_MOVING = 999

TYPE_TEXT = 0
TYPE_IMAGE = 1
TYPE_DRAWING = 2

# TODO: Need to expand to support popup menus
MENU_EMPTY_SPACE = 0

# UNDO actions
UNDO_MOVE = 0
UNDO_CREATE = 1
UNDO_DELETE = 2
UNDO_DELETE_SINGLE = 3
UNDO_COMBINE_DELETE_NEW = 4
UNDO_DELETE_LINK = 5
UNDO_STRENGTHEN_LINK = 6
UNDO_CREATE_LINK = 7

# Note: This is (atm) very broken.  It will allow you to create new canvases, but not
# create new thoughts or load existing maps.
# To get it working either fix the TODO list at the bottom of the class, implement the
# necessary features within all the thought types.  If you do, please send a patch ;)
# OR: Change this class to MMapAreaNew and MMapAreaOld to MMapArea

class MMapArea (gtk.DrawingArea):
	'''A MindMapArea Widget.  A blank canvas with a collection of child thoughts.\
	   It is responsible for processing signals and such from the whole area and \
	   passing these on to the correct child.  It also informs things when to draw'''

	__gsignals__ = dict (title_changed		= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_STRING, )),
						 doc_save			= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
						 doc_delete         = (gobject.SIGNAL_RUN_FIRST,
						 					   gobject.TYPE_NONE,
						 					   ()),
						 change_mode        = (gobject.SIGNAL_RUN_LAST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_INT, )),
						 change_buffer      = (gobject.SIGNAL_RUN_LAST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_OBJECT, )),
						 text_selection_changed  = (gobject.SIGNAL_RUN_FIRST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_STRING)),
						 set_focus				 = (gobject.SIGNAL_RUN_FIRST,
						 							gobject.TYPE_NONE,
						 							(gobject.TYPE_PYOBJECT, gobject.TYPE_BOOLEAN)),
						 set_attrs				 = (gobject.SIGNAL_RUN_LAST,
						 							gobject.TYPE_NONE,
						 							(gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)))

	def __init__(self, undo):
		super (MMapArea, self).__init__()

		self.thoughts = []
		self.links = []
		self.selected = []
		self.num_selected = 0
		self.primary = None
		self.editing = None
		self.pango_context = self.create_pango_context()
		self.undo = undo
		self.scale_fac = 1.0
		self.translate = False
		self.translation = [0.0,0.0]
		self.timeout = -1
		self.current_cursor = None

		self.unending_link = None
		self.nthoughts = 0

		impl = dom.getDOMImplementation()
		self.save = impl.createDocument("http://www.donscorgie.blueyonder.co.uk/labns", "MMap", None)
		self.element = self.save.documentElement
		self.im_context = gtk.IMMulticontext ()

		self.mode = MODE_EDITING
		self.old_mode = MODE_EDITING

		self.connect ("expose_event", self.expose)
		self.connect ("button_release_event", self.button_release)
		self.connect ("button_press_event", self.button_down)
		self.connect ("motion_notify_event", self.motion)
		self.connect ("key_press_event", self.key_press)
		self.connect ("key_release_event", self.key_release)
		self.connect ("scroll_event", self.scroll)
		self.commit_handler = None
		self.title_change_handler = None
		self.moving = False
		self.move_origin = None
		self.move_origin_new = None
		self.motion = None
		self.move_action = None
		self.current_root = []
		self.rotation = 0

		self.set_events (gtk.gdk.KEY_PRESS_MASK |
						 gtk.gdk.KEY_RELEASE_MASK |
						 gtk.gdk.BUTTON_PRESS_MASK |
						 gtk.gdk.BUTTON_RELEASE_MASK |
						 gtk.gdk.POINTER_MOTION_MASK |
						 gtk.gdk.SCROLL_MASK
						)

		self.set_flags (gtk.CAN_FOCUS)

	def transform_coords(self, loc_x, loc_y):
		return self.transform.transform_point(loc_x, loc_y)

	def button_down (self, widget, event):
		coords = self.transform_coords (event.get_coords()[0], event.get_coords()[1])

		ret = False
		obj = self.find_object_at (coords)
		if event.button == 2:
			self.original_translation = self.translation
			self.origin_x = event.x
			self.origin_y = event.y
			return
		if obj and obj.want_motion ():
			self.motion = obj
			ret = obj.process_button_down (event, self.mode, coords)
			if event.button == 1 and self.mode == MODE_EDITING:
				self.moving = not (event.state & gtk.gdk.CONTROL_MASK)
				self.move_origin = (coords[0],coords[1])
				self.move_origin_new = self.move_origin
			return ret
		if obj:
			if event.button == 1 and self.mode == MODE_EDITING:
				self.moving = not (event.state & gtk.gdk.CONTROL_MASK)
				self.move_origin = (coords[0],coords[1])
				self.move_origin_new = self.move_origin
			ret = obj.process_button_down (event, self.mode, coords)
		elif event.button == 3:
			ret = self.create_popup_menu (None, event.get_coords (), MENU_EMPTY_SPACE)
		return ret

	def undo_move (self, action, mode):
		self.undo.block ()
		move_thoughts = action.args[1]
		old_coords = action.args[0]
		new_coords = action.args[2]
		move_x = old_coords[0] - new_coords[0]
		move_y = old_coords[1] - new_coords[1]
		if mode == UndoManager.REDO:
			move_x = -move_x
			move_y = -move_y
		self.unselect_all ()
		for t in move_thoughts:
			self.select_thought (t, -1)
			t.move_by (move_x, move_y)
		self.undo.unblock ()
		self.invalidate ()

	def button_release (self, widget, event):
		coords = self.transform_coords (event.get_coords()[0], event.get_coords()[1])

		ret = False
		if self.translate:
			self.translate = False
			return True
		if self.moving and self.move_action:
			self.move_action.add_arg (event.get_coords ())
			self.undo.add_undo (self.move_action)
			self.move_action = None
		self.motion = None
		self.moving = False
		self.move_origin = None
		if self.mode == MODE_EDITING:
			self.set_cursor(gtk.gdk.LEFT_PTR)
		else:
			self.set_cursor(gtk.gdk.CROSSHAIR)
		obj = self.find_object_at (coords)
		if event.button == 2:
			self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.TRANSFORM_CANVAS, \
														self.undo_transform_cb,
														self.scale_fac, self.scale_fac, 
														self.original_translation,
														self.translation))

		if obj:
			ret = obj.process_button_release (event, self.unending_link, self.mode, coords)
		elif self.unending_link or event.button == 1:
			sel = self.selected
			thought = self.create_new_thought (coords)
			if not thought:
				return True
			if not self.primary:
				self.make_primary (thought)
				self.select_thought (thought, None)
			else:
				self.emit ("change_buffer", thought.extended_buffer)
				self.hookup_im_context (thought)
				# Creating links adds an undo action.  Block it here
				self.undo.block ()
				for x in self.current_root:
					self.create_link (x, None, thought)
				for x in self.selected:
					x.unselect ()
				self.selected = [thought]
				thought.select ()
			if self.unending_link:
				self.unending_link.set_child (thought)
				self.links.append (self.unending_link)
				element = self.unending_link.get_save_element ()
				self.element.appendChild (element)
				self.unending_link = None
			self.undo.unblock ()
			act = UndoManager.UndoAction (self, UNDO_CREATE, self.undo_create_cb, thought, sel, \
										  self.mode, self.old_mode, event.get_coords())
			for l in self.links:
				if l.uses (thought):
					act.add_arg (l)
			if self.undo.peak ().undo_type == UNDO_DELETE_SINGLE:
				last_action = self.undo.pop ()
				action = UndoManager.UndoAction (self, UNDO_COMBINE_DELETE_NEW, self.undo_joint_cb, \
												 last_action, act)
				self.undo.add_undo (action)
			else:
				self.undo.add_undo (act)
			self.begin_editing (thought)
		self.invalidate ()
		return ret

	def undo_transform_cb (self, action, mode):
		if mode == UndoManager.UNDO:
			self.scale_fac = action.args[0]
			self.translation = action.args[2]
		else:
			self.scale_fac = action.args[1]
			self.translation = action.args[3]
		self.invalidate ()

	def scroll (self, widget, event):
		scale = self.scale_fac
		if event.direction == gtk.gdk.SCROLL_UP:
			self.scale_fac*=1.2
		elif event.direction == gtk.gdk.SCROLL_DOWN:
			self.scale_fac/=1.2
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.TRANSFORM_CANVAS, \
													self.undo_transform_cb,
													scale, self.scale_fac, self.translation,
													self.translation))
		self.invalidate()

	def undo_joint_cb (self, action, mode):
		delete = action.args[0]
		create = action.args[1]

		if mode == UndoManager.UNDO:
			self.undo_create_cb (create, mode)
			self.undo_deletion (delete, mode)
		else:
			self.undo_deletion (delete, mode)
			self.undo_create_cb (create, mode)
		self.invalidate ()

	def key_press (self, widget, event):
		if not self.im_context.filter_keypress (event):
			if self.editing:
				if not self.editing.process_key_press (event, self.mode):
					return self.global_key_handler (event)
				return True
			if len(self.selected) != 1 or not self.selected[0].process_key_press (event, self.mode):
				return self.global_key_handler (event)
		return True

	def key_release (self, widget, event):
		self.im_context.filter_keypress (event)
		return True

	def motion (self, widget, event):
		coords = self.transform_coords (event.get_coords()[0], event.get_coords()[1])

		if self.motion:
			if self.motion.handle_motion (event, self.mode, coords):
				return True
		obj = self.find_object_at (coords)
		if self.unending_link:
			self.unending_link.set_end (coords)
			self.invalidate ()
			return True
		elif self.moving and not self.editing and not self.unending_link:
			self.set_cursor(gtk.gdk.FLEUR)
			if not self.move_action:
				self.move_action = UndoManager.UndoAction (self, UNDO_MOVE, self.undo_move, self.move_origin,
														   self.selected)
			for t in self.selected:
				t.move_by (coords[0] - self.move_origin_new[0], coords[1] - self.move_origin_new[1])
			self.move_origin_new = (coords[0], coords[1])
			self.invalidate ()
			return True
		elif self.editing and event.state & gtk.gdk.BUTTON1_MASK and not obj:
			# We were too quick with the movement.  We really actually want to
			# create the unending link
			self.create_link (self.editing)
			self.finish_editing ()
		elif event.state & gtk.gdk.BUTTON2_MASK:
			self.translate = True
			self.translation[0] -= (self.origin_x - event.x) / self.scale_fac
			self.translation[1] -= (self.origin_y - event.y) / self.scale_fac
			self.origin_x = event.x
			self.origin_y = event.y
			self.invalidate()
			return True
			
		if obj:
			obj.handle_motion (event, self.mode, coords)
		elif self.mode == MODE_IMAGE or self.mode == MODE_DRAW:
			self.set_cursor(gtk.gdk.CROSSHAIR)
		else:
			self.set_cursor(gtk.gdk.LEFT_PTR)

	def find_object_at (self, coords):
		for x in reversed(self.thoughts):
			if x.includes (coords, self.mode):
				return x
		for x in self.links:
			if x.includes (coords, self.mode):
				return x
		return None

	def realize_cb (self, widget):
		self.disconnect (self.realize_handle)
		if self.mode == MODE_IMAGE or self.mode == MODE_DRAW:
			self.set_cursor (gtk.gdk.CROSSHAIR)
		else:
			self.set_cursor (gtk.gdk.LEFT_PTR)
		return False

	def set_cursor(self, kind):
		new_cursor = CursorFactory().get_cursor(kind)
		if self.current_cursor != new_cursor:
			self.current_cursor = new_cursor
			self.window.set_cursor(self.current_cursor)

	def set_mode (self, mode):
		if mode == self.mode:
			return
		self.old_mode = self.mode
		self.mode = mode
		self.finish_editing ()
		self.hookup_im_context ()

		if self.window:
			if mode == MODE_IMAGE or mode == MODE_DRAW:
				self.set_cursor (gtk.gdk.CROSSHAIR)
			else:
				self.set_cursor (gtk.gdk.LEFT_PTR)
		else:
			self.realize_handle = self.connect ("realize", self.realize_cb)
		self.mode = mode
		if self.window:
			self.invalidate ()

	def title_changed_cb (self, widget, new_title):
		self.emit ("title_changed", new_title)

	def make_primary (self, thought):
		if self.primary:
			print "Warning: Already have a primary root"
			if self.title_change_handler:
				self.primary.disconnect (self.title_change_handler)
		self.title_change_handler = thought.connect ("title_changed", self.title_changed_cb)
		self.emit ("title_changed", thought.text)
		self.primary = thought
		thought.make_primary ()

	def hookup_im_context (self, thought = None):
		if self.commit_handler:
			self.im_context.disconnect (self.commit_handler)
			self.im_context.disconnect (self.delete_handler)
			self.im_context.disconnect (self.preedit_changed_handler)
			self.im_context.disconnect (self.preedit_end_handler)
			self.im_context.disconnect (self.preedit_start_handler)
			self.im_context.disconnect (self.retrieve_handler)
			self.commit_handler = None
		if thought:
			self.commit_handler = self.im_context.connect ("commit", thought.commit_text, self.mode)
			self.delete_handler = self.im_context.connect ("delete-surrounding", thought.delete_surroundings, self.mode)
			self.preedit_changed_handler = self.im_context.connect ("preedit-changed", thought.preedit_changed, self.mode)
			self.preedit_end_handler = self.im_context.connect ("preedit-end", thought.preedit_end, self.mode)
			self.preedit_start_handler = self.im_context.connect ("preedit-start", thought.preedit_start, self.mode)
			self.retrieve_handler = self.im_context.connect ("retrieve-surrounding", thought.retrieve_surroundings, \
															 self.mode)

	def unselect_all (self):
		self.hookup_im_context ()
		for t in self.selected:
			t.unselect ()
		self.selected = []

	def select_link (self, link, modifiers):
		if modifiers and modifiers & gtk.gdk.SHIFT_MASK and len (self.selected) > 1 and self.selected.count (link) > 0:
			self.selected.remove (link)
			link.unselect ()
			return

		if modifiers and (modifiers & gtk.gdk.SHIFT_MASK or modifiers == -1):
			if self.selected.count (link) == 0:
				self.selected.append (link)
		else:
			for x in self.selected:
				x.unselect ()
			self.selected = [link]
		link.select()
		self.emit("change_buffer", None)
		
		
	def select_thought (self, thought, modifiers):
		if modifiers and modifiers & gtk.gdk.SHIFT_MASK and len (self.selected) > 1 and self.selected.count (thought) > 0:
			self.selected.remove (thought)
			thought.unselect ()
			return
		self.hookup_im_context ()
		if self.editing:
			self.finish_editing ()
		self.thoughts.remove (thought)
		self.thoughts.append(thought)

		if modifiers and (modifiers & gtk.gdk.SHIFT_MASK or modifiers == -1):
			if self.selected.count (thought) == 0:
				self.selected.append (thought)
		else:
			for x in self.selected:
				x.unselect ()
			self.selected = [thought]
		self.current_root = []
		for x in self.selected:
			if x.can_be_parent():
				self.current_root.append(x)
		thought.select ()
		if len(self.selected) == 1:
			self.emit ("change_buffer", thought.extended_buffer)
			self.hookup_im_context (thought)
		else:
			self.emit ("change_buffer", None)

	def begin_editing (self, thought):
		if self.editing and thought != self.editing:
			self.finish_editing ()
		do_edit = thought.begin_editing ()
		if do_edit:
			self.editing = thought

	def undo_link_action (self, action, mode):
		self.undo.block ()
		if self.editing:
			self.finish_editing ()
		link = action.args[0]
		if action.undo_type == UNDO_CREATE_LINK:
			if mode == UndoManager.REDO:
				self.element.appendChild (link.element)
				self.links.append (link)
			else:
				self.delete_link (link)
		elif action.undo_type == UNDO_DELETE_LINK:
			if mode == UndoManager.UNDO:
				self.element.appendChild (link.element)
				self.links.append (link)
			else:
				self.delete_link (link)
		elif action.undo_type == UNDO_STRENGTHEN_LINK:
			if mode == UndoManager.UNDO:
				link.set_strength (action.args[1])
			else:
				link.set_strength (action.args[2])

		self.undo.unblock ()
		self.invalidate ()

	def connect_link (self, link):
		link.connect ("select_link", self.select_link)
		link.connect ("update_view", self.update_view)
		link.connect ("popup_requested", self.create_popup_menu)

	def create_link (self, thought, thought_coords = None, child = None, child_coords = None, strength = 2):
		if child:
			for x in self.links:
				if x.connects (thought, child):
					if x.change_strength (thought, child):
						self.delete_link (x)
					return
			link = Links.Link (self.save, parent = thought, child = child, strength = strength)
			self.connect_link (link)
			element = link.get_save_element ()
			self.element.appendChild (element)
			self.links.append (link)
			return link
		else:
			if self.unending_link:
				del self.unending_link
			self.unending_link = Links.Link (self.save, parent = thought, start_coords = thought_coords,
											 end_coords = child_coords, strength = strength)

			
	def set_mouse_cursor_cb (self, thought, cursor_type):
		if not self.moving:
			self.set_cursor (cursor_type)

	def update_links_cb (self, thought):
		for x in self.links:
			if x.uses (thought):
				x.find_ends ()

	def claim_unending_link (self, thought):
		if not self.unending_link:
			return
		if self.unending_link.parent == thought:
			del self.unending_link
			self.unending_link = None
			return
		for x in self.links:
			if x.connects (self.unending_link.parent, thought):
				old_strength = x.strength
				x.change_strength (self.unending_link.parent, thought)
				new_strength = x.strength
				self.undo.add_undo (UndoManager.UndoAction (self, UNDO_STRENGTHEN_LINK, self.undo_link_action, x, \
															old_strength, new_strength))
				del self.unending_link
				self.unending_link = None
				return

		self.undo.add_undo (UndoManager.UndoAction (self, UNDO_CREATE_LINK, self.undo_link_action, self.unending_link))
		self.unending_link.set_child (thought)
		self.links.append (self.unending_link)
		element = self.unending_link.get_save_element ()
		self.element.appendChild (element)
		self.unending_link = None

	def create_popup_menu (self, thought, coords, menu_type):
		# TODO: FIXME
		print "Popup menu requested"
		return

	def finish_editing (self, thought = None):
		if not self.editing or (thought and thought != self.editing):
			return
		self.editing.finish_editing ()
		self.editing = None

	def update_view (self, thought):
		self.invalidate ()

	def invalidate (self):
		'''Helper function to invalidate the entire screen, forcing a redraw'''
		alloc = self.get_allocation ()
		rect = gtk.gdk.Rectangle (0, 0, alloc.width, alloc.height)
		self.window.invalidate_rect (rect, True)

	def expose (self, widget, event):
		'''Expose event.  Calls the draw function'''
		context = self.window.cairo_create ()
		self.draw (event, context)
		return False

	def draw (self, event, context):
		'''Draw the map and all the associated thoughts'''
		context.rectangle (event.area.x, event.area.y,
						   event.area.width, event.area.height)
		context.clip ()
		context.set_source_rgb (1.0,1.0,1.0)
		context.move_to (event.area.x,event.area.y)
		context.paint ()
		context.set_source_rgb (0.0,0.0,0.0)
		alloc = self.get_allocation ()
		context.translate(alloc.width/2., alloc.height/2.)
		context.scale(self.scale_fac, self.scale_fac)
		context.translate(-alloc.width/2., -alloc.height/2.)		
		context.translate(self.translation[0], self.translation[1])
		for l in self.links:
			l.draw (context)
		if self.unending_link:
			self.unending_link.draw (context)
		for t in self.thoughts:
			t.draw (context)
		self.transform = context.get_matrix()
		self.transform.invert()


	def undo_create_cb (self, action, mode):
		self.undo.block ()
		if mode == UndoManager.UNDO:
			if action.args[0] == self.editing:
				self.editing = None
			self.unselect_all ()
			for t in action.args[1]:
				self.select_thought (t, -1)
			self.delete_thought (action.args[0])
			self.emit ("change_mode", action.args[3])
		else:
			self.emit ("change_mode", action.args[2])
			thought = action.args[0]
			self.thoughts.append (thought)
			for t in action.args[1]:
				self.unselect_all ()
				self.select_thought (t, -1)
			self.hookup_im_context (thought)
			self.emit ("change_buffer", thought.extended_buffer)
			self.element.appendChild (thought.element)
			for l in action.args[5:]:
				self.links.append (l)
				self.element.appendChild (l.element)

			self.begin_editing (thought)
		self.emit ("set_focus", None, False)
		self.undo.unblock ()
		self.invalidate ()

	def create_new_thought (self, coords, thought_type = None, loading = False):
		if self.editing:
			self.editing.finish_editing ()
		if thought_type!= None:
			type = thought_type
		else:
			type = self.mode

		if type == TYPE_TEXT:
			thought = TextThought.TextThought (coords, self.pango_context, self.nthoughts, self.save, self.undo, loading)
		elif type == TYPE_IMAGE:
			thought = ImageThought.ImageThought (coords, self.pango_context, self.nthoughts, self.save, self.undo, loading)
		elif type == TYPE_DRAWING:
			thought = DrawingThought.DrawingThought (coords, self.pango_context, self.nthoughts, self.save, self.undo,	\
													 loading)
		if not thought.okay ():
			return None


		if type == TYPE_IMAGE:
			self.emit ("change_mode", self.old_mode)
		self.nthoughts += 1
		element = thought.element
		self.element.appendChild (thought.element)
		thought.connect ("select_thought", self.select_thought)
		thought.connect ("begin_editing", self.begin_editing)
		thought.connect ("popup_requested", self.create_popup_menu)
		thought.connect ("create_link", self.create_link)
		thought.connect ("claim_unending_link", self.claim_unending_link)
		thought.connect ("update_view", self.update_view)
		thought.connect ("finish_editing", self.finish_editing)
		thought.connect ("delete_thought", self.delete_thought)
		thought.connect ("text_selection_changed", self.text_selection_cb)
		thought.connect ("change_mouse_cursor", self.set_mouse_cursor_cb)
		thought.connect ("update_links", self.update_links_cb)
		thought.connect ("grab_focus", self.regain_focus_cb)
		thought.connect ("update-attrs", self.update_attr_cb)
		self.thoughts.append (thought)
		return thought

	def regain_focus_cb (self, thought, ext):
		self.emit ("set_focus", None, ext)

	def update_attr_cb (self, widget, bold, italics, underline):
		self.emit ("set_attrs", bold, italics, underline)

	def delete_thought (self, thought):
		action = UndoManager.UndoAction (self, UNDO_DELETE_SINGLE, self.undo_deletion, [thought])
		self.element.removeChild (thought.element)
		self.thoughts.remove (thought)
		try:
			self.selected.remove (thought)
		except:
			pass
		if self.editing == thought:
			self.hookup_im_context ()
			self.editing = None
		if self.primary == thought:
			thought.disconnect (self.title_change_handler)
			self.title_change_handler = None
			self.primary = None
			if self.thoughts:
				self.make_primary (self.thoughts[0])
		rem_links = []
		for l in self.links:
			if l.uses (thought):
				action.add_arg (l)
				rem_links.append (l)
		for l in rem_links:
			self.delete_link (l)
		self.undo.add_undo (action)
		return True

	def undo_deletion (self, action, mode):
		self.undo.block ()
		if mode == UndoManager.UNDO:
			self.unselect_all ()
			for t in action.args[0]:
				self.thoughts.append (t)
				self.select_thought (t, -1)
				self.element.appendChild (t.element)
			for l in action.args[1:]:
				self.links.append (l)
				self.element.appendChild (l.element)
			if action.undo_type == UNDO_DELETE_SINGLE:
				self.begin_editing (action.args[0][0])
				self.emit ("change_buffer", action.args[0][0].extended_buffer)
				if not self.primary:
					self.make_primary (action.args[0][0])
			else:
				self.emit ("change_buffer", None)
		else:
			for t in action.args[0]:
				self.delete_thought (t)
			for l in action.args[1:]:
				self.delete_link (l)
		self.emit ("set_focus", None, False)
		self.undo.unblock ()
		self.invalidate ()


	def delete_selected_thoughts (self):
		if len(self.selected) == 0:
			return
		action = UndoManager.UndoAction (self, UNDO_DELETE, self.undo_deletion, copy.copy(self.selected))
		# delete_thought as a callback adds it's own undo action.  Block that here
		self.undo.block ()
		tmp = self.selected
		t = tmp.pop()
		while t:
			for l in self.links:
				if l.uses (t):
					action.add_arg (l)
			self.delete_thought (t)
			if len (tmp) == 0:
				t = None
			else:
				t = tmp.pop()
		self.undo.unblock ()
		self.undo.add_undo (action)
		self.invalidate ()

	def delete_link (self, link):
		self.element.removeChild (link.element)
		#link.element.unlink ()
		self.links.remove (link)

	def popup_menu_key (self, event):
		print "Popup Menu Key"

	def global_key_handler (self, event):
		if event.keyval == gtk.keysyms.Delete:
			self.delete_selected_thoughts ()
		elif event.keyval == gtk.keysyms.BackSpace:
			self.delete_selected_thoughts ()
		elif event.keyval == gtk.keysyms.Menu:
			self.popup_menu_key (event)
		elif event.keyval == gtk.keysyms.a and event.state & gtk.gdk.CONTROL_MASK:
			self.unselect_all ()
			for t in self.thoughts:
				t.select ()
				self.selected.append (t)
		else:
			return False
		self.invalidate ()
		return True

	def load_thought (self, node, type):
		thought = self.create_new_thought (None, type, loading = True)
		thought.load (node)

	def load_link (self, node):
		link = Links.Link (self.save)
		self.connect_link (link)
		link.load (node)
		self.links.append (link)
		element = link.get_save_element ()
		self.element.appendChild (element)

	def load_thyself (self, top_element, doc):
		for node in top_element.childNodes:
			if node.nodeName == "thought":
				self.load_thought (node, TYPE_TEXT)
			elif node.nodeName == "image_thought":
				self.load_thought (node, TYPE_IMAGE)
			elif node.nodeName == "drawing_thought":
				self.load_thought (node, TYPE_DRAWING)
			elif node.nodeName == "link":
				self.load_link (node)
			else:
				print "Warning: Unknown element type.  Ignoring: "+node.nodeName

		self.finish_loading ()

	def finish_loading (self):
		# Possible TODO: This all assumes we've been given a proper,
		# consistant file.  It should fallback nicely, but...
		# First, find the primary root:
		for t in self.thoughts:
			if t.am_primary:
				self.make_primary (t)
			if t.am_selected:
				self.selected.append (t)
				t.select ()
			if t.editing:
				self.begin_editing (t)
			if t.identity >= self.nthoughts:
				self.nthoughts = t.identity + 1
		if self.selected:
			self.current_root = self.selected
		else:
			self.current_root = [self.primary]
		if len(self.selected) == 1:
			self.emit ("change_buffer", self.selected[0].extended_buffer)
			self.hookup_im_context (self.selected[0])
		else:
			self.emit ("change_buffer", None)
		del_links = []
		for l in self.links:
			if (l.parent_number == -1 and l.child_number == -1) or \
			   (l.parent_number == l.child_number):
				del_links.append (l)
				continue
			parent = child = None
			for t in self.thoughts:
				if t.identity == l.parent_number:
					parent = t
				elif t.identity == l.child_number:
					child = t
				if parent and child:
					break
			l.set_parent_child (parent, child)
			if not l.parent or not l.child:
				del_links.append (l)
		for l in del_links:
			self.delete_link (l)

	def save_thyself (self):
		for t in self.thoughts:
			t.update_save ()
		for l in self.links:
			l.update_save ()
		if len(self.thoughts) > 0:
			self.emit ("doc_save", self.save, self.element)
		else:
			self.emit ("doc_delete")

	def text_selection_cb (self, thought, start, end, text):
		self.emit ("text_selection_changed", start, end, text)

	def copy_clipboard (self, clip):
		if len (self.selected) != 1:
			return
		self.selected[0].copy_text (clip)


	def cut_clipboard (self, clip):
		if len (self.selected) != 1:
			return
		self.selected[0].cut_text (clip)


	def paste_clipboard (self, clip):
		if len (self.selected) != 1:
			return
		self.selected[0].paste_text (clip)

	def export (self, context, width, height, native):
		context.rectangle (0, 0, width, height)
		context.clip ()
		context.set_source_rgb (1.0,1.0,1.0)
		context.move_to (0,0)
		context.paint ()
		context.set_source_rgb (0.0,0.0,0.0)
		if not native:
			move_x = self.move_x
			move_y = self.move_y
		else:
			move_x = 0
			move_y = 0
		for l in self.links:
			l.export (context, move_x, move_y)
		for t in self.thoughts:
			t.export (context, move_x, move_y)

	def get_max_area (self):
		minx = 999
		maxx = -999
		miny = 999
		maxy = -999

		for t in self.thoughts:
			mx,my,mmx,mmy = t.get_max_area ()
			if mx < minx:
				minx = mx
			if my < miny:
				miny = my
			if mmx > maxx:
				maxx = mmx
			if mmy > maxy:
				maxy = mmy
		# Add a 10px border around all
		self.move_x = 10-minx
		self.move_y = 10-miny
		maxx = maxx-minx+20
		maxy = maxy-miny+20
		return (maxx,maxy)

	def get_selection_bounds (self):
		if len (self.selected) == 1:
			return self.selected[0].index, self.selected[0].end_index
		else:
			return None, None

	def thoughts_are_linked (self):
		if len (self.selected) != 2:
			return False
		for l in self.links:
			if l.connects (self.selected[0], self.selected[1]):
				return True
		return False

	def link_menu_cb (self):
		if len (self.selected) != 2:
			return
		lnk = None
		for l in self.links:
			if l.connects (self.selected[0], self.selected[1]):
				lnk = l
				break
		if lnk:
			self.undo.add_undo (UndoManager.UndoAction (self, UNDO_DELETE_LINK, self.undo_link_action, lnk))
			self.delete_link (lnk)
		else:
			lnk = self.create_link (self.selected[0], None, self.selected[1])
			self.undo.add_undo (UndoManager.UndoAction (self, UNDO_CREATE_LINK, self.undo_link_action, lnk))
		self.invalidate ()

	def set_bold (self, active):
		if len(self.selected) != 1:
			return
		self.selected[0].set_bold (active)
		self.invalidate()
		
	def set_italics (self, active):
		if len(self.selected) != 1:
			return
		self.selected[0].set_italics (active)
		self.invalidate()
		
	def set_underline (self, active):
		if len(self.selected) != 1:
			return
		self.selected[0].set_underline (active)
		self.invalidate()
	
class CursorFactory:
	__shared_state = {"cursors": {}}

	def __init__(self):
		self.__dict__ = self.__shared_state

	def get_cursor(self, cur_type):
		if not self.cursors.has_key(cur_type):
			cur = gtk.gdk.Cursor(cur_type)
			self.cursors[cur_type] = cur
		return self.cursors[cur_type]

