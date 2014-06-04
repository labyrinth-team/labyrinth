import pygtk
import gettext, locale
import os
import os.path as osp

pygtk.require('2.0')

import gtk

from labyrinth_lib import Browser
try:
    from labyrinth_lib import defs
    localedir = osp.abspath(osp.join(defs.DATA_DIR, "locale"))
except:
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


gtk.glade.bindtextdomain('labyrinth')
gtk.glade.textdomain('labyrinth')


def main():
    MapBrowser = Browser.Browser (
            start_hidden = False,
            tray_icon = False
    )

    gtk.main()