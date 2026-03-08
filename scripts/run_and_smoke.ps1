# scripts/run_and_smoke.ps1
param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 0,
  [int]$HealthTimeoutSec = 25
)


# After param() — PowerShell requires param to be first
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

# After param() — allowed
$ErrorActionPreference = "Stop"

function Get-FreePort {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  $p = $listener.LocalEndpoint.Port
  $listener.Stop()
  return $p
}

if ($Port -eq 0) { $Port = Get-FreePort }

$BaseUrl = "http://$BindHost`:$Port"
$env:BASE_URL = $BaseUrl

function Fail($msg) { Write-Host "❌ $msg"; exit 1 }

function Wait-Health([string]$url, [int]$timeoutSec) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $code = & curl.exe -sS -o NUL -w "%{http_code}" "$url/health"
      if ($code -eq "200") { return $true }
    } catch {}
    Start-Sleep -Milliseconds 350
  }
  return $false
}

Write-Host "== AI Agent Hub V3 :: Run + Smoke (Windows) =="
Write-Host "BASE_URL=$BaseUrl"
Write-Host ""

$uvicorn = Start-Process -FilePath "uvicorn" `
  -ArgumentList "src.api.main:app --host $BindHost --port $Port" `
  -PassThru -NoNewWindow

try {
  Write-Host "1) Starting server (pid=$($uvicorn.Id))"
  if (-not (Wait-Health -url $BaseUrl -timeoutSec $HealthTimeoutSec)) {
    Fail "Server did not become healthy within $HealthTimeoutSec seconds"
  }
  Write-Host "   ✅ /health is ready"
  Write-Host ""

  Write-Host "2) Running smoke.ps1"
  & "$PSScriptRoot\smoke.ps1" -BaseUrl $BaseUrl
  if ($LASTEXITCODE -ne 0) { Fail "smoke.ps1 failed" }

  Write-Host ""
  Write-Host "✅ Run + Smoke PASSED"
  exit 0
}
finally {
  try { if (-not $uvicorn.HasExited) { Stop-Process -Id $uvicorn.Id -Force } } catch {}
}