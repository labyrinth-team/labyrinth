# prefs.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <Don@Scorgie.org>
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

# Generally available prefs for all sorts of interesting stuff

from gi.repository import Gtk

_dirn = None

def init ():
    global _dirn
    _dirn = Gtk.Widget.get_default_direction()


def get_direction ():
    global _dirn
    return _dirn


init ()
