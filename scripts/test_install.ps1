\
Param(
  [ValidateSet("base","base_full")]
  [string]$Profile = "base"
)

Write-Host "== AI Agent Hub V3 :: test_install.ps1 ==" -ForegroundColor Cyan
Write-Host "Profile: $Profile"

$WorkDir = Get-Location
$VenvDir = Join-Path $WorkDir ".venv_test_install_$Profile"

if (Test-Path $VenvDir) { Remove-Item -Recurse -Force $VenvDir }

python -m venv $VenvDir
& (Join-Path $VenvDir "Scripts\Activate.ps1")

python -m pip install -U pip setuptools wheel

if ($Profile -eq "base") {
  python -m pip install -e ".[base]"
}
elseif ($Profile -eq "base_full") {
  python -m pip install -e ".[base,security,embeddings,faiss,ingest,test]"
}
else {
  throw "Unknown profile: $Profile"
}

python -m compileall src
pytest -q

Write-Host "OK: install + compile + tests" -ForegroundColor Green
