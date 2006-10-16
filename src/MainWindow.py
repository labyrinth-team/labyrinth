#! /usr/bin env python

# MainWindow.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <DonScorgie@Blueyonder.co.uk
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
import sha
import os
import gobject
import gettext
_ = gettext.gettext
import MMapArea
try:
	import defs
except:
	class defs:
		DATA_DIR="./data"
		VERSION="Uninstalled"
import utils

import xml.dom.minidom as dom

num_maps= 1

class LabyrinthWindow (gtk.Window):
	__gsignals__ = dict (title_changed		= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_STRING, gobject.TYPE_OBJECT)),
						 doc_save			= (gobject.SIGNAL_RUN_FIRST,
											   gobject.TYPE_NONE,
											   (gobject.TYPE_STRING, gobject.TYPE_OBJECT)),
						 file_saved         = (gobject.SIGNAL_RUN_FIRST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_STRING, gobject.TYPE_OBJECT)),
						 window_closed      = (gobject.SIGNAL_RUN_FIRST,
						 					   gobject.TYPE_NONE,
						 					   (gobject.TYPE_OBJECT, )))	
	
	def __init__ (self, filename):
		global num_maps
		super(LabyrinthWindow, self).__init__()
		try:
			self.set_icon_name ('labyrinth')
		except:
			self.set_icon_from_file('data/labyrinth.svg')
		self.MainArea = MMapArea.MMapArea ()
		vbox = gtk.VBox ()
		self.add (vbox)
		self.MainArea.set_flags (gtk.CAN_FOCUS)
		self.set_focus_child (self.MainArea)
		self.MainArea.connect ("title_changed", self.title_changed_cb)
		self.MainArea.connect ("doc_save", self.doc_save_cb)
		self.MainArea.connect ("doc_delete", self.doc_del_cb)
		self.MainArea.connect ("change_mode", self.mode_request_cb)
		self.MainArea.connect ("button-press-event", self.main_area_focus_cb)
		self.MainArea.connect ("thought_changed", self.switch_buffer_cb)
		self.extended = gtk.TextView ()
		self.extended.set_wrap_mode (gtk.WRAP_WORD_CHAR)
		self.save_file = filename
		self.maximised = False
		self.view_type = 0
		
		if not filename:
			self.MainArea.set_size_request (500, 500)
			self.map_number = num_maps
			num_maps += 1
			# TODO: This shouldn't be set to a hard-coded number.  Fix.
			self.pane_pos = 500
			self.title_cp = _("Untitled Map %d" % self.map_number)
		else:
			self.title_cp = (_('Somethings broken'))
		self.set_title (self.title_cp)
		self.mode = MMapArea.MODE_EDITING

		self.extended_visible = False
		self.connect ("configure_event", self.configure_cb)
		self.connect ("window-state-event", self.window_state_cb)
		self.connect ("destroy", self.close_window_cb)
		
		panes = gtk.VPaned ()
		panes.connect ("button-release-event", self.pos_changed)
		self.swin = gtk.ScrolledWindow ()
		self.swin.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		
		self.create_ui ()
		if filename:
			self.parse_file (filename)
		(self.width, self.height) = self.get_size ()
		
		self.swin.add (self.extended)
		
		nvbox = gtk.VBox ()
		nvbox.pack_start (self.MainArea)
		nvbox.pack_end (self.ui.get_widget('/AddedTools'), expand=False)
		panes.add1 (nvbox)
		panes.add2 (self.swin)
		panes.set_position (self.pane_pos)

		vbox.pack_start(self.ui.get_widget('/MenuBar'), expand=False)
		vbox.pack_start(self.ui.get_widget('/ToolBar'), expand=False)
		vbox.pack_end (panes)
		
		# For now, set the Bold et. al. insensitive
		self.ui.get_widget('/AddedTools/Bold').set_sensitive (False)
		self.ui.get_widget('/AddedTools/Italics').set_sensitive (False)
		self.ui.get_widget('/AddedTools/Underline').set_sensitive (False)
		
		self.show_all ()
		if not self.extended_visible:
			self.swin.hide ()

	def create_ui (self):
		actions = [
			('FileMenu', None, _('_File')),
			('New', gtk.STOCK_NEW, _('_New'), '<control>N',
			 _('Create a new mind-map'), self.new_window_cb),
			('Close', gtk.STOCK_CLOSE, _('_Close'), '<control>W',
			 _('Close the current window'), self.close_window_cb),
			('Quit', gtk.STOCK_QUIT, _('_Quit'), '<control>Q',
			 _('Close all the windows and exit the application'), self.quit_cb),
			('ModeMenu', None, _('_Mode')),
			('DeleteNodes', gtk.STOCK_DELETE, _('_Delete Selected Thoughts'), None,
			 _('Delete the selected element(s)'), self.delete_cb),
			('HelpMenu', None, _('_Help')),
			('About',gtk.STOCK_ABOUT, _('_About'), None,
			 _('Learn about the application'), self.about_cb)]
		self.radio_actions = [
			('Edit', gtk.STOCK_EDIT, _('_Edit Mode'), '<control>E',
			 _('Turn on edit mode'), MMapArea.MODE_EDITING),
			('Move', gtk.STOCK_JUMP_TO, _('_Move Mode'), '<control>M',
			 _('Turn on move mode'), MMapArea.MODE_MOVING),
			 ('AddImage', gtk.STOCK_ADD, _('_Add Image'), None,
			 _('Add an image to selected thought'), MMapArea.MODE_IMAGE),
			 ('Drawing', gtk.STOCK_COLOR_PICKER, _('_Drawing Mode'), None,
			 _('Make a pretty drawing'), MMapArea.MODE_DRAW)]
		self.toggle_actions = [
			('ViewExtend', None, _('_View Extended'), None,
			 _('View extended infor for thoughts'), self.view_extend_cb),
			('Bold', gtk.STOCK_BOLD, _('Bold'), None,
			None, self.bold_toggled),
			('Italics', gtk.STOCK_ITALIC, _('Italics'), None,
			None, self.italic_toggled),
			('Underline', gtk.STOCK_UNDERLINE, _('Underline'), None,
			None, self.underline_toggled)]


		ag = gtk.ActionGroup ('WindowActions')
		ag.add_actions (actions)
		ag.add_radio_actions (self.radio_actions, value=self.mode)
		ag.add_toggle_actions (self.toggle_actions)
		self.act = ag.get_action ('Edit')
		self.ext_act = ag.get_action ('ViewExtend')
		self.act.connect ("changed", self.mode_change_cb)
				 
		self.ui = gtk.UIManager ()
		self.ui.insert_action_group (ag, 0)
		try:
			self.ui.add_ui_from_file (defs.DATA_DIR+'/labyrinth/labyrinth-ui.xml')
		except:
			self.ui.add_ui_from_file ('data/labyrinth-ui.xml')
		self.add_accel_group (self.ui.get_accel_group ())
		 
	def view_extend_cb (self, arg):
		if self.extended_visible:
			self.swin.hide ()
			self.view_type = 0
		else:
			self.swin.show ()
			self.view_type = 1
		self.extended_visible = not self.extended_visible
	
	def pos_changed (self, panes, arg2):
		self.pane_pos = panes.get_position ()
	
	def bold_toggled (self, arg):
		print "Bold"
		
	def italic_toggled (self, arg):
		print "Italic"
		
	def underline_toggled (self, arg):
		print "Underline"
	
	 
	def new_window_cb (self, arg):
		global_new_window ()
		return
	
	def switch_buffer_cb (self, arg, new_buffer):
		self.extended.set_buffer (new_buffer)
	
	def main_area_focus_cb (self, arg, arg2):
		self.MainArea.grab_focus ()
	
	def quit_cb (self, event):
		gtk.main_quit ()
	
	def about_cb (self, arg):
		about_dialog = gtk.AboutDialog ()
		about_dialog.set_name ("Labyrinth")
		about_dialog.set_version (defs.VERSION)
		about_dialog.set_license (
	"Labyrinth is free software; you can redistribute it and/or modify "
	"it under the terms of the GNU General Public Licence as published by "
	"the Free Software Foundation; either version 2 of the Licence, or"
	"(at your option) any later version."
	"\n\n"
	"Labyrinth is distributed in the hope that it will be useful,"
	"but WITHOUT ANY WARRANTY; without even the implied warranty of"
	"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the"
	"GNU General Public Licence for more details."
	"\n\n"
	"You should have received a copy of the GNU General Public Licence"
	"along with Nautilus; if not, write to the Free Software Foundation, Inc.,"
	"59 Temple Place, Suite 330, Boston, MA  02111-1307  USA")
		about_dialog.set_wrap_license (True)
		about_dialog.set_copyright ("2006 Don Scorgie")
		about_dialog.set_authors (["Don Scorgie <DonScorgie@Blueyonder.co.uk>"])
		about_dialog.set_website ("http://www.donscorgie.pwp.blueyonder.co.uk")
		about_dialog.run ()
		about_dialog.hide ()
		del (about_dialog)
		return
	
	def mode_change_cb (self, base, activated):
		self.MainArea.set_mode (activated.get_current_value ())
		self.mode = activated.get_current_value ()
		return
		
	def mode_request_cb (self, widget, mode):
		self.act.set_current_value (mode)

	def title_changed_cb (self, widget, new_title, obj):
		self.title_cp = ''
		if new_title == '':
			self.title_cp = _('Untitled Map %d' % self.map_number)
		else:
			split = new_title.splitlines ()
			if split:
				final = split.pop ()
				for s in split:
				   self.title_cp += s
				   self.title_cp += ' '
				self.title_cp += final
				if len(self.title_cp) > 27:
					self.title_cp = self.title_cp[0:27]
					self.title_cp += '...'
		self.set_title (self.title_cp)
		self.emit ("title-changed", self.title_cp, self)
	
	def delete_cb (self, event):
		self.MainArea.delete_selected_nodes ()
	
	def close_window_cb (self, event):
		self.hide ()
		self.MainArea.area_close ()
		del (self)
		
	def doc_del_cb (self, w, a):
		self.emit ('window_closed', None)
		
	def doc_save_cb (self, widget, doc, top_element):
		top_element.setAttribute ("title", self.title_cp)
		top_element.setAttribute ("number", str(self.map_number))
		top_element.setAttribute ("mode", str(self.mode))
		top_element.setAttribute ("size", str((self.width,self.height)))
		top_element.setAttribute ("position", str((self.xpos,self.ypos)))
		top_element.setAttribute ("maximised", str(self.maximised))
		top_element.setAttribute ("view_type", str(self.view_type))
		top_element.setAttribute ("pane_position", str(self.pane_pos))
		string = doc.toxml ()
		if not self.save_file:
			sham = sha.new (string)
			save_loc = utils.get_save_dir ()
			self.save_file = save_loc+sham.hexdigest()+".map"
		f = file (self.save_file, 'w')
		f.write (string)
		f.close ()
		self.emit ('file_saved', self.save_file, self)
		
	def parse_file (self, filename):
		f = file (filename, 'r')
		doc = dom.parse (f)
		top_element = doc.documentElement
		self.title_cp = top_element.getAttribute ("title")
		self.map_number = int (top_element.getAttribute ("number"))
		self.mode = int (top_element.getAttribute ("mode"))
		if top_element.hasAttribute ("maximised"):
			maxi = top_element.getAttribute ("maximised")
		else:
			maxi = False
		if maxi == "True":
			self.maximised = True
			self.maximize ()
		if top_element.hasAttribute ("pane_position"):
			self.pane_pos = int (top_element.getAttribute ("pane_position"))
		else:
			self.pane_pos = 500
		if top_element.hasAttribute ("view_type"):
			vt = int (top_element.getAttribute ("view_type"))
		else:
			vt = 0
		if vt == 1:
			self.ext_act.set_active (True)
		tmp = top_element.getAttribute ("size")
		(width, height) = utils.parse_coords (tmp)
		tmp = top_element.getAttribute ("position")
		(x, y) = utils.parse_coords (tmp)
		self.resize (int (width), int (height))
		
		# Don't know why, but metacity seems to move the window 24 pixels
		# further down than requested.  Compensate by removing 24
		# pixels from the stored size
		y -= 24
		self.move (int (x), int (y))
		
		self.set_title (self.title_cp)
		self.MainArea.set_mode (self.mode, False)
		self.MainArea.load_thyself (top_element, doc)
		
	def configure_cb (self, window, event):
		self.xpos = event.x
		self.ypos = event.y
		self.width = event.width
		self.height = event.height
		return False	
		
	def window_state_cb (self, window, event):
		if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
			self.maximised = not self.maximised
		
