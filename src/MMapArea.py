#! /usr/bin/env python
# MMapArea.py
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

import time
import gtk
import pango
import gobject

import xml.dom.minidom as dom

import Links
import TextThought
import ImageThought

#Temporary
import BaseThought

MODE_EDITING = 0
MODE_MOVING = 1
MODE_IMAGE = 2

class MMapArea (gtk.DrawingArea):
	'''A MindMapArea Widget.  A blank canvas with a collection of child thoughts.\
	   It is responsible for processing signals and such from the whole area and \
	   passing these on to the correct child.  It also informs things when to draw'''
	   
	__gsignals__ = dict (single_click_event = (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_PYOBJECT, gobject.TYPE_INT, gobject.TYPE_INT)),
						 double_click_event = (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_PYOBJECT, gobject.TYPE_INT, gobject.TYPE_INT)),
						 title_changed		= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
						 doc_save			= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
						 doc_delete         = (gobject.SIGNAL_RUN_FIRST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_PYOBJECT, )))

	def __init__(self):
		super (MMapArea, self).__init__()

		self.thoughts = []
		self.links = []
		self.selected_thoughts = []
		self.num_selected = 0
		self.primary_thought = None
		self.current_root = None
		self.connect ("expose_event", self.expose)
		self.connect ("button_release_event", self.button_release)
		self.connect ("button_press_event", self.button_down)
		self.connect ("motion_notify_event", self.motion)
		self.connect ("key_press_event", self.key_press)
		self.connect ("single_click_event", self.single_click)
		self.connect ("double_click_event", self.double_click)
		
		self.set_events (gtk.gdk.KEY_PRESS_MASK |
						 gtk.gdk.BUTTON_PRESS_MASK |
						 gtk.gdk.BUTTON_RELEASE_MASK |
						 gtk.gdk.POINTER_MOTION_MASK
						)
		self.set_flags (gtk.CAN_FOCUS)
		self.pango_context = self.create_pango_context()
		self.mode = MODE_EDITING
		self.watching_movement = False
		self.release_time = None

		self.unended_link = None
		self.nthoughts = 0
		self.b_down = False
		
		impl = dom.getDOMImplementation()
		self.save = impl.createDocument("http://www.donscorgie.blueyonder.co.uk/labns", "MMap", None)
		self.element = self.save.documentElement
		
		self.time_elapsed = 0.0
	
# Signal Handlers for the Map Class
	
	def button_down (self, widget, event):
		self.b_down = True
		for s in self.selected_thoughts:
			self.finish_editing (s)
			
		thought = self.find_thought_at (event.get_coords ())
		
		if thought:
			self.make_current_root (thought)
			self.select_thought (thought)
			self.watching_movement = True
		self.invalidate ()
		return False
		
	def button_release (self, widget, event):	
		self.b_down = False
		self.watching_movement = False
		if len (self.selected_thoughts) > 0:
			self.selected_thoughts[0].finish_motion ()
			self.update_links (self.selected_thoughts[0])
		
		self.prev_release_time = self.release_time
		self.release_time = event.get_time ()
		
		if self.prev_release_time and (self.release_time - self.prev_release_time) < 700:
			self.release_time = None
			self.emit ("double_click_event", event.get_coords (), event.state, event.button)
		else:
			self.emit ("single_click_event", event.get_coords (), event.state, event.button)
		self.invalidate ()
		return False
		
	def motion (self, widget, event):
		if not self.watching_movement:
			return False

		if self.mode == MODE_EDITING:
			self.handle_movement (event.get_coords ())
			self.invalidate ()
			return False

		for s in self.selected_thoughts:
			s.handle_movement (event.get_coords ())
			self.update_links (s)
		
		self.invalidate ()	
		return False
		
	def key_press (self, widget, event):
		if self.mode == MODE_EDITING:
			if self.num_selected > 1 or self.num_selected == 0:
				return False
			self.edit_thought (self.selected_thoughts[0])
			ret = self.selected_thoughts[0].handle_key (event.string, event.keyval)
		else:
			ret = self.handle_key_global (event.keyval)
		self.invalidate ()
		return ret
		
	def expose (self, widget, event):
		'''Expose event.  Calls the draw function'''
		context = self.window.cairo_create ()
		self.draw (event, context)
		return False

	def single_click (self, widget, coords, state, button):
		# For now, ignore any other buttons
		if button != 1:
			return
		thought = self.find_thought_at (coords)
		
		#We may have a dangling link.  Need to destroy it now
		self.unended_link = None

		if thought:
			if self.num_selected == 1 and thought != self.selected_thoughts[0]:
				self.link_thoughts (self.selected_thoughts[0], thought)
			elif self.num_selected == 1:
				self.make_current_root (thought)
		else:
			if self.mode == MODE_EDITING:
				self.create_new_thought (coords)
			elif self.mode == MODE_IMAGE:
				self.create_image (coords)
			else:
				self.unselect_all ()
					
		self.invalidate ()
		return

	def double_click (self, widget, coords, state, button):
		if button != 1:
			return

		thought = self.find_thought_at (coords)
		
		if self.mode == MODE_EDITING:
			if thought:
				self.edit_thought (thought)
			else:
				self.create_new_thought (coords)
		
		self.invalidate ()
		return

	def title_changed_cb (self, widget, new_title, obj):
		self.emit ("title_changed", new_title, obj)		   

