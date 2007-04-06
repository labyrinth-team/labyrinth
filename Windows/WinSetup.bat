@ECHO OFF
rem This is a script to automate generating Windows packages
rem It is fairly basic and still requires quite a bit of
rem user-interaction.  I'll try and include what needs doing
rem In addition, the script makes various assumptions about locations
rem and such.
rem if you really want to help, you'd write me a nice long
rem set of instructions on how to generate all this stuff under
rem cygwin and how to make most of this obsolete (if possible)


rmdir /S /Q dist
mkdir dist
del src\defs.py
copy Windows\defs.py src\defs.py

rem Assumes python is at this location.  Change to proper location
c:\Python24\python.exe Windows\winsetup.py py2exe
copy Windows\labyrinth.lnk dist\
copy Windows\labyrinth.bat dist\

mkdir dist\data_files\share\locale\ca\LC_MESSAGES
mkdir dist\data_files\share\locale\cs\LC_MESSAGES
mkdir dist\data_files\share\locale\de\LC_MESSAGES
mkdir dist\data_files\share\locale\eu\LC_MESSAGES
mkdir dist\data_files\share\locale\fr\LC_MESSAGES
mkdir dist\data_files\share\locale\it\LC_MESSAGES
mkdir dist\data_files\share\locale\nl\LC_MESSAGES
mkdir dist\data_files\share\locale\pl\LC_MESSAGES
mkdir dist\data_files\share\locale\pt_BR\LC_MESSAGES
mkdir dist\data_files\share\locale\pt\LC_MESSAGES
mkdir dist\data_files\share\locale\ru\LC_MESSAGES
mkdir dist\data_files\share\locale\sv\LC_MESSAGES

rem Assumes GetText-Tools is installed in c:
rem change as appropriate.
rem Also, a nice loop would be great here...
cd po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\ca\LC_MESSAGES\labyrinth.mo ca.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\cs\LC_MESSAGES\labyrinth.mo cs.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\de\LC_MESSAGES\labyrinth.mo de.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\eu\LC_MESSAGES\labyrinth.mo eu.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\fr\LC_MESSAGES\labyrinth.mo fr.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\it\LC_MESSAGES\labyrinth.mo it.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\nl\LC_MESSAGES\labyrinth.mo nl.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\pl\LC_MESSAGES\labyrinth.mo pl.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\pt_BR\LC_MESSAGES\labyrinth.mo pt_BR.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\pt\LC_MESSAGES\labyrinth.mo pt_PT.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\ru\LC_MESSAGES\labyrinth.mo ru.po
c:\GetText-Tools\bin\msgfmt.exe -o ..\dist\data_files\share\locale\sv\LC_MESSAGES\labyrinth.mo sv.po

cd ..
rem and that's it folks.  From here on out, you need user-interaction
rem (sorry).  Copy relevant files from the GTK install (Need a list of
rem what can be deleted etc. and then run innosetup using the given iss


rem This is specific to my install.  Copying files from GTK install
rem in c:.  Edit as needed ;)

mkdir dist\data_files\lib
copy c:\GTK\lib dist\data_files\lib
mkdir dist\data_files\lib\gtk-2.0
mkdir dist\data_files\lib\gtk-2.0\2.4.0\engines
mkdir dist\data_files\lib\gtk-2.0\2.4.0\immodules
mkdir dist\data_files\lib\gtk-2.0\2.4.0\loaders
mkdir dist\data_files\lib\libglade
mkdir dist\data_files\lib\pango
mkdir dist\data_files\lib\pango\1.4.0\modules

copy c:\GTK\lib\gtk-2.0\2.4.0\engines dist\data_files\lib\gtk-2.0\2.4.0\engines
copy c:\GTK\lib\gtk-2.0\2.4.0\immodules dist\data_files\lib\gtk-2.0\2.4.0\immodules
copy c:\GTK\lib\gtk-2.0\2.4.0\loaders dist\data_files\lib\gtk-2.0\2.4.0\loaders
copy c:\GTK\lib\libglade dist\data_files\lib\libglade
copy c:\GTK\lib\pango\1.4.0\modules dist\data_files\lib\pango\1.4.0\modules
mkdir dist\data_files\etc
mkdir dist\data_files\etc\fonts
mkdir dist\data_files\etc\gtk-2.0
mkdir  dist\data_files\etc\pango
copy c:\GTK\etc\fonts dist\data_files\etc\fonts
copy c:\GTK\etc\gtk-2.0 dist\data_files\etc\gtk-2.0
copy c:\GTK\etc\pango dist\data_files\etc\pango

mkdir dist\data_files\share\themes\MS-Windows\gtk-2.0
mkdir dist\data_files\share\themes\Default\gtk-2.0-key
mkdir dist\data_files\share\themes\Metal\gtk-2.0
mkdir dist\data_files\share\themes\Raleigh\gtk-2.0
mkdir dist\data_files\share\themes\Redmond95\gtk-2.0

copy c:\GTK\share\themes\MS-Windows\gtk-2.0 dist\data_files\share\themes\MS-Windows\gtk-2.0
copy c:\GTK\share\themes\Default\gtk-2.0-key dist\data_files\share\themes\Default\gtk-2.0-key
copy c:\GTK\share\themes\Metal\gtk-2.0 dist\data_files\share\themes\Metal\gtk-2.0
copy c:\GTK\share\themes\Raleigh\gtk-2.0 dist\data_files\share\themes\Raleigh\gtk-2.0
copy c:\GTK\share\themes\Redmond95\gtk-2.0 dist\data_files\share\themes\Redmond95\gtk-2.0

copy c:\GTK\share\locale\ca\LC_MESSAGES dist\data_files\share\locale\ca\LC_MESSAGES
copy c:\GTK\share\locale\cs\LC_MESSAGES dist\data_files\share\locale\cs\LC_MESSAGES
copy c:\GTK\share\locale\de\LC_MESSAGES dist\data_files\share\locale\de\LC_MESSAGES
copy c:\GTK\share\locale\eu\LC_MESSAGES dist\data_files\share\locale\eu\LC_MESSAGES
copy c:\GTK\share\locale\fr\LC_MESSAGES dist\data_files\share\locale\fr\LC_MESSAGES
copy c:\GTK\share\locale\it\LC_MESSAGES dist\data_files\share\locale\it\LC_MESSAGES
copy c:\GTK\share\locale\nl\LC_MESSAGES dist\data_files\share\locale\nl\LC_MESSAGES
copy c:\GTK\share\locale\pl\LC_MESSAGES dist\data_files\share\locale\pl\LC_MESSAGES
copy c:\GTK\share\locale\pt\LC_MESSAGES dist\data_files\share\locale\pt\LC_MESSAGES
copy c:\GTK\share\locale\pt_BR\LC_MESSAGES dist\data_files\share\locale\pt_BR\LC_MESSAGES
copy c:\GTK\share\locale\ru\LC_MESSAGES dist\data_files\share\locale\ru\LC_MESSAGES
copy c:\GTK\share\locale\sv\LC_MESSAGES dist\data_files\share\locale\sv\LC_MESSAGES
