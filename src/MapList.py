# MapList.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Andreas Sliwka <sndreas.sliwka@gmail.com>
#
# Labyrinth is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Labyrinth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#


import os
import utils
import pygtk
import gtk
import xml.dom.minidom as dom
import datetime

class MapList(object):
	COL_ID = 0
	COL_TITLE = 1
	COL_FNAME = 2
	COL_OPEN = 3
	"""Holds the list of maps. has a couple of convinience functions. Sings irish folk

	this is (regarding to MCV) a model class.  """
	class MapCore(object):
		__slots__ = "__dict__ filename title nodes window index".split(" ")
		def __init__(self, index):
			self.__dict__["filename"] = None
			self.__dict__["title"] = None
			self.__dict__["modtime"] = None
			self.__dict__["nodes"] = []
			self.__dict__["window"] = None
			self.__dict__["index"] = index

		def _read_from_file(self, filename):
			doc = dom.parse (filename)
			top_element = doc.documentElement
			self.filename = filename
			self.title = top_element.getAttribute ("title")
			self.window = None

		def __getattr__(self, key):
			dict = self.__dict__
			if key in dict:
				return dict[key]
			else:
				raise ValueError("Class MapCore does not have an attribute named %s" % key)

		def __setattr__(self, key, value):
			dict = self.__dict__
			if key in dict:
				old_value=dict[key]
				dict[key]=value
			else:
				raise ValueError("Class MapCore does not have an attribute named %s" % key)
			if "dont_listen" in dict: return
			listener = "_%s_changed" % key
			class_dict = self.__class__.__dict__
			if listener in class_dict and callable(class_dict[listener]):
				class_dict[listener](self, value, old_value)

		# these listeners get called after the attribute has been changed already

		def _filename_changed(self, value, old_value):
			if not old_value is None:
				del MapList._maps_by_filename[old_value]
			if not value is None:
				MapList._maps_by_filename[value] = self.index

		def _title_changed(self, value, old_value):
			MapList._at_col_set_value(self.index, MapList.COL_TITLE, value)

		def __str__(self):
			return "<MapCore title='%s' window='%s'>" % (self.title, self.window and "yes" or "no")

		def __repr__(self):
			return self.__str__()

	_maps = []
	_maps_by_filename = {}
	tree_view_model = gtk.ListStore(int, str, str, str, 'gboolean')

	def __init__(self):
		raise Exception("This class is a singleton full of classmethods, dont instantiate it.")

	@classmethod
	def load_all_from_dir(cls,dir):
		for f in os.listdir(dir):
			if not os.path.isdir(dir+f):
				cls.new_from_file(dir+f)

	@classmethod
	def new_from_file(cls, filename):
		index = len(cls._maps)
		map = cls.MapCore(index = index)
		cls._maps.append(map)
		map.modtime = datetime.datetime.fromtimestamp(os.stat(filename)[8]).strftime("%x %X")
		cls.tree_view_model.append([map.index, map.title, map.modtime, map.filename, False])
		map._read_from_file(filename)
		return map

	@classmethod
	def create_empty_map(cls):
		index = cls.next_col_id ()
		map = cls.MapCore(index = index)
		map.modtime = datetime.datetime.now().strftime("%x %X")
		cls._maps.append(map)
		cls.tree_view_model.append([map.index, map.title, map.modtime, map.filename, False])
		return map

	@classmethod
	def __str__(cls):
		return "<MapList>\n\t%s\n</MapList>" % "\n\t".join([ map.__str__() for map in cls._maps])

	@classmethod
	def delete(cls, map):
		index = cls._maps.index(map)
		del cls._maps[ index ]
		if map.filename:
			del cls._maps_by_filename[map.filename]
			os.unlink(map.filename)
		iter = cls.get_iter_by_col_id(map.index)
		if iter:
			cls.tree_view_model.remove(iter)

	@classmethod
	def index(cls, map):
		cls._maps.index(map)

	# these functions return None or a single MapCore
	@classmethod
	def get_by_index(cls, index):
		for map in cls._maps:
			if map.index == index:
				return map
		return None

	@classmethod
	def __getitem__(cls, index):
		return cls._maps[index]

	@classmethod
	def get_by_filename(cls, name):
		return cls._maps[cls._maps_by_filename[name]]

	@classmethod
	def get_by_window(cls, window):
		for map in cls._maps:
			if map.window == window:
				return map
		return None

	#These functions return a (possibly empty) list of MapCores
	@classmethod
	def get_open_windows(cls):
		return [map for map in cls._maps if map.window is not None]

	# other functions
	@classmethod
	def count(cls):
		return len(cls._maps)

	# these functions wrap the gtk.ListStore that is used as View
	@classmethod
	def get_TreeViewModel(cls):
		return cls.tree_view_model

	@classmethod
	def _at_col_set_value(cls, col_id, col, value):
		iter = cls.get_iter_by_col_id (col_id)
		if iter:
			cls.tree_view_model.set_value(iter, col, value)

	@classmethod
	def get_iter_by_col_id(cls, col_id):
		found = False
		iter = cls.tree_view_model.get_iter_first ()
		while iter:
			(num,) = cls.tree_view_model.get (iter, MapList.COL_ID)
			if col_id == num:
				found = True
				break
			iter = cls.tree_view_model.iter_next (iter)

		if not found:
			iter = None

		return iter

	@classmethod
	def next_col_id(cls):
		next_col_id = -1
		iter = cls.tree_view_model.get_iter_first ()
		while iter:
			(num,) = cls.tree_view_model.get (iter, MapList.COL_ID)
			if next_col_id < num:
				next_col_id = num
			iter = cls.tree_view_model.iter_next (iter)

		return next_col_id + 1

MapList.load_all_from_dir(utils.get_save_dir ())
