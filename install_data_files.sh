# Run this to install Labyrinth's optional data files - language packs, icons,
# and the .desktop file.
#
# Set the $PREFIX environment variable to install somewhere other than /usr.
set -e

# := sets the variable to the default if it's not already set
echo "Installing data files to prefix: ${PREFIX:=/usr}"

echo "Installing icons"
for size in 16x16 22x22 24x24 scalable; do install -d $PREFIX/share/icons/hicolor/$size/apps; done
install -m 644 data/labyrinth-16.png $PREFIX/share/icons/hicolor/16x16/apps/labyrinth.png
install -m 644 data/labyrinth-22.png $PREFIX/share/icons/hicolor/22x22/apps/labyrinth.png
install -m 644 data/labyrinth-24.png $PREFIX/share/icons/hicolor/24x24/apps/labyrinth.png
install -m 644 data/labyrinth.svg $PREFIX/share/icons/hicolor/scalable/apps/labyrinth.svg

echo "Installing .desktop file"
install -D -m 755 data/labyrinth.desktop $PREFIX/share/applications/labyrinth.desktop

echo "Installing .appdata.xml file"
install -D -m 644 data/labyrinth.appdata.xml $PREFIX/share/appdata/labyrinth.appdata.xml

echo "Installing translations"
make -C po localedir=$PREFIX/share/locale install
