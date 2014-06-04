# This script downloads, unpacks and arranges the necessary compiled libraries
# to build a Windows installer for Labyrinth. After running this, you can use
# Pynsist (http://pynsist.readthedocs.org/) to build the installer by running:
#  pynsist installer.cfg

# At present, this is a Linux shell script, because that was the easiest way to
# write it. We can translate it into Python if you want to run it on Windows.

# Download the necessary files
wget -O gtkbundle.zip http://ftp.gnome.org/pub/gnome/binaries/win32/gtk+/2.24/gtk+-bundle_2.24.10-20120208_win32.zip
wget -O pygobject.exe http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.28/pygobject-2.28.3.win32-py2.7.exe
wget -O pycairo.exe http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.8/pycairo-1.8.10.win32-py2.7.exe
wget -O pygtk.exe http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-2.24.0.win32-py2.7.exe

# GTK runtime
mkdir gtkbundle
unzip -d gtkbundle gtkbundle.zip
cd gtkbundle
rm -r src man include share/doc share/man share/gtk-doc share/gtk-2.0/demo bin/gtk-demo.exe etc/bash_completion.d
cd ..

# Python bindings
mkdir pygobject
unzip -d pygobject pygobject.exe
mkdir pycairo
unzip -d pycairo pycairo.exe
mkdir pygtk
unzip -d pygtk pygtk.exe

# Reassemble into pynsist_pkgs
echo -n "Assembling GTK files into pynsist_pkgs... "
rm -r pynsist_pkgs
mkdir pynsist_pkgs
mv gtkbundle pynsist_pkgs/gtk

cp -r pygobject/PLATLIB/* pynsist_pkgs
rm -r pygobject

cp -r pycairo/PLATLIB/* pynsist_pkgs
cp -r pycairo/DATA/lib/site-packages/cairo/* pynsist_pkgs/cairo
rm -r pycairo

cp -r pygtk/PLATLIB/* pynsist_pkgs
rm -r pygtk

rm -r pynsist_pkgs/gtk-2.0/tests

echo "done"

# Extra bits for libglade
wget -O libglade.zip http://ftp.gnome.org/pub/GNOME/binaries/win32/libglade/2.6/libglade_2.6.4-1_win32.zip
wget -O libxml2.zip ftp://ftp.zlatkovic.com/libxml/libxml2-2.7.8.win32.zip
wget -O iconv.zip ftp://ftp.zlatkovic.com/libxml/iconv-1.9.2.win32.zip

unzip -d libglade libglade.zip
cp libglade/bin/libglade-2.0-0.dll pynsist_pkgs/gtk/bin/
rm -r libglade

unzip -d libxml2 libxml2.zip
cp libxml2/libxml2-*/bin/libxml2.dll pynsist_pkgs/gtk/bin/libxml2-2.dll
rm -r libxml2

unzip -d iconv iconv.zip
cp iconv/iconv-*/bin/iconv.dll pynsist_pkgs/gtk/bin/
rm -r iconv
