#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

__revision__ = '$Id: $'

# Copyright (c) 2005 Vasco Nunes
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# You may use and distribute this software under the terms of the
# GNU General Public License, version 2 or later


# for build this on a win32 environment and becames with a standalone distribution
# a base python 2.4 for 2in32 instalation must be present
# along with gtk+ development libraries
# pywin32com extensions, reportlab module, pygtk for win32 and pysqlite-1.1.7.win32-py2.4 (current win32 distro install is using this pysqlite 3 version)

import time
import sys

# ModuleFinder can't handle runtime changes to __path__, but win32com uses them

try:
    import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass

from distutils.core import setup
import glob
import py2exe

opts = {
    "py2exe": {
        "includes": "cairo,pangocairo,pango,atk,gobject,xml.dom,xml.dom.minidom,threading,shutil,pygtk,gtk,sys,gtk.glade",
        "optimize": 2,
                "dist_dir": "dist\\data_files",
    }
}

setup(
    name = "Labyrinth",
    description = "Labyrinth",
    version = "0.3",
    windows = [
        {
            "script": "src\\labyrinth.py",
            "icon_resources": [(1, "Windows\labyrinth.ico")]
        }],
                options = opts,
                data_files=[
                ("images",
                glob.glob("data\\*.png")),
                ("data",
                glob.glob("data\\*.glade")),
                ("data",
                glob.glob("data\\*.xml")),
                ("",
                glob.glob("src\\*.py"))],
)
