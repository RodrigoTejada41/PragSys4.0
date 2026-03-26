#define MyAppName "SysPragas Teste"
#define MyAppVersion "3.1.0"
#define MyAppPublisher "MoviSys Tecnologia"
#define MyAppExeName "SysPragas-Teste.exe"
#define MyAppSourceDir "E:\Projetos\Controle_de_pragas1.1\dist\SysPragas-Teste"
#define MyAppIconFile "E:\Projetos\Controle_de_pragas1.1\assets\icons\syspragas.ico"

[Setup]
AppId={{E44F43A5-A1D0-4FCE-A53A-0A6581B6D121}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SysPragas Teste
DefaultGroupName=SysPragas Teste
DisableProgramGroupPage=yes
OutputDir=E:\Projetos\Controle_de_pragas1.1\dist\installer
OutputBaseFilename=SysPragas-Teste-Setup-3.1.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
#ifexist "{#MyAppIconFile}"
SetupIconFile={#MyAppIconFile}
#endif

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SysPragas Teste"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\SysPragas Teste"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir SysPragas Teste"; Flags: nowait postinstall skipifsilent
