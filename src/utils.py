# functions.py
# This file is part of labyrinth
#
# Copyright (C) 2006 - Don Scorgie
#
# labyrinth is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# labyrinth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

# This file defines various useful functions
# that can be accessed from anywhere :)

import sys
from os.path import *
import os


def get_save_dir ():
	''' Returns the path to the directory to save the maps to '''
	base = os.environ ['HOME']
	dirname = base+"/.gnome2/labyrinth/"
	if not os.access (dirname, os.W_OK):
		os.mkdir (dirname)
	return dirname

def parse_coords (string):
	if string == "None":
		return None
	local = string[1:string.find(',')]
	local_2 = string[string.find (',')+1:string.find(')')]
	coord = (float(local),	float(local_2))
	return coord

