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

# Use venv-local python explicitly (service/runner PATH can be weird)
$Py = Join-Path $VenvDir 'Scripts\python.exe'

# Ensure pip exists inside venv
& $Py -m ensurepip --upgrade
& $Py -m pip install -U pip setuptools wheel

# Ensure pip exists inside the venv (Windows can be missing pip)
python -m ensurepip --upgrade

# (moved to venv-local $Py pip bootstrap)

if ($Profile -eq "base") {
  & $Py -m pip install -e '.[base]'
}
elseif ($Profile -eq "base_full") {
  & $Py -m pip install -e '.[base,security,embeddings,faiss,ingest,test]'
}
else {
  throw "Unknown profile: $Profile"
}

& $Py -m compileall src
& $Py -m pip install pytest pytest-asyncio pytest-mock

& $Py -m pytest -q

Write-Host "OK: install + compile + tests" -ForegroundColor Green
