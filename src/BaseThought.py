# BaseThought.py
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

import gobject
import utils

class BaseThought (gobject.GObject):
	''' the basic class to derive other thouhts from'''
	
	def __init__ (self):
		super (BaseThought, self).__init__()
		self.am_primary = False
		self.am_root = False
		self.editing = False
		self.identity = -1
		
	def includes (self, coords):
		print "Warning: includes is not implemented for one thought type"
		return False
		
	def draw (self, context):
		print "Warning: drawing is not implemented for one thought type"
		return
		
	def handle_movement (self, coords):
		print "Warning: handle_movement is not implemented for this node type"
		return
	
	def handle_key (self, string, keysym):
		print "Warning: handle_key is not implemented for this node type"
		return False
		
	def find_connection (self, other):
		print "Warning: Unable to find connection for this node type"
		return (None, None)
		
	def update_save (self):
		print "Warning: Saving is not working for a node type.  This node will not be saved."
		return
		
	def load_data (self, node):
		print "Warning: Loading this type of node isn't allowed just now."
		return
		
	def begin_editing (self):
		print "Warning: Cannot edit this thought type"
		return
	
	def finish_editing (self):
		print "Warning: This node type cannot be edited"
		return
	
	def become_active_root (self):
		print "Warning: This type of node cannot become root"
		return
		
	def finish_active_root (self):
		print "Warning: This type of not isn't currently root"
		return
		
	def become_primary_thought (self):
		print "Warning: Become primary root isn't implemented for this node type"
		return
		
	
		
		
		
		
		
		
		
		
