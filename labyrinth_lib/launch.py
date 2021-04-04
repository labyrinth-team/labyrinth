import gettext, locale
import optparse
import os
import os.path as osp
import sys

import gi

gi.require_versions({
    'Gtk': '3.0',
    'GConf': '2.0',
    'PangoCairo': '1.0',
    'PangoAttrCast': '1.0',
})

from gi.repository import Gtk

from labyrinth_lib import Browser
from labyrinth_lib import utils

def prepare_locale():
    if os.name == 'nt':
        instdir = osp.abspath(osp.dirname(sys.argv[0]))
        localedir = osp.join(instdir, "locale")
    else:
        localedir = "/usr/share/locale"

    gettext.bindtextdomain('labyrinth', localedir)
    if hasattr(gettext, 'bind_textdomain_codeset'):
        gettext.bind_textdomain_codeset('labyrinth','UTF-8')

    gettext.textdomain('labyrinth')

    if hasattr(locale, 'bindtextdomain'):
        if not os.name == 'nt':
            locale.bindtextdomain('labyrinth', localedir)
            if hasattr(locale, 'bind_textdomain_codeset'):
                locale.bind_textdomain_codeset('labyrinth','UTF-8')
            locale.textdomain('labyrinth')

def set_win_taskbar_app():
    "On Windows 7, use our own icon in the taskbar rather than the Python one."
    if os.name != 'nt':
        return
    import ctypes
    myappid = 'labyrinth_team.labyrinth' # arbitrary string
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except AttributeError:
        # That function doesn't exist on Windows XP
        pass

def main():
    parser = optparse.OptionParser()
    parser.add_option("--use-tray-icon", dest="tray_icon",
            action="store_true", default=False)
    parser.add_option("--no-tray-icon", dest="tray_icon", action="store_false")
    parser.add_option("--hide-main-window", action="store_true", default=False)
    parser.add_option("-m", "--map", action="store", type="string", dest="filename",
            help="Open a map from a given filename (from internal database)")
    parser.add_option("-o", "--open", action="store", type="string",
            dest="filepath", help="Open a map from a given filename (including path)")

    (options, args) = parser.parse_args()
    if not options.tray_icon:
        options.hide_main_window=False

    MapBrowser = Browser.Browser (
            start_hidden = options.hide_main_window,
            tray_icon = options.tray_icon
    )

    if options.filename != None:
        MapBrowser.open_map_filename (utils.get_save_dir() + options.filename)
    elif options.filepath != None:
        MapBrowser.open_map_filename (options.filepath)

    Gtk.main()

if __name__ == '__main__':
    main()
