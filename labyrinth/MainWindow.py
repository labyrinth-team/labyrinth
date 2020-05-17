# MainWindow.py
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

# Standard library
import hashlib
import os
import tarfile
import gettext
_ = gettext.gettext
import xml.dom.minidom as dom

# Gtk stuff
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import PangoCairo
import cairo
if os.name != 'nt':
    from gi.repository import GConf

# Local imports
import MMapArea
import UndoManager
import PeriodicSaveThread
import ImageThought
import BaseThought
import utils
from MapList import MapList

# UNDO varieties for us
UNDO_MODE = 0
UNDO_SHOW_EXTENDED = 1

class LabyrinthWindow (GObject.GObject):
    __gsignals__ = dict (title_changed = (GObject.SignalFlags.RUN_FIRST,
                                          None,
                                          (str, object)),
                         doc_save      = (GObject.SignalFlags.RUN_FIRST,
                                          None,
                                          (str, object)),
                         file_saved    = (GObject.SignalFlags.RUN_FIRST,
                                          None,
                                          (str, object)),
                         window_closed = (GObject.SignalFlags.RUN_FIRST,
                                          None,
                                          (object, )),
                        )

    def __init__ (self, filename, imported=False):
        super(LabyrinthWindow, self).__init__()

        # First, construct the MainArea and connect it all up
        self.undo = UndoManager.UndoManager (self)
        self.undo.block ()
        self.MainArea = MMapArea.MMapArea (self.undo)
        self.MainArea.connect ("title_changed", self.title_changed_cb)
        self.MainArea.connect ("doc_save", self.doc_save_cb)
        self.MainArea.connect ("doc_delete", self.doc_del_cb)
        self.MainArea.connect ("change_mode", self.mode_request_cb)
        self.MainArea.connect ("button-press-event", self.main_area_focus_cb)
        self.MainArea.connect ("change_buffer", self.switch_buffer_cb)
        self.MainArea.connect ("thought_selection_changed", self.thought_selected_cb)
        self.MainArea.connect ("set_focus", self.main_area_focus_cb)
        self.MainArea.connect ("set_attrs", self.attrs_cb)
        if os.name != 'nt':
            self.MainArea.connect ("text_selection_changed", self.selection_changed_cb)
            self.config_client = GConf.Client.get_default()

        glade = Gtk.Builder()
        glade.add_from_file(utils.get_data_file_name('labyrinth.xml'))
        self.main_window = glade.get_object('MapWindow')
        self.main_window.set_focus_child (self.MainArea)
        if os.name != 'nt':
            try:
                self.main_window.set_icon_name ('labyrinth')
            except:
                self.main_window.set_icon_from_file(utils.get_data_file_name('labyrinth.svg'))
        else:
            self.main_window.set_icon_from_file('images\\labyrinth-24.png')

        # insert menu, toolbar and map
        self.create_menu()
        glade.get_object('main_area_insertion').pack_start(self.MainArea, expand=True, fill=True, padding=0)
        vbox = glade.get_object('map_window_vbox')
        menubar = self.ui.get_widget('/MenuBar')
        menubar.show_all()
        vbox.pack_start(menubar, expand=True, fill=True, padding=0)
        vbox.reorder_child(menubar, 0)
        vbox.set_child_packing(menubar, 0, 0, 0, Gtk.PackType.START)

        toolbar = self.ui.get_widget('/ToolBar')
        toolbar.show_all()
        vbox.pack_start(toolbar, expand=True, fill=True, padding=0)
        vbox.reorder_child(toolbar, 1)
        vbox.set_child_packing(toolbar, 0, 0, 0, Gtk.PackType.START)

        # TODO: Bold, Italics etc.
        self.bold_widget = glade.get_object('tool_bold')
        self.bold_widget.connect('toggled', self.bold_toggled)
        self.bold_block = False
        self.bold_state = False
        self.italic_widget = glade.get_object('tool_italic')
        self.italic_widget.connect('toggled', self.italic_toggled)
        self.italic_block = False
        self.italic_state = False
        self.underline_widget = glade.get_object('tool_underline')
        self.underline_widget.connect('toggled', self.underline_toggled)
        self.underline_block = False
        self.underline_state = False

        self.font_widget = glade.get_object('font_button')
        self.font_widget.connect ("font-set", self.font_change_cb)
        self.background_widget = glade.get_object('background_color_button')
        self.background_widget.connect ("color-set", self.background_change_cb)
        self.foreground_widget = glade.get_object('foreground_color_button')
        self.foreground_widget.connect ("color-set", self.foreground_change_cb)

        self.cut = self.ui.get_widget ('/MenuBar/EditMenu/Cut')
        self.copy = self.ui.get_widget ('/MenuBar/EditMenu/Copy')
        self.paste = self.ui.get_widget ('/MenuBar/EditMenu/Paste')
        self.link = self.ui.get_widget ('/MenuBar/EditMenu/LinkThoughts')
        self.delete = self.ui.get_widget ('/MenuBar/EditMenu/DeleteNodes')

        self.ui.get_widget('/MenuBar/EditMenu').connect ('activate', self.edit_activated_cb)
        self.cut.set_sensitive (False)
        self.copy.set_sensitive (False)

        # get toolbars and activate corresponding menu entries
        self.main_toolbar = self.ui.get_widget ('/ToolBar')
        self.format_toolbar = glade.get_object('format_toolbar')
        self.ui.get_widget('/MenuBar/ViewMenu/ShowToolbars/ShowMainToolbar').set_active(True)
        self.ui.get_widget('/MenuBar/ViewMenu/ShowToolbars/ShowFormatToolbar').set_active(True)
        self.ui.get_widget('/MenuBar/ViewMenu/UseBezier').set_active(utils.use_bezier_curves)

        # Add in the extended info view
        self.extended_window = glade.get_object('extended_window')
        self.extended = glade.get_object('extended')
        self.invisible_buffer = Gtk.TextBuffer()

        # Connect all our signals
        self.main_window.connect ("configure_event", self.configure_cb)
        self.main_window.connect ("window-state-event", self.window_state_cb)
        self.main_window.connect ("destroy", self.close_window_cb)

        # Deal with loading the map
        if not filename:
            self.MainArea.set_size_request (400, 400)
            # TODO: This shouldn't be set to a hard-coded number.  Fix.
            self.pane_pos = 500
            self.title_cp = _("Untitled Map")
            self.mode = MMapArea.MODE_EDITING
            self.extended_visible = False
        else:
            self.parse_file (filename)

        up_box = glade.get_object('up_box')
        up_box.connect("button-press-event", self.translate, "Up")
        up_box.connect("button-release-event", self.finish_translate)
        down_box = glade.get_object('down_box')
        down_box.connect("button-press-event", self.translate, "Down")
        down_box.connect("button-release-event", self.finish_translate)
        right_box = glade.get_object('right_box')
        right_box.connect("button-press-event", self.translate, "Right")
        right_box.connect("button-release-event", self.finish_translate)
        left_box = glade.get_object('left_box')
        left_box.connect("button-press-event", self.translate, "Left")
        left_box.connect("button-release-event", self.finish_translate)

        panes = glade.get_object('vpaned1')
        panes.connect ("button-release-event", self.pos_changed)
        panes.set_position (self.pane_pos)

        # Other stuff
        self.width, self.height = self.main_window.get_size ()

        # if we import, we dump the old filename to create a new hashed one
        self.save_file = None
        if not imported:
            self.save_file = filename

        self.maximised = False
        self.view_type = 0
        self.act.set_current_value (self.mode)

        self.undo.unblock ()
        self.start_timer ()

    def show(self):
        self.main_window.show_all()
        self.ext_act.set_active(self.extended_visible)
        if not self.extended_visible:
            self.extended_window.hide()

    def create_menu (self):
        actions = [
                ('FileMenu', None, _('File')),
                ('Export', None, _('Export as Image'), None,
                 _("Export your map as an image"), self.export_cb),
                ('ExportMap', Gtk.STOCK_SAVE_AS, _('Export Map...'), '<control>S',
                 _("Export your map as XML"), self.export_map_cb),
                ('Close', Gtk.STOCK_CLOSE, None, '<control>W',
                 _('Close the current window'), self.close_window_cb),
                ('EditMenu', None, _('_Edit')),
                ('ViewMenu', None, _('_View')),
                ('ShowToolbars', None, _('_Toolbar')),
                ('Undo', Gtk.STOCK_UNDO, None, '<control>Z', None),
                ('Redo', Gtk.STOCK_REDO, None, '<control><shift>Z', None),
                ('Cut', Gtk.STOCK_CUT, None, '<control>X',
                 None, self.cut_text_cb),
                ('Copy', Gtk.STOCK_COPY, None, '<control>C',
                 None, self.copy_text_cb),
                ('Paste', Gtk.STOCK_PASTE, None, '<control>V',
                 None, self.paste_text_cb),
                ('LinkThoughts', None, _("Link Thoughts"), '<control>L',
                _("Link the selected thoughts"), self.link_thoughts_cb),
                ('ModeMenu', None, _('_Mode')),
                ('ZoomIn', Gtk.STOCK_ZOOM_IN, None, '<control>plus',
                 None, self.zoomin_cb),
                ('ZoomOut', Gtk.STOCK_ZOOM_OUT, None, '<control>minus',
                 None, self.zoomout_cb),
                ('ZoomFit', Gtk.STOCK_ZOOM_FIT, None, None,
                 None, self.zoomfit_cb)]
        self.radio_actions = [
                ('Edit', Gtk.STOCK_EDIT, _('_Edit Mode'), '<control>E',
                 _('Turn on edit mode'), MMapArea.MODE_EDITING),
                 ('AddImage', Gtk.STOCK_ADD, _('_Add Image'), None,
                 _('Add an image to selected thought'), MMapArea.MODE_IMAGE),
                 ('Drawing', Gtk.STOCK_COLOR_PICKER, _('_Drawing Mode'), None,
                 _('Make a pretty drawing'), MMapArea.MODE_DRAW)]
        self.view_radio_actions = [
                ('UseBezier', None, _('Use _Curves'), None,
                 _('Use curves as links'), MMapArea.VIEW_BEZIER),
                 ('UseLines', None, _('Use _Lines'), None,
                 _('Use straight lines as links'), MMapArea.VIEW_LINES)]
        self.toggle_actions = [
                ('ViewExtend', None, _('_Extended Information'), None,
                 _('Show extended information for thoughts'), self.view_extend_cb),
                ('ShowMainToolbar', None, _('_Main'), None,
                 _('Show main toolbar'), self.show_main_toolbar_cb),
                ('ShowFormatToolbar', None, _('_Format'), None,
                 _('Show format toolbar'), self.show_format_toolbar_cb)]

        ag = Gtk.ActionGroup ('WindowActions')
        ag.set_translation_domain(gettext.textdomain())
        ag.add_actions (actions)
        ag.add_radio_actions (self.radio_actions)
        ag.add_radio_actions (self.view_radio_actions)
        ag.add_toggle_actions (self.toggle_actions)
        self.act = ag.get_action ('Edit')
        self.ext_act = ag.get_action ('ViewExtend')
        self.act.connect ("changed", self.mode_change_cb)
        self.undo.set_widgets (ag.get_action ('Undo'), ag.get_action ('Redo'))

        self.view_action = ag.get_action('UseBezier')
        self.view_action.connect ("changed", self.view_change_cb)

        self.ui = Gtk.UIManager ()
        self.ui.insert_action_group (ag, 0)
        self.ui.add_ui_from_file (utils.get_data_file_name('labyrinth-ui.xml'))
        self.main_window.add_accel_group (self.ui.get_accel_group ())

    def align_cb(self, widget, direction):
        if direction == "vl" or direction == "ht":
            self.MainArea.align_top_left(direction == "vl")
        elif direction == "vr" or direction == "hb":
            self.MainArea.align_bottom_right(direction == "vr")
        else:
            self.MainArea.align_centered(direction == "vc")

        if widget != self.align_button:
            self.align_button.disconnect(self.align_handler_id)
            self.align_handler_id = self.align_button.connect('clicked', self.align_cb, direction)
            self.align_button.set_icon_name(widget.get_image().get_icon_name()[0])

    def link_thoughts_cb (self, arg):
        self.MainArea.link_menu_cb ()

    def undo_show_extended (self, action, mode):
        self.undo.block ()
        self.ext_act.set_active (not self.ext_act.get_active ())
        self.undo.unblock ()

    def view_extend_cb (self, arg):
        self.undo.add_undo (UndoManager.UndoAction (self, UNDO_SHOW_EXTENDED, self.undo_show_extended))
        self.extended_visible = arg.get_active ()
        if self.extended_visible:
            self.extended_window.show ()
            self.view_type = 1
        else:
            self.extended_window.hide ()
            self.view_type = 0

    def show_main_toolbar_cb(self, arg):
        if arg.get_active():
            self.main_toolbar.show()
        else:
            self.main_toolbar.hide()

    def show_format_toolbar_cb(self, arg):
        if arg.get_active():
            self.format_toolbar.show()
        else:
            self.format_toolbar.hide()

    def view_change_cb(self, base, activated):
        utils.use_bezier_curves = activated.get_current_value() == MMapArea.VIEW_BEZIER
        if os.name != 'nt':
            self.config_client.set_bool('/apps/labyrinth/curves', utils.use_bezier_curves)
        self.MainArea.update_all_links()
        self.MainArea.invalidate()

    def attrs_cb (self, widget, bold, italics, underline, pango_font):
        # Yes, there is a block method for signals
        # but I don't currently know how to
        # implement it for action-based signals
        # without messyness
        if bold != self.bold_state:
            self.bold_block = True
            self.bold_widget.set_active(bold)
        if italics != self.italic_state:
            self.italic_block = True
            self.italic_widget.set_active(italics)
        if underline != self.underline_state:
            self.underline_block = True
            self.underline_widget.set_active(underline)
        if pango_font:
            font_name = pango_font.to_string()
            self.font_widget.set_font_name (font_name)
            self.MainArea.set_font(font_name)
        else:
            self.font_widget.set_font_name (utils.default_font)

    def translate (self, box, arg1, direction):
        self.orig_translate = [self.MainArea.translation[0], self.MainArea.translation[1]]
        if direction == "Up":
            translation_x = 0
            translation_y = 5
        elif direction == "Down":
            translation_x = 0
            translation_y = -5
        elif direction == "Right":
            translation_x = -5
            translation_y = 0
        elif direction == "Left":
            translation_x = 5
            translation_y = 0
        else:
            print("Error")
            return
        GObject.timeout_add (20, self.translate_timeout, translation_x, translation_y)
        self.tr_to = True

    def translate_timeout (self, addition_x, addition_y):
        if not self.tr_to:
            return False
        self.MainArea.translation[0] += addition_x / self.MainArea.scale_fac
        self.MainArea.translation[1] += addition_y / self.MainArea.scale_fac
        self.MainArea.invalidate()
        return self.tr_to

    def finish_translate (self, box, arg1):
        self.undo.add_undo (UndoManager.UndoAction (self.MainArea, UndoManager.TRANSFORM_CANVAS, \
                self.MainArea.undo_transform_cb,
                self.MainArea.scale_fac,
                self.MainArea.scale_fac,
                self.orig_translate,
                self.MainArea.translation))
        self.tr_to = False

    def pos_changed (self, panes, arg2):
        self.pane_pos = panes.get_position ()

    def bold_toggled (self, action):
        self.bold_state = (not self.bold_state)
        if self.bold_block:
            self.bold_block = False
            return
        if self.extended.is_focus ():
            self.extended.get_buffer().set_bold(action.get_active())
        else:
            self.MainArea.set_bold (action.get_active())

    def italic_toggled (self, action):
        self.italic_state = (not self.italic_state)
        if self.italic_block:
            self.italic_block = False
            return
        if self.extended.is_focus ():
            self.extended.get_buffer().set_italics(action.get_active())
        else:
            self.MainArea.set_italics (action.get_active())

    def underline_toggled (self, action):
        self.underline_state = (not self.underline_state)
        if self.underline_block:
            self.underline_block = False
            return
        if self.extended.is_focus ():
            self.extended.get_buffer().set_underline(action.get_active())
        else:
            self.MainArea.set_underline (action.get_active())

    def foreground_change_cb (self, button):
        if not self.extended.is_focus ():
            self.MainArea.set_foreground_color (button.get_color())

    def background_change_cb (self, button):
        if not self.extended.is_focus ():
            self.MainArea.set_background_color (button.get_color())

    def font_change_cb (self, button):
        if not self.extended.is_focus ():
            self.MainArea.set_font (button.get_font_name ())

    def zoomin_cb(self, arg):
        self.MainArea.scale_fac *= 1.2
        self.MainArea.invalidate()

    def zoomout_cb(self, arg):
        self.MainArea.scale_fac /= 1.2
        self.MainArea.invalidate()

    def zoomfit_cb(self, arg):
        self.MainArea.translation = [0.0, 0.0]
        self.MainArea.invalidate()

    def new_window_cb (self, arg):
        global_new_window ()
        return

    def switch_buffer_cb (self, arg, new_buffer):
        if new_buffer:
            self.extended.set_editable (True)
            self.extended.set_buffer (new_buffer)
        else:
            self.extended.set_buffer (self.invisible_buffer)
            self.extended.set_editable (False)

    def thought_selected_cb (self, arg, background_color, foreground_color):
        if background_color:
            self.background_widget.set_color(background_color)
        if foreground_color:
            self.foreground_widget.set_color(foreground_color)

    def main_area_focus_cb (self, arg, event, extended = False):
        if not extended:
            self.MainArea.grab_focus ()
        else:
            self.extended.grab_focus ()

    def revert_mode (self, action, mode):
        self.undo.block ()
        if mode == UndoManager.UNDO:
            self.mode_request_cb (None, action.args[0])
        else:
            self.mode_request_cb (None, action.args[1])
        self.undo.unblock ()

    def mode_change_cb (self, base, activated):
        self.MainArea.set_mode (activated.get_current_value ())
        self.mode = activated.get_current_value ()

    def mode_request_cb (self, widget, mode):
        self.act.set_current_value (mode)

    def title_changed_cb (self, widget, new_title):
        self.title_cp = self.title_cp = _('Untitled Map')
        if new_title != '':
            split = new_title.splitlines ()
            self.title_cp = reduce(lambda x,y : x + ' ' + y, split)

        if len(self.title_cp) > 27:
            x = self.title_cp[:27] + "..."
            self.emit ("title-changed", x, self)
        else:
            self.emit ("title-changed", self.title_cp, self)
        self.main_window.set_title (self.title_cp)

    def delete_cb (self, event):
        self.MainArea.delete_selected_elements ()

    def close_window_cb (self, event):
        self.SaveTimer.cancel = True
        self.main_window.hide ()
        self.MainArea.save_thyself ()
        del (self)

    def doc_del_cb (self, widget):
        self.emit ('window_closed', None)

    def serialize_to_xml(self, doc, top_element):
        top_element.setAttribute ("title", self.title_cp)
        top_element.setAttribute ("mode", str(self.mode))
        top_element.setAttribute ("size", str((self.width,self.height)))
        top_element.setAttribute ("position", str((self.xpos,self.ypos)))
        top_element.setAttribute ("maximised", str(self.maximised))
        top_element.setAttribute ("view_type", str(self.view_type))
        top_element.setAttribute ("pane_position", str(self.pane_pos))
        top_element.setAttribute ("scale_factor", str(self.MainArea.scale_fac))
        top_element.setAttribute ("translation", str(self.MainArea.translation))
        string = doc.toxml ()
        return string.encode ("utf-8" )

    def doc_save_cb (self, widget, doc, top_element):
        save_string = self.serialize_to_xml(doc, top_element)
        if not self.save_file:
            hsh = hashlib.sha256 (save_string)
            save_loc = utils.get_save_dir ()
            self.save_file = save_loc+hsh.hexdigest()+".map"
            counter = 1
            while os.path.exists(self.save_file):

                print("Warning: Duplicate File.  Saving to alternative")
                self.save_file = save_loc + "Dup"+str(counter)+hsh.hexdigest()+".map"
                counter += 1

        with open(self.save_file, 'w') as f:
            f.write(save_string)
        self.emit ('file_saved', self.save_file, self)

    def export_map_cb(self, event):
        chooser = Gtk.FileChooserDialog(title=_("Save File As"), action=Gtk.FileChooserAction.SAVE, \
                    buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        chooser.set_current_name ("%s.mapz" % self.main_window.title)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename ()
            self.MainArea.save_thyself ()
            tf = tarfile.open (filename, "w")
            tf.add (self.save_file, os.path.basename(self.save_file))
            for t in self.MainArea.thoughts:
                if isinstance(t, ImageThought.ImageThought):
                    tf.add (t.filename, 'images/' + os.path.basename(t.filename))

            tf.close()

        chooser.destroy()

    def parse_file (self, filename):
        with open(filename, 'r') as f:
            doc = dom.parse(f)
        top_element = doc.documentElement
        self.title_cp = top_element.getAttribute ("title")
        self.mode = int (top_element.getAttribute ("mode"))
        if top_element.hasAttribute ("maximised"):
            maxi = top_element.getAttribute ("maximised")
        else:
            maxi = False
        if maxi == "True":
            self.main_window.maximize ()
        if top_element.hasAttribute ("pane_position"):
            self.pane_pos = int (top_element.getAttribute ("pane_position"))
        else:
            self.pane_pos = 500
        if top_element.hasAttribute ("view_type"):
            vt = int (top_element.getAttribute ("view_type"))
        else:
            vt = 0
        self.extended_visible = vt == 1

        tmp = top_element.getAttribute ("size")
        (width, height) = utils.parse_coords (tmp)
        tmp = top_element.getAttribute ("position")
        (x, y) = utils.parse_coords (tmp)
        self.main_window.resize (int (width), int (height))

        # Don't know why, but metacity seems to move the window 24 pixels
        # further down than requested.  Compensate by removing 24
        # pixels from the stored size
        y -= 24
        self.main_window.move (int (x), int (y))

        self.MainArea.set_mode (self.mode)
        self.MainArea.load_thyself (top_element, doc)
        if top_element.hasAttribute("scale_factor"):
            self.MainArea.scale_fac = float (top_element.getAttribute ("scale_factor"))
        if top_element.hasAttribute("translation"):
            tmp = top_element.getAttribute("translation")
            (x,y) = utils.parse_coords(tmp)
            self.MainArea.translation = [x,y]

    def configure_cb (self, window, event):
        self.xpos = event.x
        self.ypos = event.y
        self.width = event.width
        self.height = event.height
        return False

    def window_state_cb (self, window, event):
        if event.changed_mask & Gdk.WindowState.MAXIMIZED:
            self.maximised = not self.maximised

    def toggle_range (self, arg, native_width, native_height, max_width, max_height):
        if arg.get_active ():
            self.spin_width.set_value (max_width)
            self.spin_height.set_value (max_height)
            # TODO: Fix this (and below) to cope with non-native resolutions properly
            #self.spin_width.set_sensitive (True)
            #self.spin_height.set_sensitive (True)
        else:
            #self.spin_width.set_sensitive (False)
            #self.spin_height.set_sensitive (False)
            self.spin_width.set_value (native_width)
            self.spin_height.set_value (native_height)

    def export_cb (self, event):
        maxx, maxy = self.MainArea.get_max_area ()

        x, y, width, height, bitdepth = self.MainArea.window.get_geometry ()
        glade = Gtk.Builder()
        glade.add_from_file(utils.get_data_file_name('labyrinth.xml'))
        dialog = glade.get_object('ExportImageDialog')
        box = glade.get_object('dialog_insertion')
        fc = Gtk.FileChooserWidget(Gtk.FileChooserAction.SAVE)
        box.pack_end (fc)

        filter_mapping = [  (_('All Files'), ['*']),
                                                (_('PNG Image (*.png)'), ['*.png']),
                                                (_('JPEG Image (*.jpg, *.jpeg)'), ['*.jpeg', '*.jpg']),
                                                (_('SVG Vector Image (*.svg)'), ['*.svg']),
                                                (_('PDF Portable Document (*.pdf)'), ['*.pdf']) ]

        for (filter_name, filter_patterns) in filter_mapping:
            fil = Gtk.FileFilter()
            fil.set_name(filter_name)
            for pattern in filter_patterns:
                fil.add_pattern(pattern)
            fc.add_filter(fil)

        fc.set_current_name ("%s.png" % self.main_window.title)
        rad = glade.get_object('rb_complete_map')
        rad2 = glade.get_object('rb_visible_area')
        self.spin_width = glade.get_object('width_spin')
        self.spin_height = glade.get_object('height_spin')
        self.spin_width.set_value (maxx)
        self.spin_height.set_value (maxy)
        self.spin_width.set_sensitive (False)
        self.spin_height.set_sensitive (False)

        rad.connect ('toggled', self.toggle_range, width, height,maxx,maxy)

        fc.show ()
        while 1:
        # Cheesy loop.  Break out as needed.
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                ext_mime_mapping = { 'png':'png', 'jpg':'jpeg', 'jpeg':'jpeg', \
                            'svg':'svg', 'pdf':'pdf' }
                filename = fc.get_filename()
                ext = filename[filename.rfind('.')+1:]

                try:
                    mime = ext_mime_mapping[ext]
                    break
                except KeyError:
                    msg = Gtk.MessageDialog(self, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, \
                            _("Unknown file format"))
                    msg.format_secondary_text (_("The file type '%s' is unsupported.  Please use the suffix '.png',"\
                            " '.jpg' or '.svg'." % ext))
                    msg.run ()
                    msg.destroy ()
            else:
                dialog.destroy ()
                return

        true_width = int (self.spin_width.get_value ())
        true_height = int (self.spin_height.get_value ())
        native = not rad.get_active ()
        dialog.destroy ()

        if mime in ['png', 'jpg']:
            self.save_as_pixmap(filename, mime, true_width, true_height, bitdepth, native)
        else:
            surface = None
            if mime == 'svg':
                surface = cairo.SVGSurface(filename, true_width, true_height)
            elif mime == 'pdf':
                surface = cairo.PDFSurface(filename, true_width, true_height)
            self.save_surface(surface, true_width, true_height, native)

    def save_as_pixmap(self, filename, mime, width, height, bitdepth, native):
        # FIXME: Convert to cairo surfaces:
        # http://developer.gnome.org/gtk3/3.5/ch24s02.html#id1444286
        pixmap = gtk.gdk.Pixmap (None, width, height, bitdepth)
        self.MainArea.export (pixmap.cairo_create (), width, height, native)

        pb = gtk.gdk.Pixbuf.get_from_drawable(gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height), \
                pixmap, gtk.gdk.colormap_get_system(), 0, 0, 0, 0, width, height)
        pb.save(filename, mime)

    def save_surface(self, surface, width, height, native):
        cairo_context = cairo.Context(surface)
        context = pangocairo.CairoContext(cairo_context)
        self.MainArea.export(context, width, height, native)
        surface.finish()

    def selection_changed_cb(self, area, start, end, text):
        clip = Gtk.Clipboard(selection="PRIMARY")
        if text:
            clip.set_text (text)
        else:
            clip.clear ()

    def edit_activated_cb (self, menu):
        # FIXME: Keybindings should also be deactivated.
        self.cut.set_sensitive (False)
        self.copy.set_sensitive (False)
        self.paste.set_sensitive (False)
        self.link.set_sensitive (False)
        if self.extended.is_focus ():
            self.paste.set_sensitive (True)
            stend = self.extended.get_buffer().get_selection_bounds()
            if len (stend) > 1:
                start, end = stend
            else:
                start = end = stend
        else:
            start, end = self.MainArea.get_selection_bounds ()
            try:
                if self.mode == MMapArea.MODE_EDITING and len(self.MainArea.selected) and \
                   self.MainArea.selected[0].editing:
                    self.paste.set_sensitive (True)
            except AttributeError:
                pass
            if len (self.MainArea.selected) == 2:
                self.link.set_sensitive (True)

        if start and start != end:
            self.cut.set_sensitive (True)
            self.copy.set_sensitive (True)

    def cut_text_cb (self, event):
        clip = Gtk.Clipboard()
        if self.extended.is_focus ():
            self.extended.get_buffer().cut_clipboard (clip)
        else:
            self.MainArea.cut_clipboard (clip)

    def copy_text_cb (self, event):
        clip = Gtk.Clipboard()
        if self.extended.is_focus ():
            self.extended.get_buffer().copy_clipboard (clip)
        else:
            self.MainArea.copy_clipboard (clip)

    def paste_text_cb (self, event):
        clip = Gtk.Clipboard()
        if self.extended.is_focus ():
            self.extended.get_buffer().paste_clipboard (clip, None, True)
        else:
            self.MainArea.paste_clipboard (clip)

    def start_timer (self):
        self.SaveTimer = PeriodicSaveThread.PeriodicSaveThread(self.MainArea)
        self.SaveTimer.setDaemon( True)
        self.SaveTimer.start()
