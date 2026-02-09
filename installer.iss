; Inno Setup Script for Smart Flashcards
; Creates a proper Windows installer with desktop shortcut

[Setup]
AppId={{B7E3A1D4-5F2C-4A8B-9D6E-1C3F5A7B9D2E}
AppName=Smart Flashcards
AppVersion=1.0.0
AppPublisher=Smart Flashcards
DefaultDirName={localappdata}\SmartFlashcards
DefaultGroupName=Smart Flashcards
OutputDir=installer_output
OutputBaseFilename=SmartFlashcards_Setup
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SmartFlashcards\SmartFlashcards.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\SmartFlashcards\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\SmartFlashcards\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Smart Flashcards"; Filename: "{app}\SmartFlashcards.exe"
Name: "{group}\Uninstall Smart Flashcards"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Smart Flashcards"; Filename: "{app}\SmartFlashcards.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SmartFlashcards.exe"; Description: "Launch Smart Flashcards"; Flags: nowait postinstall skipifsilent
