; Inno Setup Script for Smart Flashcards
; Creates a proper Windows installer with desktop shortcut
; Version comes from build.py (ISCC /DAppVer=x.y.z); the fallback below keeps a
; manual Ctrl+F9 compile working too. build.py is the recommended one-shot build.
#ifndef AppVer
  #define AppVer "1.0.2"
#endif

[Setup]
AppId={{B7E3A1D4-5F2C-4A8B-9D6E-1C3F5A7B9D2E}
AppName=Smart Flashcards
AppVersion={#AppVer}
VersionInfoVersion={#AppVer}
AppPublisher=Smart Flashcards
; Icon shown on the Setup.exe itself and in Add/Remove Programs.
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\SmartFlashcards.exe
DefaultDirName={localappdata}\SmartFlashcards
; Always show the "choose install location" page (default was auto-hidden when a
; previous install was detected, which silently reused the old D: folder).
DisableDirPage=no
DefaultGroupName=Smart Flashcards
OutputDir=installer_output
OutputBaseFilename=SmartFlashcards_Setup
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
; Silent auto-update: close the running app before replacing its files, and don't
; force a reboot. The updater runs this installer with /VERYSILENT (no wizard).
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"  

[Files]
; Wrap the whole Nuitka standalone folder (exe + Qt DLLs + Python runtime, ~124 MB).
Source: "nuitka_build\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: user data (vocabulary, profiles, config, logs) is intentionally NOT shipped.
; The app creates it per-user in %APPDATA%\SmartFlashcards on first run, so each
; user starts with their own empty vocabulary and their data survives uninstall.

[Icons]
Name: "{group}\Smart Flashcards"; Filename: "{app}\SmartFlashcards.exe"
Name: "{group}\Uninstall Smart Flashcards"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Smart Flashcards"; Filename: "{app}\SmartFlashcards.exe"; Tasks: desktopicon

[Run]
; No 'skipifsilent' — so the app relaunches itself after a silent auto-update too.
Filename: "{app}\SmartFlashcards.exe"; Description: "Launch Smart Flashcards"; Flags: nowait postinstall
