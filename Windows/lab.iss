[Setup]
AppName=Labyrinth
AppVerName=Labyrinth 0.3
AppPublisher=Don Scorgie
AppPublisherURL=http://www.gnome.org/~dscorgie/labyrinth.html
DefaultDirName={pf}\labyrinth
DefaultGroupName=Labyrinth
DisableProgramGroupPage=true
OutputBaseFilename=labyrinth-setup
Compression=lzma
SolidCompression=true
AllowUNCPath=false
VersionInfoVersion=0.3
VersionInfoCompany=None
VersionInfoDescription=A Mind mapping tool
PrivilegesRequired=admin
LicenseFile=COPYING.txt


[Dirs]
Name: {app}; Flags: uninsalwaysuninstall;

[Files]
Source: ..\dist\*; DestDir: {app}; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: {group}\labyrinth; Filename: {app}\data_files\labyrinth.exe; WorkingDir: {app}\data_files

[Run]
Filename: {app}\labyrinth.bat; Description: {cm:LaunchProgram,labyrinth}; Flags: nowait postinstall skipifsilent
