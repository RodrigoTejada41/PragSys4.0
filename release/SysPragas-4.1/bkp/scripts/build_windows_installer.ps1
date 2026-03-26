$ErrorActionPreference = "Stop"

$projectRoot = "E:\Projetos\Controle_de_pragas1.1"
$issPath = Join-Path $projectRoot "scripts\SysPragas-Teste.iss"
$iscc = Get-Command ISCC -ErrorAction SilentlyContinue

if (-not $iscc) {
    Write-Host "ISCC (Inno Setup) nao encontrado no PATH." -ForegroundColor Yellow
    Write-Host "Instale o Inno Setup e execute este script novamente para gerar o instalador."
    exit 1
}

& $iscc.Source $issPath

Write-Host ""
Write-Host "Instalador gerado em: $projectRoot\dist\installer" -ForegroundColor Green
