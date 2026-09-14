$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Find-Python {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        try {
            $version = & $candidate.Exe @($candidate.Args) -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $version) {
                $parts = $version.Trim().Split('.')
                if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 12)) {
                    return $candidate
                }
            }
        } catch {}
    }
    throw "Python 3.12 or newer was not found. Install 64-bit Python 3.12+ and run this installer again."
}

Write-Host "[1/7] Locating Python 3.12+..."
$Python = Find-Python

Write-Host "[2/7] Creating local virtual environment..."
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $Python.Exe @($Python.Args) -m venv .venv
}
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

Write-Host "[3/7] Installing the application and runtime dependencies..."
& $VenvPython -m pip install --upgrade pip setuptools wheel
& $VenvPython -m pip install -e ".[all]"

Write-Host "[4/7] Installing Playwright Chromium..."
try {
    & $VenvPython -m playwright install chromium
} catch {
    Write-Warning "Playwright Chromium could not be downloaded. Job scanning and the UI can still work, but browser autofill needs Chromium. See README_ZH.md for the fallback command."
}

Write-Host "[5/7] Creating local configuration without overwriting existing files..."
New-Item -ItemType Directory -Force "config\local" | Out-Null
Get-ChildItem "config\examples\*.yaml" | ForEach-Object {
    $target = Join-Path "config\local" $_.Name
    if (-not (Test-Path $target)) { Copy-Item $_.FullName $target }
}
New-Item -ItemType Directory -Force "config\local\registries", "data", "artifacts", "browser_profiles\default" | Out-Null
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Write-Host "[6/7] Initialising the local SQLite database..."
& (Join-Path $Root ".venv\Scripts\alembic.exe") upgrade head

Write-Host "[7/7] Running health checks..."
& (Join-Path $Root ".venv\Scripts\job-agent.exe") doctor
& (Join-Path $Root ".venv\Scripts\job-agent.exe") evaluate-golden "tests\golden\jobs\synthetic"

Write-Host ""
Write-Host "Installation finished. Next: edit config\local, then run scripts\windows\02_START_UI.bat." -ForegroundColor Green
