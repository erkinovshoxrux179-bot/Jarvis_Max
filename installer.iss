[Setup]
AppName=Mark XXXIX
AppVersion=1.0
DefaultDirName={pf}\Mark XXXIX
DefaultGroupName=Mark XXXIX
OutputDir=dist
OutputBaseFilename=Mark_XXXIX_Installer
Compression=lzma
SolidCompression=yes
SetupIconFile=ico.ico

[Files]
Source: "dist\Mark_XXXIX.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Mark XXXIX"; Filename: "{app}\Mark_XXXIX.exe"; IconFilename: "{app}\Mark_XXXIX.exe"
Name: "{commondesktop}\Mark XXXIX"; Filename: "{app}\Mark_XXXIX.exe"; IconFilename: "{app}\Mark_XXXIX.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\Mark_XXXIX.exe"; Description: "Launch Mark XXXIX"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\Mark_XXXIX.exe"