# Other functions

	def draw (self, event, context):
		'''Draw the map and all the associated thoughts'''
		context.rectangle (event.area.x, event.area.y,
						   event.area.width, event.area.height)
		context.clip ()
		context.set_source_rgb (1.0,1.0,1.0)
		context.move_to (0,0)
		context.paint ()
		context.set_source_rgb (0.0,0.0,0.0)
		for l in self.links:
			l.draw (context)
		if self.unended_link:
			self.unended_link.draw (context)
		for t in self.thoughts:
			t.draw (context)
	
	def invalidate (self):
		'''Helper function to invalidate the entire screen, forcing a redraw'''
		ntime = time.time ()
		if ntime - self.time_elapsed > 0.025:
			alloc = self.get_allocation ()
			rect = gtk.gdk.Rectangle (0, 0, alloc.width, alloc.height)
			self.window.invalidate_rect (rect, True)
			self.time_elapsed = ntime
	
	def find_thought_at (self, coords):
		'''Checks the given coords and sees if there are any thoughts there'''
		if self.mode == MODE_EDITING and self.b_down:
			allow_resize = True
		else:
			allow_resize = False
		for thought in self.thoughts:
			if thought.includes (coords, allow_resize):
				return thought
		return None

	def create_new_thought (self, coords):
		elem = self.save.createElement ("thought")
		text_element = self.save.createTextNode ("GOOBAH")
		elem.appendChild (text_element)
		self.element.appendChild (elem)
		thought = TextThought.TextThought (coords, self.pango_context, self.nthoughts, elem, text_element)
		self.nthoughts += 1
		if self.current_root:
			self.link_thoughts (self.current_root, thought)
		else:
			self.make_current_root (thought)
			
		if not self.primary_thought:
			self.make_primary_root (thought)
		
		self.edit_thought (thought)
		self.thoughts.append (thought)
		self.invalidate ()
		

	def load_thought (self, node):
		elem = self.save.createElement ("thought")
		text_element = self.save.createTextNode ("")
		elem.appendChild (text_element)
		self.element.appendChild (elem)
		thought = TextThought.TextThought (element = elem, text_element = text_element, pango=self.pango_context, load=node)
		self.thoughts.append (thought)
		self.nthoughts += 1
		
	def load_link (self, node):
		link_elem = self.save.createElement ("link")
		self.element.appendChild (link_elem)
		link = Links.Link (element = link_elem, load=node)
		self.links.append (link)
	
	def finish_loading (self):
		# First, find the primary root:
		for t in self.thoughts:
			if t.am_primary:
				t.connect ("title_changed", self.title_changed_cb)
				self.primary_thought = t
			if t.am_root:
				self.current_root = t
			if t.editing:
				self.selected_thoughts = [t]
				self.num_selected = 1
		for l in self.links:
			if l.parent_number == -1 and l.child_number == -1:
				self.delete_link (l)
				continue
			parent = child = None
			for t in self.thoughts:
				if t.identity == l.parent_number:
					parent = t
				elif t.identity == l.child_number:
					child = t
				if parent and child:
					break
			l.set_ends (parent, child)
			
	def handle_movement (self, coords):
		# We can only be called (for now) if a node is selected.  Plan accordingly.
		if self.selected_thoughts[0].want_movement ():
			self.selected_thoughts[0].handle_movement (coords)
			self.update_links (self.selected_thoughts[0])
			self.invalidate ()
			return
		if not self.unended_link:
			self.unended_link = Links.Link (parent = self.selected_thoughts[0], from_coords = coords)
		self.unended_link.set_new_end (coords)
		self.invalidate ()
		return
		
	def handle_key_global (self, keysym):
		# Use a throw-away dictionary for keysym lookup.
		# Idea from: http://simon.incutio.com/archive/2004/05/07/switch
		# Dunno why.  Just trying things out
		try:
			{ gtk.keysyms.Delete: self.delete_selected_nodes,
			  gtk.keysyms.BackSpace: self.delete_selected_nodes}[keysym]()
		except:
			return False
		self.invalidate ()
		return True
	
	def link_thoughts (self, parent, child):
		link = None
		for l in self.links:
			if l.connects (parent, child):
				link = l
				break
		if not link:
			link_elem = self.save.createElement ("link")
			self.element.appendChild (link_elem)
			link = Links.Link (parent, child, link_elem)
			link.update ()
			self.links.append (link)
		else:
			do_del = l.mod_strength (parent, child)
			if do_del:
				self.delete_link (l)
		self.invalidate ()

	def edit_thought (self, thought):
		self.select_thought (thought)
		thought.begin_editing ()
		self.update_links (thought)

	def make_current_root (self, thought):
		if self.current_root:
			self.current_root.finish_active_root ()
		self.current_root = thought
		if thought:
			thought.become_active_root ()
		self.invalidate ()
		
	def unselect_all (self):
		self.num_selected = 0
		self.selected_thoughts = []
		self.invalidate ()

	def delete_selected_nodes (self):
		for t in self.selected_thoughts:
			self.delete_thought (t)

	def make_primary_root (self, thought):
		thought.connect ("title_changed", self.title_changed_cb)
		thought.become_primary_thought ()
		self.primary_thought = thought
		self.current_root = self.primary_thought
		self.current_root.become_active_root ()
		self.emit ("title_changed", thought.text, thought)
		
	def set_mode (self, mode, invalidate = True):
		if self.mode == MODE_IMAGE:
			self.window.set_cursor (gtk.gdk.Cursor (gtk.gdk.LEFT_PTR))
		self.mode = mode
		if mode == MODE_MOVING:
			for s in self.selected_thoughts:
				self.finish_editing (s)
		if mode == MODE_IMAGE and invalidate:
			self.window.set_cursor (gtk.gdk.Cursor (gtk.gdk.CROSSHAIR))
			self.old_mode = self.mode
		if invalidate:
			self.invalidate ()
	
	def save_thyself (self):
		for t in self.thoughts:
			t.update_save ()
		for l in self.links:
			l.update_save ()
		if len(self.thoughts) > 0:
			self.emit ("doc_save", self.save, self.element)
		else:
			self.emit ("doc_delete", None)
		
	def load_thyself (self, top_element, doc):
		for node in top_element.childNodes:
			if node.nodeName == "thought":
				self.load_thought (node)
			elif node.nodeName == "link":
				self.load_link (node)
			elif node.nodeName == "image_thought":
				self.load_image (node)
			else:
				print "Warning: Unknown element type.  Ignoring: "+node.nodeName
				
		self.finish_loading ()
		
	def finish_editing (self, thought):
		do_del = thought.finish_editing ()		
		
		if do_del:
			self.delete_thought (thought)
		else:
			thought.update_save ()
		self.update_links (thought)
		return

	def update_links (self, affected_thought):
		for l in self.links:
			if l.uses (affected_thought):
				l.update ()		

	def delete_link (self, link):
		self.element.removeChild (link.element)
		self.links.remove (link)

	def delete_thought (self, thought):
		self.element.removeChild (thought.element)
		self.thoughts.remove (thought)
		try:
			self.selected_thoughts.remove (thought)
			self.num_selected -= 1
		except:
			pass
		if self.current_root == thought:
			self.current_root = None
		if self.primary_thought == thought:
			self.primary_thought = None
			if self.thoughts:
				self.make_primary_root (self.thoughts[0])
		rem_links = []
		for l in self.links:
			if l.uses (thought):
				self.delete_link (l)
		del thought

	def create_image (self, coords):
		self.window.set_cursor (gtk.gdk.Cursor (gtk.gdk.LEFT_PTR))
		try:
			self.mode = self.old_mode
		except:
			self.mode = MODE_EDITING
		
		# Present a dialog for the user to choose an image here
		dialog = gtk.FileChooserDialog ("Choose image to insert", None, gtk.FILE_CHOOSER_ACTION_OPEN, \
		(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		res = dialog.run ()
		dialog.hide ()
		if res == gtk.RESPONSE_OK:
			fname = dialog.get_filename()
			elem = self.save.createElement ("image_thought")
			self.element.appendChild (elem)
			thought = ImageThought.ImageThought (fname, coords, self.nthoughts, elem)
			if not thought.okay:
				dialog = gtk.MessageDialog (None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
											gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE,
											"Error loading file")
				dialog.format_secondary_text (fname+" could not be read.  Please ensure its a valid image.")
				dialog.run ()
				dialog.hide ()
				return
			thought.connect ("change_cursor", self.cursor_change_cb)
			self.nthoughts+=1
			if self.current_root:
				self.link_thoughts (self.current_root, thought)
			else:
				self.make_current_root (thought)
			
			if not self.primary_thought:
				self.make_primary_root (thought)
		
			self.thoughts.append (thought)
			self.invalidate ()

	def load_image (self, node):
		elem = self.save.createElement ("image_thought")
		self.element.appendChild (elem)
		thought = ImageThought.ImageThought (element = elem, load=node)
		thought.connect ("change_cursor", self.cursor_change_cb)
		self.thoughts.append (thought)
		self.nthoughts += 1	

		pass

	def select_thought (self, thought):
		self.selected_thoughts = [thought]
		self.num_selected = 1

	def area_close (self):
		self.save_thyself ()

		
	def cursor_change_cb (self, thought, cursor_type, a):
		self.window.set_cursor (gtk.gdk.Cursor (cursor_type))	
		return
		
		
		
		
		
		
		
		
		
		
		
