# Run this to install Labyrinth's optional data files - language packs, icons,
# and the .desktop file.
#
# Set the $DESTDIR environment variable to install somewhere other than root.
set -e

echo "Installing icons"
for size in 16x16 22x22 24x24 scalable; do install -d $DESTDIR/usr/share/icons/hicolor/$size/apps; done
install -m 644 data/labyrinth-16.png $DESTDIR/usr/share/icons/hicolor/16x16/apps/labyrinth.png
install -m 644 data/labyrinth-22.png $DESTDIR/usr/share/icons/hicolor/22x22/apps/labyrinth.png
install -m 644 data/labyrinth-24.png $DESTDIR/usr/share/icons/hicolor/24x24/apps/labyrinth.png
install -m 644 data/labyrinth.svg $DESTDIR/usr/share/icons/hicolor/scalable/apps/labyrinth.svg

echo "Installing .desktop file"
install -D -m 755 data/labyrinth.desktop $DESTDIR/usr/share/applications/labyrinth.desktop

echo "Installing translations"
make -C po localedir=$DESTDIR/usr/share/locale install
