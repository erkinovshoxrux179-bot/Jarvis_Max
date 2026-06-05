[Setup]
AppName=MARK XXXIX - JARVIS AI Assistant
AppVersion=39.0.1
AppPublisher=FatihMakes
AppPublisherURL=https://github.com/erkinovshoxrux179-bot/Jarvis_Max
DefaultDirName={localappdata}\Mark-XXXIX
DefaultGroupName=MARK XXXIX
OutputBaseFilename=MarkXXXIX-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\ico.ico
UninstallDisplayIcon={app}\ico.ico
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupentry"; Description: "Start JARVIS with Windows"; GroupDescription: "Startup:"

[Files]
Source: "..\dist\Mark_XXXIX\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\ico.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MARK XXXIX"; Filename: "{app}\Mark_XXXIX.exe"; IconFilename: "{app}\ico.ico"
Name: "{group}\Uninstall MARK XXXIX"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MARK XXXIX - JARVIS"; Filename: "{app}\Mark_XXXIX.exe"; IconFilename: "{app}\ico.ico"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "MarkXXXIX_JARVIS"; ValueData: """{app}\Mark_XXXIX.exe"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
Filename: "{app}\Mark_XXXIX.exe"; Description: "Launch MARK XXXIX"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\memory"
Type: filesandordirs; Name: "{app}\__pycache__"
