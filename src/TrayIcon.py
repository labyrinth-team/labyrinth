# TrayIcon.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Andreas Sliwka <andreas.sliwka@gmail.com>
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


"""
this module implements a tray icon for Labyrinth.

As of now it only brings the application to front if it is clicked.

"""
import sys
import os
import gtk
from utils import *

class TrayIcon(object):
	"""This is possibly the thinnest wrapper class I've written. Ever.

	Its a tray icon that you can parameterize during initialisation with the name or file of an icon, with a menu and a simple callback

	It will create such an Icon, will display the image, call back the callback when left clicked and pop up the menu
	when right clicked.
	"""
	def __init__(self, icon_name="TestTrayIcon", icon_file=None, menu=None, activate=None):
		# thats so incredibly simple!
		if icon_file:
			self.status_icon=gtk.status_icon_new_from_file(icon_file)
		else:
			self.status_icon=gtk.status_icon_new_from_icon_name(icon_name)
		
		# connect the menu and the callback if given
		if menu:
			self.connect_popup_menu(menu)

		if activate:
			self.connect_activate(activate)
	
	def connect_activate(self, method):
		def activate_callback(status_icon, *data):
			method()
		self.status_icon.connect("activate", activate_callback)

	def connect_popup_menu(self,  menu):
		def popup_menu_callback(status_icon, button, activate_time, *data):
			menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, status_icon)
		self.status_icon.connect("popup-menu", popup_menu_callback)

if __name__ == "__main__":
   menu = gtk.Menu()
   quit_item = gtk.MenuItem("Quit")
   quit_item.connect("activate", gtk.main_quit)
   menu.add(quit_item)
   menu.show_all()
   yell_at_them = lambda : sys.stdout.write("you hit %s...\n" % trayicon)
   trayicon = TrayIcon(icon_name="labyrinth", menu=menu, activate=yell_at_them)
   gtk.main()
