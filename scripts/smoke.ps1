[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

# Windows-safe smoke: NO param() (PowerShell 5.1 parser friendliness)
if (-not $env:BASE_URL -or $env:BASE_URL.Trim() -eq "") {
  $env:BASE_URL = "http://localhost:8000"
}
$BaseUrl = $env:BASE_URL

Write-Host "== AI Agent Hub V3 :: Windows Smoke =="
Write-Host "BASE_URL=$BaseUrl"
Write-Host ""

function Fail($msg) {
  Write-Host "❌ $msg"
  exit 1
}

function CurlCode([string]$url, [string]$method="GET") {
  $code = & curl.exe -sS -o NUL -w "%{http_code}" -X $method $url
  return $code
}

function CurlJson([string]$url, [string]$method="GET", [string]$body=$null) {
  if ($body) {
    return & curl.exe -sS -H "Content-Type: application/json" --data-binary $body -X $method $url
  }
  return & curl.exe -sS -X $method $url
}

Write-Host "1) Health"
$code = CurlCode "$BaseUrl/health"
if ($code -ne "200") { Fail "Health failed (HTTP $code)" }
Write-Host "   ✅ /health OK"

Write-Host "2) Documents list"
$docs = CurlJson "$BaseUrl/api/v1/documents"
Write-Host $docs

Write-Host "3) Upload (dedup)"
$tmp = Join-Path $env:TEMP "ai-agent-hub-smoke"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$file = Join-Path $tmp "smoke.txt"
"This is a smoke document about foxes and dogs." | Set-Content -Encoding utf8 $file

$upload1 = & curl.exe -sS -F ("file=@{0};type=text/plain" -f $file) "$BaseUrl/api/v1/documents/upload"
$docId1 = ($upload1 | python scripts/jsonutil.py get id)
Write-Host "   upload#1 id=$docId1"

$upload2 = & curl.exe -sS -F ("file=@{0};type=text/plain" -f $file) "$BaseUrl/api/v1/documents/upload"
$docId2 = ($upload2 | python scripts/jsonutil.py get id)
Write-Host "   upload#2 id=$docId2"

if ($docId1 -ne $docId2) { Fail "Dedup failed: ids differ" }
Write-Host "   ✅ Dedup OK"

Write-Host "4) Search"

# Write JSON to file (UTF-8 without BOM) to avoid PowerShell quoting issues
$searchJsonPath = Join-Path $tmp "search.json"
$searchBody = '{"query":"foxes","k":3,"include_metadata":false}'
[System.IO.File]::WriteAllText($searchJsonPath, $searchBody, [System.Text.UTF8Encoding]::new($false))

$search = & curl.exe -sS -H "Content-Type: application/json" --data-binary "@$searchJsonPath" "$BaseUrl/api/v1/search"
$count = ($search | python scripts/jsonutil.py len)
Write-Host "   results: $count"
if ([int]$count -lt 1) {
  Write-Host $search
  Fail "Search returned no results"
}
Write-Host "   ✅ Search OK"

Write-Host "5) Export"

# Write JSON to file (UTF-8 without BOM) to avoid PowerShell quoting issues
$exportJsonPath = Join-Path $tmp "export.json"
$exportBody = '{"content":"Hello export world!","format":"pdf"}'
[System.IO.File]::WriteAllText($exportJsonPath, $exportBody, [System.Text.UTF8Encoding]::new($false))

$export = & curl.exe -sS -H "Content-Type: application/json" --data-binary "@$exportJsonPath" "$BaseUrl/api/v1/export"
$exportId = ($export | python scripts/jsonutil.py export_id)
if (-not $exportId) {
  Write-Host $export
  Fail "Export did not return export_id"
}
Write-Host "   export_id=$exportId"

$dl = Join-Path $tmp "export.pdf"
$code = & curl.exe -sS -o $dl -w "%{http_code}" "$BaseUrl/api/v1/export/$exportId/download"
if ($code -ne "200") { Fail "Export download failed (HTTP $code)" }
Write-Host "   ✅ Export OK"

Write-Host "✅ SMOKE PASSED"
Write-Host "✅ SMOKE PASSED"
