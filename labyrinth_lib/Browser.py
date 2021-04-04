# Browser.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <Don@Scorgie.org>
#                    - Andreas Sliwka <andreas.sliwka@gmail.com>
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
import tarfile
import os
import gettext
_ = gettext.gettext

# Gtk stuff
from gi.repository import Gtk
if os.name != 'nt':
    from gi.repository import GConf
from gi.repository import Pango
from gi.repository import GObject
from gi.repository import GdkPixbuf

# Local imports
from . import utils
from . import MainWindow
from .MapList import MapList
from . import TrayIcon

from . import __version__

AUTHORS = ['Don Scorgie <Don@Scorgie.org>',
                   'Martin Schaaf <mascha@ma-scha.de>',
                   'Matthias Vogelgesang <matthias.vogelgesang@gmail.com>',
                   'Andreas Sliwka <andreas.sliwka@gmail.com>']

class Browser (Gtk.Window):
    COL_ID = 0
    COL_TITLE = 1
    COL_MODTIME = 2

    def __init__(self, start_hidden, tray_icon):
        super(Browser, self).__init__()
        self.glade = Gtk.Builder()
        self.glade.add_from_file(utils.get_data_file_name('labyrinth.xml'))
        self.view = self.glade.get_object('MainView')
        self.populate_view ()
        self.view.connect ('row-activated', self.open_row_cb)
        self.view.connect ('cursor-changed', self.cursor_change_cb)

        self.view_dependants = []

        self.open_button = self.glade.get_object('OpenButton')
        self.delete_button = self.glade.get_object('DeleteButton')
        self.open_menu = self.glade.get_object('open1')
        self.delete_menu = self.glade.get_object('delete1')

        self.view_dependants.append (self.open_button)
        self.view_dependants.append (self.delete_button)
        self.view_dependants.append (self.open_menu)
        self.view_dependants.append (self.delete_menu)

        self.open_button.connect ('clicked', self.open_clicked)
        self.glade.get_object('NewButton').connect ('clicked', self.new_clicked)
        self.delete_button.connect ('clicked', self.delete_clicked)

        self.open_menu.connect ('activate', self.open_clicked)
        self.glade.get_object('new1').connect ('activate', self.new_clicked)
        self.delete_menu.connect ('activate', self.delete_clicked)
        self.glade.get_object('import1').connect ('activate', self.import_clicked)
        self.glade.get_object('quit1').connect ('activate', self.quit_clicked)
        self.glade.get_object('about1').connect ('activate', self.about_clicked)
        self.glade.get_object('showhelp').connect ('activate', self.show_help_clicked)

        for widget in self.view_dependants:
            widget.set_sensitive(False)

        self.main_window = self.glade.get_object('MapBrowser')

        # set remembered size
        if os.name != 'nt':
            self.config_client = GConf.Client.get_default()
            self.config_client.add_dir("/apps/labyrinth", GConf.ClientPreloadType.PRELOAD_NONE)

            width = self.config_client.get_int ('/apps/labyrinth/width')
            height = self.config_client.get_int ('/apps/labyrinth/height')
            utils.use_bezier_curves = self.config_client.get_bool ('/apps/labyrinth/curves')
            if width == 0 or height == 0:
                width = 400
                height = 300
        else:
            width = 400
            height = 300

        view_sortable = self.view.get_model ()
        view_sortable.connect ('sort-column-changed', self.sort_column_changed_cb)
        if os.name != 'nt':
            sort_order = self.config_client.get_int('/apps/labyrinth/map_sort_order')
            column_id = self.config_client.get_int('/apps/labyrinth/map_sort_order_column')
            view_sortable.set_sort_column_id (column_id, sort_order)

        self.main_window.resize (width, height)

        if os.name != 'nt':
            try:
                self.main_window.set_icon_name ('labyrinth')
            except:
                self.main_window.set_icon_from_file(utils.get_data_file_name('labyrinth.svg'))
        else:
            self.main_window.set_icon_from_file(utils.get_data_file_name('labyrinth-32.png'))
        if tray_icon:
            self.main_window.connect ('delete_event', self.toggle_main_window, None)
            traymenu = Gtk.Menu()
            quit_item = Gtk.MenuItem("Quit")
            quit_item.connect("activate",self.quit_clicked)
            traymenu.add(quit_item)
            traymenu.show_all()
            self.traymenu = traymenu
            self.trayicon = TrayIcon.TrayIcon(
                                            icon_name="labyrinth",
                                            menu=traymenu,
                                            activate=self.toggle_main_window)
        else:
            self.main_window.connect('delete_event', self.quit_clicked, None)
        if start_hidden:
            self.main_window.hide ()
        else:
            self.main_window.show_all ()

    def toggle_main_window(self,*args):
        if self.main_window.get_property("visible"):
            self.main_window.hide()
        else:
            self.main_window.show()
        return True

    def map_title_cb (self, mobj, new_title, mobj1):
        map = MapList.get_by_window(mobj)
        if not map:
            raise AttributeError ("What a mess, can't find the map")
        map.title = new_title

    def get_selected_map(self):
        sel = self.view.get_selection ()
        (model, it) = sel.get_selected ()
        if it:
            (num,) = MapList.tree_view_model.get (it, self.COL_ID)
            return MapList.get_by_index(num)
        return None

    def cursor_change_cb (self, treeview):
        selected_map = self.get_selected_map ()
        sensitive = not not self.get_selected_map ()
        for widget in self.view_dependants:
            widget.set_sensitive(sensitive)

    def open_map_filename (self, fname):
        win = MainWindow.LabyrinthWindow (fname)
        win.show ()

    def open_map (self, map, imported=False):
        win = MainWindow.LabyrinthWindow (map.filename, imported)
        win.connect ("title-changed", self.map_title_cb)
        win.connect ("window_closed", self.remove_map_cb)
        win.connect ("file_saved", self.file_save_cb)
        win.show ()
        map.window = win
        return (MapList.index(map), win)

    def open_selected_map(self):
        map = self.get_selected_map()
        if map is None:
            # This should be impossible, because the button & menu entry aren't
            # active until a map is selected.
            raise RuntimeError("'open' clicked with no map selected")
        if map.window:
            print("Window for map '%s' is already open" % map.title)
            # may be the window should be raised?
        else:
            self.open_map (map)

    def show_help_clicked(self, arg):
        try:
            Gtk.show_uri(None, "ghelp:labyrinth", 0)
        except GObject.GError as e:
            print(_('Unable to display help: %s') % str(e))

    def about_clicked (self, arg):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_name ("Labyrinth")
        about_dialog.set_version (__version__)
        if os.name != 'nt':
            try:
                about_dialog.set_logo_icon_name("labyrinth")
            except:
                pass
        else:
            about_dialog.set_logo (GdkPixbuf.Pixbuf.new_from_file(
                utils.get_data_file_name("labyrinth-32.png")
            ))
        about_dialog.set_license (
"Labyrinth is free software; you can redistribute it and/or modify "
"it under the terms of the GNU General Public Licence as published by "
"the Free Software Foundation; either version 2 of the Licence, or "
"(at your option) any later version."
"\n\n"
"Labyrinth is distributed in the hope that it will be useful, "
"but WITHOUT ANY WARRANTY; without even the implied warranty of "
"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
"GNU General Public Licence for more details."
"\n\n"
"You should have received a copy of the GNU General Public Licence "
"along with Labyrinth; if not, write to the Free Software Foundation, Inc., "
"59 Temple Place, Suite 330, Boston, MA  02111-1307  USA")
        about_dialog.set_wrap_license (True)
        about_dialog.set_copyright ("2006-2008 Don Scorgie et. al")
        about_dialog.set_authors (AUTHORS)
        about_dialog.set_website ("http://code.google.com/p/labyrinth")
        about_dialog.set_translator_credits (_("Translation by Don Scorgie"))
        about_dialog.run ()
        about_dialog.hide ()
        del (about_dialog)
        return

    def open_clicked (self, button):
        self.open_selected_map()

    def open_row_cb (self, view, path, col):
        self.open_selected_map ()

    def new_clicked (self, button):
        map = MapList.create_empty_map()
        self.open_map(map)

    def delete_clicked (self, button):
        map = self.get_selected_map ()
        if not map:
            # This should be impossible, because the button & menu entry aren't
            # active until a map is selected.
            raise RuntimeError("'delete' clicked with no map selected")
        error_message = ""
        if map.window:
            error_message =  _("The map cannot be deleted right now. Is it open?")
        elif not map.filename:
            error_message = _("The map has no associated filename.")
        if error_message:
            dialog = Gtk.MessageDialog (self, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK,
                                                            _("Cannot delete this map"))
            dialog.format_secondary_text (error_message)
            dialog.run ()
            dialog.hide ()
            del (dialog)
            return
        dialog = Gtk.MessageDialog (self, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO,
                                                                _("Do you really want to delete this Map?"))
        resp = dialog.run ()
        dialog.hide ()
        del (dialog)
        if resp != Gtk.ResponseType.YES:
            return
        MapList.delete (map)
        self.view.emit ('cursor-changed')

    def remove_map_cb (self, mobj, a):
        map = MapList.get_by_window(mobj)
        if map:
            MapList.delete(map)
            self.view.emit ('cursor-changed')
            return
        raise KeyError("Cant remove map of window %s" % mobj)

    def file_save_cb (self, mobj, new_fname, mobj1):
        map = MapList.get_by_window(mobj)
        if map:
            map.window = None
            map.filename = new_fname
        return

    def import_clicked(self, button, other=None, *data):
        chooser = Gtk.FileChooserNative.new(
            title=_("Import map"),
            parent=self.main_window,
            action=Gtk.FileChooserAction.OPEN,
        )

        filtr = Gtk.FileFilter()
        filtr.set_name(_('MAPZ Compressed Map (*.mapz)'))
        filtr.add_pattern('*.mapz')
        chooser.add_filter(filtr)

        response = chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = chooser.get_filename()
            tf = tarfile.open(filename)
            mapname = os.path.join (utils.get_save_dir (), tf.getnames()[0])
            tf.extractall(utils.get_save_dir())
            tf.close()
            map = MapList.new_from_file(mapname)
            map.filename = mapname

        chooser.destroy()

    def quit_clicked (self, button, other=None, *data):
        for map in MapList.get_open_windows():
            map.window.close_window_cb (None)

        width, height = self.main_window.get_size()

        if os.name != 'nt':
            self.config_client.set_int('/apps/labyrinth/width', width)
            self.config_client.set_int('/apps/labyrinth/height', height)

        Gtk.main_quit()

    def populate_view (self):
        cellrenderer = Gtk.CellRendererText()
        cellrenderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn(_("Map Name"), cellrenderer,
                                                                text=self.COL_TITLE)
        column.set_resizable(True)
        column.set_expand (True)
        column.set_sort_column_id (1)
        self.view.append_column(column)

        col1 = Gtk.TreeViewColumn(_("Last Modified"), Gtk.CellRendererText(),
                                                       text=self.COL_MODTIME)
        col1.set_resizable(True)
        col1.set_sort_column_id (2)
        self.view.append_column(col1)

        self.view.set_model (MapList.get_TreeViewModel())
        self.view.set_search_column(self.COL_TITLE)
        self.view.set_enable_search (True)

    def sort_column_changed_cb (self, data):
        column_id, sort_order = data.get_sort_column_id ()
        if os.name != 'nt':
            self.config_client.set_int('/apps/labyrinth/map_sort_order', sort_order)
            self.config_client.set_int('/apps/labyrinth/map_sort_order_column', column_id)
