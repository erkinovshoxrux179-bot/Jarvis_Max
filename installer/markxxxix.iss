[Setup]
AppName=MARK XXXIX
AppVersion=39.0
DefaultDirName={localappdata}\Mark-XXXIX
DefaultGroupName=MARK XXXIX
OutputBaseFilename=MarkXXXIX-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\MarkXXXIX-Setup.exe"; DestDir: "{tmp}"; Flags: ignoreversion

[Run]
Filename: "{tmp}\MarkXXXIX-Setup.exe"; Parameters: ""; Flags: nowait postinstall skipifsilent

