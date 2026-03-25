param(
  [string]$HostAddress = "0.0.0.0",
  [int]$Port = 8000
)

$env:APP_HOST = $HostAddress
$env:APP_PORT = "$Port"
$env:ALLOW_REMOTE_ACCESS = "true"
$env:APP_RELOAD = "false"

& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host $HostAddress --port $Port
