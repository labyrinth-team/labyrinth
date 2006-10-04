# Browser.py
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

import utils
import pygtk
pygtk.require('2.0')
import gtk
import optparse
import sys
from os.path import *
import os
import os
import gtk.glade
import MainWindow, defs
import gettext
_ = gettext.gettext
import xml.dom.minidom as dom

class Browser (gtk.Window):
	COL_ID = 0
	COL_TITLE = 1
	COL_FNAME = 2
	COL_OPEN = 3
	
	
	
	def __init__(self):
		super(Browser, self).__init__()
		self.maps=[]
		self.nmap = 0
		try:
			self.glade = gtk.glade.XML (defs.DATA_DIR+'/labyrinth/labyrinth.glade')
		except:
			print "Cannot find "+defs.DATA_DIR+".  Looking in ./data"
			self.glade = gtk.glade.XML ('data/labyrinth.glade')

		self.view = self.glade.get_widget ('MainView')
		self.populate_view ()
		self.view.connect ('row-activated', self.open_row_cb)

		self.glade.get_widget('OpenButton').connect ('clicked', self.open_clicked)
		self.glade.get_widget('NewButton').connect ('clicked', self.new_clicked)
		self.glade.get_widget('DeleteButton').connect ('clicked', self.delete_clicked)
		self.glade.get_widget('QuitButton').connect ('clicked', self.quit_clicked)

		self.main_window = self.glade.get_widget ('MapBrowser')
		try:
			self.main_window.set_icon_name ('labyrinth')
		except:
			self.main_window.set_icon_from_file('data/labyrinth.svg')
		self.main_window.connect ('destroy', self.quit_clicked, None)
		self.main_window.show_all ()
		self.main_window.set_size_request (400, 300)

	
	def map_title_cb (self, mobj, new_title, mobj1):
		for m in self.maps:
			if m[1] == mobj:
				break
		if not m:
			print "Error: Can't find map"
			sys.exit(4)
		it = self.mapslist.get_iter_root ()
		while it:
			(mnum, ) = self.mapslist.get (it, self.COL_ID)
			if mnum == m[0]:
				self.mapslist.set (it, self.COL_TITLE, new_title)
				return
			it = self.mapslist.iter_next (it)
		print "Error: Unable to set title properly"
		sys.exit (5)	
	
	def get_selected (self):
		sel = self.view.get_selection ()
		(model, it) = sel.get_selected ()
		return it

	def open_map (self, fname = None, num=-1):
		win = MainWindow.LabyrinthWindow (fname)
		if num == -1:
			num = self.nmap
		self.maps.append ((num, win))
		win.connect ("title-changed", self.map_title_cb)
		win.connect ("window_closed", self.remove_map_cb)
		win.connect ("file_saved", self.file_save_cb)
		win.show_all ()
		self.nmap += 1
		return (num, win)
	
	def open_clicked (self, button):
		selected = self.get_selected ()
		if not selected:
			return
		(fname,cur, num) = self.mapslist.get (selected, self.COL_FNAME, self.COL_OPEN, self.COL_ID)
		if not cur:
			self.open_map (fname, num)
			self.mapslist.set (selected, self.COL_OPEN, True)
	
	def new_clicked (self, button):
		(num, win) = self.open_map ()		
		self.mapslist.append ([num, win.title_cp, None, True])
			
	def delete_clicked (self, button):
		it = self.get_selected ()
		if not it:
			return
		dialog = gtk.MessageDialog (self, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
									_("Do you really want to delete this Map?"))
		resp = dialog.run ()
		dialog.hide ()
		del (dialog)
		if resp != gtk.RESPONSE_YES:
			return

		(fname, active) = self.mapslist.get (it, self.COL_FNAME, self.COL_OPEN)
		if active or not fname:
			dialog = gtk.MessageDialog (self, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
									_("Cannot delete this map"))
			dialog.format_secondary_text (_("The map cannot be deleted right now.  Is it open?"))
			dialog.run ()
			dialog.hide ()
			del (dialog)
			return
		else:
			os.unlink (fname)
			self.mapslist.remove (it)
	
	def remove_map_cb (self, mobj, a):
		for m in self.maps:
			if m[1] == mobj:
				break
		if not m:
			print "Error: Can't find map"
			sys.exit(4)
		it = self.mapslist.get_iter_root ()
		while it:
			(mnum, fname) = self.mapslist.get (it, self.COL_ID, self.COL_FNAME)
			if mnum == m[0]:
				self.mapslist.remove (it)
				if fname:
					os.unlink (fname)
				self.maps.remove (m)
				return
			it = self.mapslist.iter_next (it)
		print "Error: Unable to remove properly"
		sys.exit (5)	

	def file_save_cb (self, mobj, new_fname, mobj1):
		for m in self.maps:
			if m[1] == mobj:
				break
		if not m:
			print "Error: Can't find map"
			sys.exit(4)
		it = self.mapslist.get_iter_root ()
		while it:
			(mnum, fname) = self.mapslist.get (it, self.COL_ID, self.COL_FNAME)
			if mnum == m[0]:
				if not fname:
					self.mapslist.set (it, self.COL_FNAME, new_fname, self.COL_OPEN, False)
				else:
					self.mapslist.set (it, self.COL_OPEN, False)
				self.maps.remove (m)
				return
			it = self.mapslist.iter_next (it)
		print "Error: Unable to set save properly"
		sys.exit (5)	

	def quit_clicked (self, button, other=None):
		for m in self.maps:
			m[1].close_window_cb (None)
		gtk.main_quit ()
			
	def open_row_cb (self, view, path, col):
		self.open_clicked (None)
		pass

	def populate_model (self, filename):
		f = file (filename, 'r')
		doc = dom.parse (f)
		top_element = doc.documentElement	
	
		title = top_element.getAttribute ("title")
		
		self.mapslist.append ([self.nmap, title, filename, False])
		self.nmap += 1
			
	def populate_view (self):
		column = gtk.TreeViewColumn("Map Name", gtk.CellRendererText(), text=self.COL_TITLE)
		self.view.append_column(column)

		self.mapslist = gtk.ListStore (int, str, str, 'gboolean')
		self.view.set_model (self.mapslist)
		
		save_loc = utils.get_save_dir ()
		for f in os.listdir(save_loc):
			self.populate_model (save_loc+f)
			
			
			
			
			
