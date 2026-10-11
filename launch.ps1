param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Venv = Join-Path $Root ".venv"
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$TempDir = Join-Path $Root ".tmp"

function Get-BasePython {
    $candidates = @(
        @("py", "-3.12"),
        @("python", ""),
        @("python3", "")
    )

    foreach ($candidate in $candidates) {
        $command = $candidate[0]
        $arg = $candidate[1]
        try {
            if ($arg) {
                & $command $arg --version *> $null
            } else {
                & $command --version *> $null
            }
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }

    throw "Python was not found. Install Python 3.12 or newer from https://www.python.org/downloads/ and re-run launch.ps1."
}

function Invoke-BasePython {
    param(
        [string[]]$Arguments
    )

    $base = Get-BasePython
    if ($base[1]) {
        & $base[0] $base[1] @Arguments
    } else {
        & $base[0] @Arguments
    }
}

function Test-Venv {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        return $false
    }

    & $VenvPython --version *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    & $VenvPython -m pip --version *> $null
    return $LASTEXITCODE -eq 0
}

New-Item -ItemType Directory -Force $TempDir | Out-Null
$env:TEMP = $TempDir
$env:TMP = $TempDir

if (-not (Test-Venv)) {
    if (Test-Path -LiteralPath $Venv) {
        $backup = Join-Path $Root (".venv-broken-" + (Get-Date -Format "yyyyMMddHHmmss"))
        Write-Host "Existing .venv is not usable; moving it to $backup"
        Move-Item -LiteralPath $Venv -Destination $backup
    }

    Write-Host "Creating local Python environment in .venv..."
    Invoke-BasePython @("-m", "venv", ".venv")
}

if (-not (Test-Venv)) {
    Write-Host "Repairing pip in .venv..."
    & $VenvPython -m ensurepip --upgrade --default-pip
}

if (-not $SkipInstall) {
    Write-Host "Installing dependencies from requirements.txt..."
    & $VenvPython -m pip install -r requirements.txt
}

Write-Host ""
Write-Host "Starting GenesisScheme launcher..."
Write-Host "Open http://127.0.0.1:5000/ if your browser does not open automatically."
& $VenvPython launcher.py
