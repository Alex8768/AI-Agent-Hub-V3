# scripts/run_and_smoke.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

param(
  [string]$HostIp = "127.0.0.1",
  [int]$Port = 0,
  [int]$HealthTimeoutSec = 25
)

function Get-FreePort {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  $p = $listener.LocalEndpoint.Port
  $listener.Stop()
  return $p
}
if ($Port -eq 0) { $Port = Get-FreePort }

$ErrorActionPreference = "Stop"
$baseUrl = "http://$HostIp`:$Port"
$env:BASE_URL = $baseUrl

function Fail($msg) {
  Write-Host "❌ $msg"
  exit 1
}

function Wait-Health([string]$url, [int]$timeoutSec) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $code = & curl.exe -sS -o NUL -w "%{http_code}" "$url/health"
      if ($code -eq "200") { return $true }
    } catch { }
    Start-Sleep -Milliseconds 350
  }
  return $false
}

Write-Host "== AI Agent Hub V3 :: Run + Smoke (Windows) =="
Write-Host "BASE_URL=$baseUrl"
Write-Host ""

# Start uvicorn in background
$uvicornArgs = "src.api.main:app --host $HostIp --port $Port"
$proc = Start-Process -FilePath "uvicorn" -ArgumentList $uvicornArgs -PassThru -WindowStyle Hidden

try {
  Write-Host "1) Starting server (uvicorn pid=$($proc.Id))"
  $ok = Wait-Health -url $baseUrl -timeoutSec $HealthTimeoutSec
  if (-not $ok) {
    Fail "Server did not become healthy within $HealthTimeoutSec seconds"
  }
  Write-Host "   ✅ /health is ready"
  Write-Host ""

  Write-Host "2) Running smoke.ps1"
  & "$PSScriptRoot\smoke.ps1"
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    Fail "smoke.ps1 failed with exit code $code"
  }

  Write-Host ""
  Write-Host "✅ Run + Smoke PASSED"
  exit 0
}
finally {
  try {
    if (-not $proc.HasExited) {
      Stop-Process -Id $proc.Id -Force
      Start-Sleep -Milliseconds 300
    }
  } catch { }
}
