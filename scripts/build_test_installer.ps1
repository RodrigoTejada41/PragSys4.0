param(
    [switch]$InstallPyInstaller
)

$ErrorActionPreference = "Stop"
$projectRoot = "E:\Projetos\Controle_de_pragas1.1"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$specFile = Join-Path $projectRoot "SysPragas-Teste.spec"
$iconOutputFile = Join-Path $projectRoot "assets\icons\syspragas.ico"
$iconCandidates = @(
    (Join-Path $projectRoot "iconemovisys.ico"),
    (Join-Path $projectRoot "iconemovisys.ico.png"),
    $iconOutputFile
)

function Resolve-BuildIcon {
    foreach ($candidate in $iconCandidates) {
        if (-not (Test-Path $candidate)) {
            continue
        }
        if ([System.IO.Path]::GetExtension($candidate).ToLowerInvariant() -eq ".ico") {
            return $candidate
        }
        if ([System.IO.Path]::GetExtension($candidate).ToLowerInvariant() -eq ".png") {
            $iconDir = Split-Path -Parent $iconOutputFile
            if (-not (Test-Path $iconDir)) {
                New-Item -ItemType Directory -Path $iconDir | Out-Null
            }
            & $pythonExe -c "from PIL import Image; import sys; img = Image.open(sys.argv[1]); img.save(sys.argv[2], sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])" $candidate $iconOutputFile
            return $iconOutputFile
        }
    }
    return $null
}

if (-not (Test-Path $pythonExe)) {
    throw "Python da virtualenv nao encontrado em $pythonExe"
}

if ($InstallPyInstaller) {
    & $pythonExe -m pip install pyinstaller
}

$iconFile = Resolve-BuildIcon

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", "SysPragas-Teste",
    "--add-data", "$projectRoot\app\interfaces\web\templates;app\interfaces\web\templates",
    "--add-data", "$projectRoot\app\interfaces\web\static;app\interfaces\web\static",
    "--collect-submodules", "app",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "uvicorn.lifespan.on"
)

if ($iconFile -and (Test-Path $iconFile)) {
    $pyInstallerArgs += @("--icon", $iconFile)
}

$pyInstallerArgs += "$projectRoot\scripts\syspragas_launcher.py"

& $pythonExe $pyInstallerArgs

Write-Host ""
Write-Host "Build concluido." -ForegroundColor Green
Write-Host "Launcher gerado em: $distDir\SysPragas-Teste\SysPragas-Teste.exe"
Write-Host "Arquivos temporarios em: $buildDir"
Write-Host "Spec gerado em: $specFile"
