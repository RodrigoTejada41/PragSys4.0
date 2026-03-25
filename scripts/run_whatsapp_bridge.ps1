param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 3100
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$bridgeRoot = Join-Path $projectRoot "services\whatsapp-bridge"

if (-not (Test-Path $bridgeRoot)) {
    throw "Diretorio do WhatsApp Bridge nao encontrado: $bridgeRoot"
}

Push-Location $bridgeRoot
try {
    $env:WHATSAPP_BRIDGE_HOST = $HostAddress
    $env:WHATSAPP_BRIDGE_PORT = [string]$Port
    if (-not $env:WHATSAPP_BRIDGE_API_KEY) {
        $env:WHATSAPP_BRIDGE_API_KEY = "syspragas-local-key"
    }
    if (-not (Test-Path (Join-Path $bridgeRoot "node_modules"))) {
        & npm.cmd install
    }
    & node src/server.js
}
finally {
    Pop-Location
}
