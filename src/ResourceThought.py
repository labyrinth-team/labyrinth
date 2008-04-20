# ResourceThought.py
# This file is part of Labyrinth
#
# Copyright (C) 2008 - Labyrinth-Dev-Team
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

import gtk
import pango
import utils
import BaseThought, TextThought
import prefs
import UndoManager
import os
import webbrowser

class ResourceThought (TextThought.TextThought):
	def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color):
		super (ResourceThought, self).__init__(coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color, "res_thought")

		self.uri = ""
		if not loading:
			# FIXME: we should handle such things with a singleton
			glade = gtk.glade.XML(utils.get_data_file_name('labyrinth.glade'))
			dialog = glade.get_widget('ResourceChooserDialog')
			dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
				gtk.STOCK_OK, gtk.RESPONSE_OK)
			res = dialog.run()
			dialog.hide()

			if res == gtk.RESPONSE_OK:
				# FIXME: validate input
				self.uri = glade.get_widget('urlEntry').get_text()
				self.add_text(self.uri)
				
		self.all_okay = True

	def process_button_down (self, event, mode, transformed):
		modifiers = gtk.accelerator_get_default_mod_mask ()
		if event.type == gtk.gdk.BUTTON_PRESS and not self.editing:
			self.emit ("select_thought", event.state & modifiers)
		if event.button == 1 and mode == BaseThought.MODE_EDITING and event.type == gtk.gdk._2BUTTON_PRESS:
			webbrowser.open(self.uri)
			
	def update_save (self):
		super(ResourceThought, self).update_save()
		self.element.setAttribute ("uri", self.uri)
		
	def load (self, node):
		super(ResourceThought, self).load(node)
		self.uri = node.getAttribute ("uri")
		
	def draw (self, context):
		if not self.layout:
			self.recalc_edges ()
		if not self.editing:
			# We should draw the entire bounding box around ourselves
			# We should also have our coordinates figured out.	If not, scream!
			if not self.ul or not self.lr:
				print "Warning: Trying to draw unfinished box "+str(self.identity)+". Aborting."
				return
			utils.draw_thought_extended (context, self.ul, self.lr, self.am_selected, self.am_primary, self.background_color, False, True)
		else:
			ux, uy = self.ul
			if prefs.get_direction() == gtk.TEXT_DIR_LTR:
				context.move_to (ux, uy+5)
				context.line_to (ux, uy)
				context.line_to (ux+5, uy)
			else:
				lx = self.lr[0]
				context.move_to (lx, uy+5)
				context.line_to (lx, uy)
				context.line_to (lx-5, uy)
			context.stroke ()

		(textx, texty) = (self.text_location[0], self.text_location[1])
		r, g, b = utils.gtk_to_cairo_color(self.foreground_color)
		context.set_source_rgb (r, g, b)
		context.move_to (textx, texty)
		context.show_layout (self.layout)
		if self.editing:
			if self.preedit:
				(strong, weak) = self.layout.get_cursor_pos (self.index + self.preedit[2])
			else:
				(strong, weak) = self.layout.get_cursor_pos (self.index)
			(startx, starty, curx,cury) = strong
			startx /= pango.SCALE
			starty /= pango.SCALE
			curx /= pango.SCALE
			cury /= pango.SCALE
			context.move_to (textx + startx, texty + starty)
			context.line_to (textx + startx, texty + starty + cury)
			context.stroke ()
		context.set_source_rgb (0,0,0)
		context.stroke ()
