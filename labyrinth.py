#!/usr/bin/python
# labyrith.py
# This file is part of Labyrith
#
# Copyright (C) 2006 - Don Scorgie <Don@Scorgie.org>
# Copyright (C) 2008 - Labyrinth-Dev-Team
#
# Labyrith is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Labyrith is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#

import gettext, locale
import optparse
import sys, os
import os.path as osp

import gi

gi.require_versions({
    'Gtk': '3.0',
    'GConf': '2.0',
    'PangoCairo': '1.0',
    'PangoAttrCast': '1.0',
})

from gi.repository import Gtk

from labyrinth import utils
from labyrinth import Browser
from labyrinth import prefs
try:
    from labyrinth import defs
    localedir = abspath(join(defs.DATA_DIR, "locale"))
except:
    localedir = ""

gettext.bindtextdomain('labyrinth', localedir)
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset('labyrinth','UTF-8')

gettext.textdomain('labyrinth')

if hasattr(locale, 'bindtextdomain'):
    if not os.name == 'nt':
        locale.bindtextdomain('labyrinth', localedir)
        if hasattr(locale, 'bind_textdomain_codeset'):
            locale.bind_textdomain_codeset('labyrinth','UTF-8')
        locale.textdomain('labyrinth')

def main():
    parser = optparse.OptionParser()
    parser.add_option("--use-tray-icon", dest="tray_icon",
            action="store_true", default=False)
    parser.add_option("--no-tray-icon", dest="tray_icon", action="store_false")
    parser.add_option("--hide-main-window", action="store_true", default=False)
    parser.add_option("-m", "--map", action="store", type="string", dest="filename",
            help="Open a map from a given filename (from internal database)")
    parser.add_option("-o", "--open", action="store", type="string",
            dest="filepath", help="Open a map from a given filename (including path)")

    (options, args) = parser.parse_args()
    if not options.tray_icon:
        options.hide_main_window=False

    MapBrowser = Browser.Browser (
            start_hidden = options.hide_main_window,
            tray_icon = options.tray_icon
    )

    if options.filename != None:
        MapBrowser.open_map_filename (utils.get_save_dir() + options.filename)
    elif options.filepath != None:
        MapBrowser.open_map_filename (options.filepath)

    try:
        Gtk.main()
    except:
        print("Exception caught while running.  Dying a death.")
        sys.exit(1)

if __name__ == '__main__':
    main()
