; DominusPrime Windows Installer Script
; Inno Setup Script for creating Windows installer
; Version: 0.9.7

#define MyAppName "DominusPrime"
#define MyAppVersion "0.9.7"
#define MyAppPublisher "QuantaNova"
#define MyAppURL "https://github.com/quantanova/dominus_prime_ui"
#define MyAppExeName "DominusPrime.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{8F9A2C5E-7B4D-4E6A-9F8C-1D2E3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=DominusPrime-{#MyAppVersion}-Setup
SetupIconFile=..\console\public\favicon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\DominusPrime\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  PythonVersion: String;
begin
  Result := True;
  
  // Check if Python is installed
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonVersion) then
    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonVersion) then
      if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonVersion) then
        if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.13\InstallPath', '', PythonVersion) then
          if not RegQueryStringValue(HKEY_CURRENT_USER, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonVersion) then
            if not RegQueryStringValue(HKEY_CURRENT_USER, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonVersion) then
              if not RegQueryStringValue(HKEY_CURRENT_USER, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonVersion) then
                if not RegQueryStringValue(HKEY_CURRENT_USER, 'SOFTWARE\Python\PythonCore\3.13\InstallPath', '', PythonVersion) then
                begin
                  MsgBox('Python 3.10 or higher is required but was not found. Please install Python first from python.org', mbError, MB_OK);
                  Result := False;
                end;
end;
