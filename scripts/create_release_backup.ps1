param(
    [string]$Version = "4.1",
    [string]$OutputName = ""
)

$ErrorActionPreference = "Stop"

$releaseDir = Join-Path "release" ("SysPragas-" + $Version)
if (-not (Test-Path $releaseDir)) {
    throw "Release directory not found: $releaseDir"
}

if ([string]::IsNullOrWhiteSpace($OutputName)) {
    $OutputName = "SysPragas-$Version-backup.zip"
}

$outputPath = Join-Path $releaseDir $OutputName
if (Test-Path $outputPath) {
    Remove-Item -Force $outputPath
}

$stagingDir = Join-Path $releaseDir "__backup_staging__"
if (Test-Path $stagingDir) {
    Remove-Item -Recurse -Force $stagingDir
}

New-Item -ItemType Directory -Path $stagingDir | Out-Null

$dirs = @("app","assets","assinaturas","assinaturas_tecnicas","certificado","docs","modelo","modelos","scripts","services","tests","XSD")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Copy-Item -Recurse -Force $dir $stagingDir
    }
}

$files = @(".dockerignore",".editorconfig",".env.example",".env.sefaz-homologacao.example",".gitignore","AGENTS.md","CHANGELOG.md","CONTRIBUTING.md","docker-compose.yml","Dockerfile","pyproject.toml","README.md","render.yaml","SysPragas-Teste.spec","VERSION")
foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item -Force $file $stagingDir
    }
}

Compress-Archive -Path (Join-Path $stagingDir '*') -DestinationPath $outputPath
Remove-Item -Recurse -Force $stagingDir

Write-Output "Backup created at $outputPath"
