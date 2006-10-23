# Browser.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <DonScorgie@Blueyonder.co.uk>
#					 - Andreas Sliwka <andreas.sliwka@gmail.com>
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
import MainWindow
from MapList import MapList
import TrayIcon

import gettext
_ = gettext.gettext


class Browser (gtk.Window):
	COL_ID = 0
	COL_TITLE = 1

 
	def __init__(self, start_hidden, tray_icon):
		super(Browser, self).__init__()
		self.glade=gtk.glade.XML(utils.get_data_file_name('/labyrinth.glade'))
		self.view = self.glade.get_widget ('MainView')
		self.populate_view ()
		self.view.connect ('row-activated', self.open_row_cb)
		self.view.connect ('cursor-changed', self.cursor_change_cb)

		self.open_button = self.glade.get_widget('OpenButton')
		self.delete_button = self.glade.get_widget('DeleteButton')

		self.open_button.connect ('clicked', self.open_clicked)
		self.glade.get_widget('NewButton').connect ('clicked', self.new_clicked)
		self.delete_button.connect ('clicked', self.delete_clicked)
		self.glade.get_widget('QuitButton').connect ('clicked', self.quit_clicked)

		self.open_button.set_sensitive (False)
		self.delete_button.set_sensitive (False)

		self.main_window = self.glade.get_widget ('MapBrowser')
		self.main_window.set_size_request (400, 300)
		try:
			self.main_window.set_icon_name ('labyrinth')
		except:
			self.main_window.set_icon_from_file(utils.get_data_file_name('labyrinth.svg'))
		if tray_icon: 
			self.main_window.connect ('delete_event', self.toggle_main_window, None)
			traymenu = gtk.Menu()
			quit_item = gtk.MenuItem("Quit")
			quit_item.connect("activate",self.quit_clicked)
			traymenu.add(quit_item)
			traymenu.show_all()
			self.traymenu = traymenu
			self.trayicon = TrayIcon.TrayIcon(
							icon_name="labyrinth",
							menu=traymenu,
							activate=self.toggle_main_window)
		else:
			self.main_window.connect('delete_event', self.quit_clicked, None) 
		if start_hidden:
			self.main_window.hide ()
		else:
			self.main_window.show_all ()

	def toggle_main_window(self,*args):
		visible = self.main_window.get_property("visible")
		if visible:
			self.main_window.hide()
		else:
			self.main_window.show()
		return True

	def map_title_cb (self, mobj, new_title, mobj1):
		map = MapList.get_by_window(mobj)
		if not map:
			raise "What a mess, can't find the map"
		map.title=new_title
	
	def get_selected (self):
		raise "this function is deprecated"

	def get_selected_map(self):
		sel = self.view.get_selection ()
		(model, it) = sel.get_selected ()
		if it:
		    (num,) = MapList.tree_view_model.get (it, self.COL_ID)
		    map = MapList.get_by_index(num)
		    return  map 
		else:
		    return None
	
	def cursor_change_cb (self, treeview):
		selected_map = self.get_selected_map ()
		if not selected_map:
			self.open_button.set_sensitive (False)
			self.delete_button.set_sensitive (False)
		else:
			self.open_button.set_sensitive (True)
			self.delete_button.set_sensitive (True)
	
	def open_map (self, map):
		win = MainWindow.LabyrinthWindow (map.filename)
		win.connect ("title-changed", self.map_title_cb)
		win.connect ("window_closed", self.remove_map_cb)
		win.connect ("file_saved", self.file_save_cb)
		map.window = win
		return (MapList.index(map), win)
	
	def open_selected_map(self):
		map = self.get_selected_map()
		if map is None:
			raise "you clicked the 'open' button bud had no map selected"
		if map.window:
			print "Window for map '%s' is already open" % map.title
			# may be the window should be raised?
		else:
			self.open_map (map)
    
	def open_clicked (self, button):
		self.open_selected_map() 
			
	def open_row_cb (self, view, path, col):
		self.open_selected_map ()

	def new_clicked (self, button):
		map = MapList.create_empty_map()
		self.open_map(map)

	def delete_clicked (self, button):
		map = self.get_selected_map ()
		if not map:
			raise "You clicked on delete but had no map selected"
		error_message = ""
		if map.window:
			error_message =  _("The map cannot be deleted right now.  Is it open?")
		elif not map.filename:
			error_message = _("Error! Error! Error! map has no filename")
		if error_message:
			dialog = gtk.MessageDialog (self, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
									_("Cannot delete this map"))
			dialog.format_secondary_text (error_message)
			dialog.run ()
			dialog.hide ()
			del (dialog)
			return
		dialog = gtk.MessageDialog (self, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
									_("Do you really want to delete this Map?"))
		resp = dialog.run ()
		dialog.hide ()
		del (dialog)
		if resp != gtk.RESPONSE_YES:
			return
		MapList.delete (map)
		self.view.emit ('cursor-changed')
	
	def remove_map_cb (self, mobj, a):
		map = MapList.get_by_window(mobj)
		if map:
		    MapList.delete(map)
		    self.view.emit ('cursor-changed')
		    return
		raise "Cant remove map of window %s" % mobj

	def file_save_cb (self, mobj, new_fname, mobj1):
		map = MapList.get_by_window(mobj)
		map.window = None
		map.filename = new_fname
		return

	def quit_clicked (self, button, other=None, *data):
		for map in MapList.get_open_windows():
			map.window.close_window_cb (None)
		gtk.main_quit ()

	def populate_view (self):
		column = gtk.TreeViewColumn(_("Map Name"), gtk.CellRendererText(), text=self.COL_TITLE)
		self.view.append_column(column)

		self.view.set_model (MapList.get_TreeViewModel())
	       
