# TextBufferMarkup.py
# This file is part of labyrinth
#
# Copyright (C) 2007 - Don Scorgie <Don@Scorgie.org>
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
# along with labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import gtk
import gobject
import UndoManager
import pango

ADD_ATTR = 42
REMOVE_ATTR = 43

class ExtendedBuffer(gtk.TextBuffer):    
	__gsignals__ = dict (set_focus		= (gobject.SIGNAL_RUN_FIRST,
										   gobject.TYPE_NONE,
										   ()),
						 set_attrs      = (gobject.SIGNAL_RUN_LAST,
						 				   gobject.TYPE_NONE,
						 				   (gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, pango.FontDescription)))

	def __init__(self, undo_manager, save, save_doc):
		super (gtk.TextBuffer, self).__init__()
		self.undo = undo_manager
		self.connect('insert-text', self.insert_text_cb)
		self.connect_after('insert-text', self.apply_attrs_cb)
		self.connect('delete-range', self.delete_range_cb)
		self.text_elem = save_doc.createTextNode ("Extended")
		self.save = save_doc
		self.element = save
		self.element.appendChild(self.text_elem)
		self.bold_tag = self.create_tag("bold", weight=pango.WEIGHT_BOLD)
		self.italics_tag = self.create_tag("italics", style=pango.STYLE_ITALIC)
		self.underline_tag = self.create_tag("underline", underline=pango.UNDERLINE_SINGLE)
		self.current_tags = []
		self.requested_tags = []
		self.connect_after('mark-set',self.mark_set_cb)
		self.bold_block = False
		self.italic_block = False
	
	def undo_action (self, action, mode):
		self.undo.block ()
		self.emit ("set_focus")
		if action.undo_type == UndoManager.DELETE_LETTER or action.undo_type == UndoManager.DELETE_WORD:
			real_mode = not mode
		else:
			real_mode = mode
		if real_mode == UndoManager.UNDO:
			self.delete (self.get_iter_at_offset(action.args[0]),
						 self.get_iter_at_offset (action.args[0]+action.args[2]))
		else:
			self.insert (self.get_iter_at_offset(action.args[0]), action.args[1])
		self.undo.unblock ()
		bold = italics = underline = False
		for x in self.current_tags:
			if x == "bold":
				bold = True
			elif x == "italic":
				italics = True
			elif x == "underline":
				underline = True
		self.emit("set_attrs_bla", bold, italics, underline, None)
		
	def delete_range_cb (self, buffer, iter, it1):
		text = self.get_text (iter, it1)
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.DELETE_LETTER, self.undo_action,
													iter.get_offset(), text, len (text), -1, None, None))
		return False
		
	def insert_text_cb (self, buffer, iter, text, length):
		self.undo.add_undo (UndoManager.UndoAction (self, UndoManager.INSERT_LETTER, self.undo_action,
													iter.get_offset(), text, length, None, None))

		return False

	def apply_attrs_cb (self, buffer, iter, text, length):
		prev_iter = iter.copy()
		if not prev_iter.backward_chars(length):
			print "Errored"
		for x in self.current_tags:
			self.apply_tag_by_name(x, prev_iter, iter)
		return False

	def mark_set_cb(self, buffer, iter, mark, *params):
		italics = underline = bold = False
		if iter.has_tag(self.bold_tag):
			bold = True
		elif self.current_tags.count("bold") > 0:
			self.current_tags.remove("bold")
		if iter.has_tag(self.italics_tag):
			italics = True
		elif self.current_tags.count("italics") > 0:
			self.current_tags.remove("italics")
		if iter.has_tag(self.underline_tag):
			underline = True
		elif self.current_tags.count("underline") > 0:
			self.current_tags.remove("underline")
		for x in self.requested_tags:
			if x == "bold":
				bold = True
			if x == "italics":
				italics = True
			if x == "underline":
				underline = True
			if self.current_tags.count(x) == 0:
				self.current_tags.append(x)
		
		self.emit("set_attrs", bold, italics, underline, None)
		return False
		
	def update_save (self):
		next = self.element.firstChild
		while next:
			m = next.nextSibling
			if next.nodeName == "attribute":
				self.element.removeChild (next)
				next.unlink ()
			next = m
			
		self.text_elem.replaceWholeText (self.get_text())
		mark = self.get_insert()
		it = self.get_iter_at_mark(mark)
		self.element.setAttribute("mark", str(it.get_offset())) 
		iter = self.get_start_iter()
		cur = 0
		tags = {}
		doc = self.element.ownerDocument
		tag_table = self.get_tag_table()
		while(1):
			if iter.begins_tag(tag_table.lookup("bold")):
				tags["bold"] = cur
			if iter.ends_tag(tag_table.lookup("bold")):
				elem = doc.createElement ("attribute")
				self.element.appendChild (elem)
				start = tags.pop("bold")
				elem.setAttribute("start", str(start))
				elem.setAttribute("end", str(cur))
				elem.setAttribute("type", "bold")
			if iter.begins_tag(tag_table.lookup("italics")):
				tags["italics"] = cur
			if iter.ends_tag(tag_table.lookup("italics")):
				elem = doc.createElement ("attribute")
				self.element.appendChild (elem)
				start = tags.pop("italics")
				elem.setAttribute("start", str(start))
				elem.setAttribute("end", str(cur))
				elem.setAttribute("type", "italics")
			if iter.begins_tag(tag_table.lookup("underline")):
				tags["underline"] = cur
			if iter.ends_tag(tag_table.lookup("underline")):
				elem = doc.createElement ("attribute")
				self.element.appendChild (elem)
				start = tags.pop("underline")
				elem.setAttribute("start", str(start))
				elem.setAttribute("end", str(cur))
				elem.setAttribute("type", "underline")
			cur+=1
			if not iter.forward_char():
				break
		for x in tags:
			elem = doc.createElement ("attribute")
			self.element.appendChild (elem)
			elem.setAttribute("start", str(tags[x]))
			elem.setAttribute("end", str(-1))
			elem.setAttribute("type", x)

	def load(self, node):
		mark = None
		if node.hasAttribute("mark"):
			mark = int(node.getAttribute("mark"))
		for n in node.childNodes:
			if n.nodeType == n.TEXT_NODE:
				if n.data != "LABYRINTH_AUTOGEN_TEXT_REMOVE":
					self.set_text(n.data)
			elif n.nodeName == "attribute":
				attrType = n.getAttribute("type")
				start = int(n.getAttribute("start"))
				end = int(n.getAttribute("end"))
				start_it = self.get_iter_at_offset(start)
				if end >= 0:
					end_it = self.get_iter_at_offset(end)
				else:
					end_it = self.get_end_iter()

				self.apply_tag_by_name(attrType, start_it, end_it)
			else:
				print "Error: Unknown type: %s.  Ignoring." % n.nodeName
		if mark:
			ins_iter = self.get_iter_at_offset(mark)
			self.move_mark_by_name("insert", ins_iter)
			self.move_mark_by_name("selection_bound", ins_iter)
		
	def get_text (self, start=None, end=None, include_hidden_chars=True):
		if not start: start=self.get_start_iter()
		if not end: end=self.get_end_iter()
		return gtk.TextBuffer.get_text(self,start,end)

	def undo_attr (self, action, mode):
		if mode == UndoManager.UNDO:
			if action.undo_type == ADD_ATTR and len(action.args[1]) > 0:
				self.remove_tag_by_name(action.args[0], action.args[1][0],
										action.args[1][1])
			elif action.undo_type == ADD_ATTR and len(action.args[1]) == 0:			
				self.current_tags.remove(action.args[0])
				self.requested_tags.remove(action.args[0])
			elif action.undo_type == REMOVE_ATTR and len(action.args[1]) > 0:
				self.apply_tag_by_name(action.args[0], action.args[1][0],
									   action.args[1][1])			
			else:
				self.current_tags.append(action.args[0])
				self.requested_tags.append(action.args[0])
		else:
			if action.undo_type == ADD_ATTR and len(action.args[1]) > 0:
				self.apply_tag_by_name(action.args[0], action.args[1][0],
									   action.args[1][1])			
			elif action.undo_type == ADD_ATTR and len(action.args[1]) == 0:	
				self.current_tags.append(action.args[0])
				self.requested_tags.append(action.args[0])
			elif action.undo_type == REMOVE_ATTR and len(action.args[1]) > 0:
				self.remove_tag_by_name(action.args[0], action.args[1][0],
										action.args[1][1])
			else:		
				self.current_tags.remove(action.args[0])
				self.requested_tags.remove(action.args[0])
		bold = italics = underline = False
		for x in self.current_tags:
			if x == "bold":
				bold = True
			elif x == "italics":
				italics = True
			elif x == "underline":
				underline = True
		self.emit("set_attrs", bold, italics, underline)
		
	def	set_bold (self, bold):
		selection = self.get_selection_bounds()
		if bold:
			if len(selection) > 0:
				self.apply_tag_by_name("bold", selection[0], selection[1])
			else:
				self.current_tags.append("bold")
				self.requested_tags.append("bold")
			self.undo.add_undo(UndoManager.UndoAction(self, ADD_ATTR, self.undo_attr,
													  "bold", selection))
		else:
			if len(selection) > 0:
				self.remove_tag_by_name("bold", selection[0], selection[1])	
			else:
				self.current_tags.remove("bold")
				self.requested_tags.remove("bold")
			self.undo.add_undo(UndoManager.UndoAction(self, REMOVE_ATTR, self.undo_attr,
													  "bold", selection))
		
	def	set_italics (self, italics):
		selection = self.get_selection_bounds()
		if italics:
			if len(selection) > 0:
				self.apply_tag_by_name("italics", selection[0], selection[1])
			else:
				self.current_tags.append("italics")
				self.requested_tags.append("italics")
			self.undo.add_undo(UndoManager.UndoAction(self, ADD_ATTR, self.undo_attr,
													  "italics", selection))
		else:
			if len(selection) > 0:
				self.remove_tag_by_name("italics", selection[0], selection[1])	
			else:
				self.current_tags.remove("italics")
				self.requested_tags.remove("italics")
			self.undo.add_undo(UndoManager.UndoAction(self, REMOVE_ATTR, self.undo_attr,
													  "italics", selection))
		
	def	set_underline (self, underline):
		selection = self.get_selection_bounds()
		if underline:
			if len(selection) > 0:
				self.apply_tag_by_name("underline", selection[0], selection[1])
			else:
				self.current_tags.append("underline")
				self.requested_tags.append("underline")
			self.undo.add_undo(UndoManager.UndoAction(self, ADD_ATTR, self.undo_attr,
													  "underline", selection))
		else:
			if len(selection) > 0:
				self.remove_tag_by_name("underline", selection[0], selection[1])	
			else:
				self.current_tags.remove("underline")
				self.requested_tags.remove("underline")
			self.undo.add_undo(UndoManager.UndoAction(self, REMOVE_ATTR, self.undo_attr,
													  "underline", selection))
				
		
