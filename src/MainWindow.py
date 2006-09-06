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

import MMapArea
import defs
import utils

import xml.dom.minidom as dom

#windows = []
num_maps= 1



#def global_new_window (from_filename = None):
#	window = LabyrinthWindow (from_filename)
#	windows.append (window)
#	window.show_all ()

def number_windows ():
	return len(windows)

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
		self.MainArea = MMapArea.MMapArea ()
		vbox = gtk.VBox ()
		self.add (vbox)
		self.MainArea.set_flags (gtk.CAN_FOCUS)
		self.set_focus_child (self.MainArea)
		self.MainArea.connect ("title_changed", self.title_changed_cb)
		self.MainArea.connect ("doc_save", self.doc_save_cb)
		self.MainArea.connect ("doc_delete", self.doc_del_cb)		
		self.save_file = filename
		
		if not filename:
			self.MainArea.set_size_request (500, 500)
			self.map_number = num_maps
			num_maps += 1
			self.title_cp = "Untitled Map %d" % self.map_number			   
		else:
			self.title_cp = "Somethings broken"
		self.set_title (self.title_cp)
		self.mode = MMapArea.MODE_EDITING

		self.connect ("configure_event", self.configure_cb)
		self.connect ("destroy", self.close_window_cb)

		if filename:
			self.parse_file (filename)
		self.create_ui ()
		vbox.pack_start(self.ui.get_widget('/MenuBar'), expand=False)
		vbox.pack_start(self.ui.get_widget('/ToolBar'), expand=False)
		vbox.pack_end (self.MainArea, expand = True)

	def create_ui (self):
		actions = [
			('FileMenu', None, '_File'),
			('New', gtk.STOCK_NEW, '_New', '<control>N',
			 'Create a new mind-map', self.new_window_cb),
			('Close', gtk.STOCK_CLOSE, '_Close', '<control>W',
			 'Close the current window', self.close_window_cb),
			('Quit', gtk.STOCK_QUIT, '_Quit', '<control>Q',
			 'Close all the windows and exit the application', self.quit_cb),
			('ModeMenu', None, '_Mode'),
			('DeleteNodes', gtk.STOCK_DELETE, '_Delete Selected Thoughts', None,
			 'Delete the selected element(s)', self.delete_cb),
			('HelpMenu', None, '_Help'),
			('About',gtk.STOCK_ABOUT, '_About', None,
			 'Learn about the application', self.about_cb)]
		radio_actions = [
			('Edit', None, '_Edit Mode', '<control>E',
			 'Turn on edit mode', MMapArea.MODE_EDITING),
			('Move', None, '_Move Mode', '<control>M',
			 'Turn on move mode', MMapArea.MODE_MOVING)]

		ag = gtk.ActionGroup ('WindowActions')
		ag.add_actions (actions)
		ag.add_radio_actions (radio_actions, value=self.mode)
		act = ag.get_action ('Edit')
		act.connect ("changed", self.mode_change_cb)
				 
		self.ui = gtk.UIManager ()
		self.ui.insert_action_group (ag, 0)
		try:
			self.ui.add_ui_from_file (defs.DATA_DIR+'/labyrinth/labyrinth-ui.xml')
		except:
			print "Cannot find "+defs.DATA_DIR+".  Looking in ./data"
			self.ui.add_ui_from_file ('data/labyrinth-ui.xml')
		self.add_accel_group (self.ui.get_accel_group ())
		 
	 
	def new_window_cb (self, arg):
		global_new_window ()
		return
	
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

	def title_changed_cb (self, widget, new_title, obj):
		self.title_cp = ''
		if new_title == '':
			self.title_cp = 'Untitled Map %d' % self.map_number
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
		#windows.remove (self)
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
		
		
		
