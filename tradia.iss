; Inno Setup script for Tradia
; Creates Start Menu and Desktop shortcuts

#define MyAppName "Tradia"
#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "Ebenezer Fuachie"
#define MyAppURL ""
#define MyAppExeName "tradia.exe"
#define MyAppId "{6CFBE7E7-7B8E-4B0F-9B77-32F9C6F4D6A1}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
Disable ProgramGroupPage=no
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
OutputDir=output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\tradia.ico
ArchitecturesInstallIn64BitMode=x64
; Request admin for Program Files install
PrivilegesRequired=admin
UsePreviousAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Build your app with PyInstaller first: pyinstaller tradia.spec
; Then point this to the PyInstaller dist output folder
Source: "dist\tradia\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
; Desktop shortcut (now always created)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
; Uninstall shortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Offer to launch after install completes
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Nothing extra to delete; user data (SQLite DB) is stored under Documents/tradia/data
