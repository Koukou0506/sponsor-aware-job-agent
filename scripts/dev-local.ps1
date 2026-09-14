$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:APP_MODE = "local"
$env:PYTHONPATH = "$Root/src"
if (-not $env:NEXT_PUBLIC_API_BASE_URL) { $env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000" }
if (-not (Test-Path "$Root/apps/web/node_modules")) { throw "apps/web/node_modules missing; run npm install in apps/web first" }
$Api = Start-Process python -ArgumentList @("-m","uvicorn","job_agent.api.app:app","--host","127.0.0.1","--port","8000") -PassThru -NoNewWindow
$Web = Start-Process npm -WorkingDirectory "$Root/apps/web" -ArgumentList @("run","dev","--","--hostname","127.0.0.1","--port","3000") -PassThru -NoNewWindow
Write-Host "API PID: $($Api.Id) | Web PID: $($Web.Id)"
try { Wait-Process -Id $Api.Id,$Web.Id } finally { Stop-Process -Id $Api.Id,$Web.Id -ErrorAction SilentlyContinue }
