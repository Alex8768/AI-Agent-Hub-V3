# scripts/smoke.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
param(
    [string]$BaseUrl,
    [string]$TmpDir,
    [int]$DeepHealth = 0,
    [int]$StreamOnce = 1
)

if (-not $BaseUrl) { $BaseUrl = "http://localhost:8000" }
if (-not $TmpDir) { $TmpDir = "$env:TEMP\ai-agent-hub-smoke" }

if ($env:DEEP_HEALTH) {
    $DeepHealth = [int]$env:DEEP_HEALTH
}
if ($env:STREAM_ONCE) {
    $StreamOnce = [int]$env:STREAM_ONCE
}


if (-not $BaseUrl) { $BaseUrl = $env:BASE_URL }
if (-not $TmpDir) { $TmpDir = $env:TEMP + "\ai-agent-hub-smoke" }
if (if ( { [int]  [int]$StreamOnce = $(if ()

if (-not $BaseUrl) { $BaseUrl = "http://localhost:8000" }
if (-not $TmpDir) { $TmpDir = "$env:TEMP\ai-agent-hub-smoke" }

$Api = $BaseUrl

New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

Write-Host "== AI Agent Hub V3 :: Windows Smoke ==" 
Write-Host "BASE_URL=$BaseUrl"
Write-Host ""

function Fail($msg) {
  Write-Host "   ❌ $msg"
  exit 1
}

function CurlCode([string]$url, [string]$method="GET", [string]$outFile="$TmpDir\resp.bin", [string]$dataJson=$null) {
  if (Test-Path $outFile) { Remove-Item -Force $outFile -ErrorAction SilentlyContinue | Out-Null }
  $args = @("-sS", "-o", $outFile, "-w", "%{http_code}", "-X", $method)
  if ($dataJson) {
    $args += @("-H", "Content-Type: application/json", "-d", $dataJson)
  }
  $args += $url
  $code = & curl.exe @args
  return $code
}

function GetJsonChecked([string]$url) {
  $tmp = "$TmpDir\resp.bin"
  $code = CurlCode -url $url -method "GET" -outFile $tmp
  if ($code -ne "200") {
    Write-Host "   ❌ GET $url failed (HTTP $code)"
    Write-Host "   --- body ---"
    if (Test-Path $tmp) { Get-Content -Raw $tmp | Write-Host }
    exit 1
  }
  if (-not (Test-Path $tmp) -or ((Get-Item $tmp).Length -eq 0)) {
    Fail "GET $url returned empty body"
  }
  return (Get-Content -Raw $tmp)
}

function JsonLen([string]$json) {
  return ($json | python scripts/jsonutil.py len)
}

function JsonGet([string]$json, [string]$key) {
  return ($json | python scripts/jsonutil.py get $key)
}

function PyPretty([string]$json) {
  $json | python scripts/jsonutil.py pretty | Write-Host
}

Write-Host "0) Preflight: server reachable?"
$code = CurlCode -url "$Api/health" -method "GET" -outFile "$TmpDir\health.bin"
if ($code -ne "200") {
  Fail "Server not reachable or /health not 200 (HTTP $code). Start: uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
}
Write-Host "   ✅ reachable"
Write-Host ""

Write-Host "1) Health (light)"
$code = CurlCode -url "$Api/health" -method "GET" -outFile "$TmpDir\health.bin"
if ($code -ne "200") { Fail "/health failed (HTTP $code)" }
Write-Host "   ✅ /health OK"

Write-Host "2) Health (deep, optional)"
if ($DeepHealth -eq 1) {
  $code = CurlCode -url "$Api/api/v1/health/deep" -method "GET" -outFile "$TmpDir\deep.bin"
  if ($code -ne "200") { Fail "/api/v1/health/deep failed (HTTP $code)" }
  Write-Host "   ✅ /api/v1/health/deep OK"
} else {
  Write-Host "   ⏭️  skipped (set DEEP_HEALTH=1)"
}

Write-Host "3) Documents list"
$docsJson = GetJsonChecked "$Api/api/v1/documents"
$docsBefore = JsonLen $docsJson
Write-Host "   docs before: $docsBefore"

Write-Host "4) Upload (idempotent / dedup)"
$filePath = Join-Path $TmpDir "smoke.txt"
"This is a smoke document about foxes and dogs." | Set-Content -Encoding utf8 $filePath

# Upload #1
$upload1 = & curl.exe -sS -F ("file=@{0};type=text/plain" -f $filePath) "$Api/api/v1/documents/upload"
$docId1 = JsonGet $upload1 "id"
Write-Host "   upload#1 id=$docId1"

# Upload #2
$upload2 = & curl.exe -sS -F ("file=@{0};type=text/plain" -f $filePath) "$Api/api/v1/documents/upload"
$docId2 = JsonGet $upload2 "id"
Write-Host "   upload#2 id=$docId2"

if ($docId1 -ne $docId2) { Fail "Dedup failed: ids differ" }
Write-Host "   ✅ Dedup OK"

Write-Host "5) Search (snippet mode)"
$bodySearch1 = '{"query":"foxes","k":3,"include_metadata":false}'
$search1 = & curl.exe -sS -H "Content-Type: application/json" --data-binary $bodySearch1 "$Api/api/v1/search"
$count1 = JsonLen $search1
Write-Host "   results: $count1"
if ([int]$count1 -lt 1) {
  Write-Host "   ❌ Search returned no results"
  PyPretty $search1
  exit 1
}
Write-Host "   ✅ Search OK (snippet)"

Write-Host "6) Search (include_content=true)"
$bodySearch2 = '{"query":"foxes","k":1,"include_content":true,"include_metadata":false}'
$search2 = & curl.exe -sS -H "Content-Type: application/json" --data-binary $bodySearch2 "$Api/api/v1/search"
$count2 = JsonLen $search2
if ([int]$count2 -lt 1) {
  Write-Host "   ❌ Search include_content returned no results"
  PyPretty $search2
  exit 1
}
Write-Host "   ✅ Search OK (include_content)"

Write-Host "7) Export (content -> pdf) + download"
$bodyExport = '{"content":"Hello export world!","format":"pdf"}'
$export = & curl.exe -sS -H "Content-Type: application/json" --data-binary $bodyExport "$Api/api/v1/export"
$exportId = ($export | python scripts/jsonutil.py export_id)
if (-not $exportId) {
  Write-Host "   ❌ Export did not return export_id"
  PyPretty $export
  exit 1
}
Write-Host "   export_id=$exportId"

$pdfPath = Join-Path $TmpDir "export.pdf"
$code = & curl.exe -sS -o $pdfPath -w "%{http_code}" "$Api/api/v1/export/$exportId/download"
if ($code -ne "200") { Fail "Export download failed: HTTP $code" }
$size = (Get-Item $pdfPath).Length
Write-Host "   downloaded bytes=$size"
if ($size -lt 500) { Fail "Export PDF too small (unexpected)" }
Write-Host "   ✅ Export OK"

Write-Host "8) Delete document (DB + storage + FAISS purge)"
$code = & curl.exe -sS -o NUL -w "%{http_code}" -X DELETE "$Api/api/v1/documents/$docId1"
if ($code -ne "200") { Fail "Delete failed: HTTP $code" }
Write-Host "   ✅ Delete OK"

Write-Host "9) Get-by-id after delete should 404"
$code = & curl.exe -sS -o NUL -w "%{http_code}" "$Api/api/v1/documents/$docId1"
if ($code -ne "404") { Fail "Expected 404 after delete, got HTTP $code" }
Write-Host "   ✅ Get-by-id 404 OK"

Write-Host "10) Streaming (once mode)"
$streamPath = Join-Path $TmpDir "stream.txt"
$code = & curl.exe -sS -o $streamPath -w "%{http_code}" "$Api/api/v1/stream/test-session?once=$StreamOnce"
Write-Host "   stream http=$code"
if ($code -eq "200") {
  Get-Content $streamPath -TotalCount 5 | ForEach-Object { "   | $_" } | Write-Host
  Write-Host "   ✅ Streaming OK (once)"
} elseif ($code -eq "400") {
  Write-Host "   ⏭️  Streaming disabled (expected in Base)"
} else {
  Fail "Unexpected streaming HTTP $code"
}

$docsAfter = JsonLen (GetJsonChecked "$Api/api/v1/documents")
Write-Host ""
Write-Host "docs after: $docsAfter"
Write-Host "✅ SMOKE PASSED"
