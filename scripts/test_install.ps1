Param(
  [ValidateSet("base","base_full")]
  [string]$Profile = "base",
  [string]$PyVersion = "3.12"
)

Write-Host "== AI Agent Hub V3 :: test_install.ps1 ==" -ForegroundColor Cyan
Write-Host "Profile: $Profile"
Write-Host "PyVersion: $PyVersion"

# --- Helpers ---
function Has-PyLauncherVersion([string]$v) {
  try {
    & py "-$v" --version *> $null
    return $true
  } catch { return $false }
}

$UsePy = Has-PyLauncherVersion $PyVersion
if ($UsePy) {
  Write-Host "Using: py -$PyVersion" -ForegroundColor Green
} else {
  Write-Host "ERROR: py -$PyVersion not available for this runner user/service." -ForegroundColor Red
  Write-Host "Run in admin PowerShell on the runner PC:  py -0p" -ForegroundColor Yellow
  exit 1
}

function Invoke-Py {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  if ($UsePy) {
    & py "-$PyVersion" @Args
  } else {
    & python @Args
  }
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# --- Paths ---
$WorkDir = Get-Location
$VenvDir = Join-Path $WorkDir ".venv_test_install_$Profile"
if (Test-Path $VenvDir) { Remove-Item -Recurse -Force $VenvDir }

# --- Create venv with Python 3.12 explicitly ---
Invoke-Py -m venv $VenvDir

# --- Activate ---
& (Join-Path $VenvDir "Scripts\Activate.ps1")

# --- Ensure pip exists inside venv (important on some Windows installs) ---
python -m ensurepip --upgrade

# --- Upgrade tooling ---
python -m pip install -U pip setuptools wheel

# --- Install project editable ---
if ($Profile -eq "base") {
  python -m pip install -e ".[base]"
}
elseif ($Profile -eq "base_full") {
  python -m pip install -e ".[base,security,embeddings,faiss,ingest,test]"
}
else {
  throw "Unknown profile: $Profile"
}

# --- Run checks ---
python -m compileall src

# IMPORTANT: always run pytest via module to avoid PATH issues
python -m pytest -q

Write-Host "OK: install + compile + tests" -ForegroundColor Green
