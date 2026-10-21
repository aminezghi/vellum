; ---------------------------------------------------------------------------
;  Vellum Desktop V2.0 - Fernly Botanical Bento Edition
;  Inno Setup script -> Windows installer (.exe)
;
;  Builds a standard installer around the PyInstaller onedir bundle produced by
;  Desktop_App\build_vellum_windows.spec (Desktop_App\dist\Vellum\).
;
;  Install location is per-user (%LOCALAPPDATA%\Programs) so the installer runs
;  without administrator rights - this is a local research tool, not a
;  machine-wide deployment.
;
;  The uninstaller never touches user data: the research vault
;  (%USERPROFILE%\Vellum_Research_Vault), the config (%USERPROFILE%\.vellum_config.json)
;  and the recent-folder list (%USERPROFILE%\.vellum) survive removal unless the
;  user explicitly opts in.
; ---------------------------------------------------------------------------

#define AppName "Vellum Desktop"
#define AppNameFull "Vellum Desktop V2.0"
#define AppVersion "2.0.0"
#define AppPublisher "Amine Zouaghi"
#define AppExeName "Vellum.exe"
#define AppId "{{9C1B5A74-6D2E-4C3A-9E51-7F2D8A4B6C10}"

[Setup]
AppId={#AppId}
AppName={#AppNameFull}
AppVersion={#AppVersion}
AppVerName={#AppNameFull} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/aminezouaghi
AppComments=Local-first academic literature, PDF harvesting and systematic review workbench.
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppNameFull} Installer
VersionInfoProductName={#AppNameFull}
VersionInfoProductVersion={#AppVersion}

; LZMA2 with solid compression: the bundled scientific wheels share a lot of
; structure, so a solid archive shrinks the installer substantially.
Compression=lzma2/max
SolidCompression=yes

DefaultDirName={localappdata}\Programs\Vellum Desktop
DefaultGroupName={#AppNameFull}
DisableProgramGroupPage=yes
DisableDirPage=no
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Vellum-Desktop-V2.0-Setup-x64
SetupIconFile=..\Desktop_App\downloader.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppNameFull}

; Per-user install: no admin rights required.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

WizardStyle=modern
WizardSizePercent=110
ShowLanguageDialog=no
; Timestamps make the installer reproducible for a given source tree.
UsePreviousAppDir=yes
UsePreviousGroup=yes
CloseApplications=no
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "launchapp";  Description: "Launch {#AppNameFull} after installation"; GroupDescription: "Post-installation:"; Flags: checkedonce

[Files]
; The frozen application bundle produced by PyInstaller.
Source: "dist\Vellum\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; The printed manual, shipped alongside the app so the Start Menu link works.
Source: "..\README_VELLUM_DESKTOP_V2.0.pdf"; DestDir: "{app}\docs"; DestName: "Vellum-Desktop-V2.0-Guide.pdf"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppNameFull}";        Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppNameFull}"; Filename: "{uninstallexe}"
Name: "{group}\User Guide (PDF)";      Filename: "{app}\docs\Vellum-Desktop-V2.0-Guide.pdf"; Comment: "Open the Vellum Desktop user manual"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppNameFull}}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent runascurrentuser; Tasks: launchapp

[UninstallDelete]
; Leftover logs the app writes to the temp directory. User data under
; %USERPROFILE% is deliberately NOT removed here.
Type: files; Name: "{tmp}\vellum-desktop-server.log"
Type: files; Name: "{tmp}\vellum-desktop-app.log"
Type: filesandordirs; Name: "{tmp}\vellum_desktop_app_profile"

[Code]
{ Stop a running Vellum before install or uninstall so its files are not locked. }
function KillRunningVellum(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  Exec(ExpandConstant('{cmd}'),
       '/C taskkill /F /IM {#AppExeName} /T >nul 2>nul',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    KillRunningVellum;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    KillRunningVellum;
end;
