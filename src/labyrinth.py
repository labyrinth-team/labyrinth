#! /usr/bin/env python
# labyrith.py
# This file is part of Labyrith
#
# Copyright (C) 2006 - Don Scorgie <DonScorgie@Blueyonder.co.uk>
#
# Labyrith is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Labyrith is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import pygtk
pygtk.require('2.0')
import gtk
import gettext, locale
import optparse
import sys
import utils
from os.path import *
import os

def _check (path):
	return exists(path) and isdir(path) and isfile(path+"/AUTHORS")

name = join(dirname(__file__), '..')
if _check(name):
		sys.path.insert(0, abspath(name))
		print 'Running uninstalled, modifying PYTHONPATH: [@PYTHONDIR@:$PYTHONPATH]'
else:
		sys.path.insert(0, abspath("@PYTHONDIR@"))
		print "Running installed, using [@PYTHONDIR@:$PYTHONPATH]"

# Hopefully this will work now ;)
import Browser
try:
	import defs
	localedir = abspath(join(defs.DATA_DIR, "locale"))
except:
	localedir = ""
		

gettext.bindtextdomain('labyrinth', localedir)
if hasattr(gettext, 'bind_textdomain_codeset'):
	gettext.bind_textdomain_codeset('labyrinth','UTF-8')
gettext.textdomain('labyrinth')
locale.bindtextdomain('labyrinth', localedir)
if hasattr(locale, 'bind_textdomain_codeset'):
	locale.bind_textdomain_codeset('labyrinth','UTF-8')
locale.textdomain('labyrinth')

gtk.glade.bindtextdomain('labyrinth')
gtk.glade.textdomain('labyrinth')


def main():
	parser = optparse.OptionParser()
	parser.add_option("-m", "--map",
                  action="store", type="string", dest="filename",
                  help="Open a map from a given filename (from internal database)")
	parser.add_option("-o", "--open",
				  action="store", type="string", dest="filepath",
				  help="Open a map from a given filename (including path)")
	(options, args) = parser.parse_args()	
	MapBrowser = Browser.Browser ()
	if options.filename != None:
		MapBrowser.open_map(utils.get_save_dir() + options.filename, -2)
	elif options.filepath != None:
		MapBrowser.open_map(options.filepath, -2)
		
	
	try:
		gtk.main()
	except:
		print "Exception caught while running.  Dying a death."
		sys.exit(1)

if __name__ == '__main__':
		main()
