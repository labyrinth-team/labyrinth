@INTLTOOL_XML_RULE@

uidir = $(datadir)/labyrinth

ui_DATA = labyrinth-ui.xml labyrinth.glade

desktopdir = $(datadir)/applications
desktop_in_files = labyrinth.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

gtk_update_icon_cache = gtk-update-icon-cache -f -t $(datadir)/icons/hicolor

install-icons:
# This sucks
	for size in 16x16 22x22 24x24 scalable; do install -d $(DESTDIR)/$(datadir)/icons/hicolor/$$size/apps; done
	install -m 644 $(srcdir)/labyrinth-16.png $(DESTDIR)/$(datadir)/icons/hicolor/16x16/apps/labyrinth.png
	install -m 644 $(srcdir)/labyrinth-22.png $(DESTDIR)/$(datadir)/icons/hicolor/22x22/apps/labyrinth.png
	install -m 644 $(srcdir)/labyrinth-24.png $(DESTDIR)/$(datadir)/icons/hicolor/24x24/apps/labyrinth.png
	install -m 644 $(srcdir)/labyrinth.svg $(DESTDIR)/$(datadir)/icons/hicolor/scalable/apps/labyrinth.svg

install-data-local: install-icons
	if test -z "$(DESTDIR)"; then \
	        echo "Updating Gtk icon cache."; \
	        $(gtk_update_icon_cache); \
	else \
	        echo "*** Icon cache not updated.  After install, run this:"; \
	        echo "***   $(gtk_update_icon_cache)"; \
	        fi

uninstall-local:
	rm -f $(DESTDIR)/$(datadir)/icons/hicolor/16x16/apps/labyrinth.png
	rm -f $(DESTDIR)/$(datadir)/icons/hicolor/22x22/apps/labyrinth.png
	rm -f $(DESTDIR)/$(datadir)/icons/hicolor/24x24/apps/labyrinth.png
	rm -f $(DESTDIR)/$(datadir)/icons/hicolor/scalable/apps/labyrinth.svg
	if test -z "$(DESTDIR)"; then \
	        echo "Updating Gtk icon cache."; \
	        $(gtk_update_icon_cache); \
	else \
	        echo "*** Icon cache not updated.  After install, run this:"; \
	        echo "***   $(gtk_update_icon_cache)"; \
	        fi

CLEANFILES = $(desktop_DATA)

EXTRA_DIST = $(ui_DATA) labyrinth-16.png labyrinth-22.png labyrinth-24.png labyrinth.svg $(desktop_in_files)
