# UndoManager.py
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

# Different modes of operation - redo, undo
UNDO = 0
REDO = 1

# Some general actions we should always expect.
# Some require special handling within ourselves
# (taking care of letter insertion / word insertion)

INSERT_LETTER = 100
INSERT_WORD = 101
DELETE_LETTER = 102
DELETE_WORD = 103
TRANSFORM_CANVAS = 104

class UndoAction:
    def __init__(self, owner, undo_type, callback, *args):
        self.owner = owner
        self.undo_type = undo_type
        self.callback = callback
        self.text = ""
        if undo_type == INSERT_LETTER or undo_type == INSERT_WORD or undo_type == DELETE_LETTER or \
           undo_type == DELETE_WORD:
            for z in args:
                if isinstance(z, basestring):
                    self.text = z
                    break
        self.args = args
    def add_arg (self, *args):
        for t in args:
            self.args += (t,)

class UndoManager:
    ''' A basic manager for undoing and redoing actions.\
            Doesn't do anything itself, instead it marshals \
            all the minion classes to do its bidding.  Any class \
            can add items to its lists and they're corresponding \
            methods will be called if and when needed.  The \
            manager doesn't care what you give it, so long as
            it has a method to call and an owner'''

    def __init__(self, top_owner, undo_widget = None, redo_widget = None):
        self.undo = undo_widget
        self.redo = redo_widget

        self.blocked = False

        self.undo_list = []
        self.redo_list = []

        if self.undo:
            self.undo.connect('activate', self.undo_action)
        if self.redo:
            self.redo.connect('activate', self.redo_action)
        self.owner = top_owner
        self.update_sensitive ()

    def block (self):
        ''' Used as generally, when an undo is performed a \
        signal will be emitted that causes an undo action \
        to be added.  Use this to block tht from happening \
        To add actions again, call unblock'''
        self.blocked = True

    def unblock (self):
        self.blocked = False

    def set_widgets (self, undo, redo):
        self.undo = undo
        self.redo = redo
        self.undo.connect('activate', self.undo_action)
        self.redo.connect('activate', self.redo_action)
        self.update_sensitive ()

    def update_sensitive (self):
        if not self.undo or not self.redo:
            return
        self.undo.set_sensitive(len(self.undo_list) > 0)
        self.redo.set_sensitive(len(self.redo_list) > 0)

    def undo_action (self, arg):
        result = self.undo_list.pop()
        self.redo_list.append (result)
        self.update_sensitive ()
        result.callback (result, mode=UNDO)

    def redo_action (self, arg):
        result = self.redo_list.pop()
        self.undo_list.append (result)
        self.update_sensitive ()
        result.callback (result, mode=REDO)

    def combine_insertions (self, action):
        final_text = action.text
        start_iter = action.args[0]
        length = action.args[2]
        owner = action.owner
        cb = action.callback
        old_attrs = action.args[3]
        new_attrs = action.args[4]
        if len (self.undo_list) > 0:
            back = self.undo_list.pop ()
        else:
            self.undo_list.append (action)
            return
        add_back = True
        while back and back.owner == owner \
              and (back.undo_type == INSERT_LETTER or back.undo_type == INSERT_WORD):
            if back.text.rfind(' ') != -1:
                break
            old_attrs = back.args[3]
            if back.args[0] <= start_iter:
                start_iter = back.args[0]
                final_text = back.text+final_text
            else:
                final_text += back.text
            length += back.args[2]
            if len (self.undo_list) == 0:
                add_back = False
                break
            back = self.undo_list.pop ()
        if add_back:
            self.undo_list.append (back)
        combi = UndoAction (owner, INSERT_WORD, cb, start_iter, final_text, length, old_attrs, new_attrs)
        self.undo_list.append (combi)

    def combine_deletions (self, action):
        bytes = True
        byte_collection = action.args[3]
        final_text = action.text
        start_iter = action.args[0]
        length = action.args[2]
        owner = action.owner
        cb = action.callback
        old_attrs = action.args[4]
        new_attrs = action.args[5]
        if len (self.undo_list) > 0:
            back = self.undo_list.pop ()
        else:
            self.undo_list.append (action)
            return
        add_back = True
        while back and back.owner == owner \
                  and (back.undo_type == DELETE_LETTER or back.undo_type == DELETE_WORD):
            if back.text.rfind(' ') != -1:
                break
            old_attrs = back.args[4]
            if back.args[0] <= start_iter:
                start_iter = back.args[0]
                final_text = back.text+final_text
                if bytes:
                    byte_collection = back.args[3] + byte_collection
            else:
                final_text += back.text
                if bytes:
                    byte_collection += back.args[3]
            length += back.args[2]
            if len (self.undo_list) == 0:
                add_back = False
                break
            back = self.undo_list.pop ()
        if add_back:
            self.undo_list.append (back)
        if bytes:
            combi = UndoAction (owner, DELETE_WORD, cb, start_iter, final_text, length, byte_collection, old_attrs, new_attrs)
        else:
            combi = UndoAction (owner, DELETE_WORD, cb, start_iter, final_text, length, -1, old_attrs, new_attrs)
        self.undo_list.append (combi)

    def combine_transforms (self, action):
        if len (self.undo_list) > 0:
            back = self.undo_list.pop ()
        else:
            self.undo_list.append (action)
            return
        add_back = True
        final_zoom = action.args[1]
        final_trans = action.args[3]
        orig_zoom = action.args[0]
        orig_trans = action.args[2]
        owner = action.owner
        cb = action.callback
        while back and back.owner == owner and \
                  back.undo_type == TRANSFORM_CANVAS:
            orig_zoom = back.args[0]
            orig_trans = back.args[2]
            if len (self.undo_list) == 0:
                add_back = False
                break
            back = self.undo_list.pop ()
        if add_back:
            self.undo_list.append (back)
        self.undo_list.append (UndoAction (owner, TRANSFORM_CANVAS, cb, orig_zoom,
                                                                           final_zoom, orig_trans, final_trans))

    def peak (self):
        if len (self.undo_list) > 0:
            return self.undo_list[-1]
        else:
            return UndoAction (None, None, None)

    def pop (self):
        if len (self.undo_list) > 0:
            return self.undo_list.pop ()
        else:
            return None

    def exists_undo_action (self):
        return len(self.undo_list) > 0

    def exists_redo_action (self):
        return len(self.redo_list) > 0

    def add_undo (self, action):
        if self.blocked:
            return
        if not isinstance(action, UndoAction):
            print("Error: Not a valid undo action.  Ignoring.")
            return
        del self.redo_list[:]
        if action.undo_type == INSERT_LETTER:
            self.combine_insertions (action)
        elif action.undo_type == DELETE_LETTER:
            self.combine_deletions (action)
        elif action.undo_type == TRANSFORM_CANVAS:
            self.combine_transforms (action)
        else:
            self.undo_list.append (action)
        self.update_sensitive ()
