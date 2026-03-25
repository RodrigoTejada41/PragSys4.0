param(
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8000
)

$env:APP_HOST = $HostAddress
$env:APP_PORT = "$Port"
$env:ALLOW_REMOTE_ACCESS = "false"
$env:APP_RELOAD = "true"

& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host $HostAddress --port $Port --reload
