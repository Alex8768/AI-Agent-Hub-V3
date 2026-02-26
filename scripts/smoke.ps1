[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

param(
    [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "== AI Agent Hub V3 :: Windows Smoke =="
Write-Host "BASE_URL=$BaseUrl"
Write-Host ""

function Fail($msg) {
    Write-Host "❌ $msg"
    exit 1
}

function CurlJson($url, $method="GET", $body=$null) {
    if ($body) {
        return curl.exe -sS -H "Content-Type: application/json" --data-binary $body $url
    } else {
        return curl.exe -sS $url
    }
}

# 1) Health
Write-Host "1) Health"
$health = CurlJson "$BaseUrl/health"
if (-not $health) { Fail "Health failed" }
Write-Host "OK"

# 2) Documents list
Write-Host "2) List documents"
$docs = CurlJson "$BaseUrl/api/v1/documents"
Write-Host $docs

# 3) Search
Write-Host "3) Search"
$searchBody = '{"query":"foxes","k":3}'
$search = CurlJson "$BaseUrl/api/v1/search" "POST" $searchBody
Write-Host $search

Write-Host ""
Write-Host "✅ SMOKE PASSED"
