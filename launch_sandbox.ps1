param([long]$Seed = 1, [switch]$Trails)
$ErrorActionPreference = 'Stop'
$SandboxRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SandboxPython = Join-Path $SandboxRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $SandboxPython)) {
    throw 'The project .venv is missing. Set up the existing project environment first.'
}
Set-Location $SandboxRoot
$env:GENESIS_USE_CUPY = 'False'
$env:OPENBLAS_NUM_THREADS = '1'
if ($Trails) {
    & $SandboxPython -B -m src.genesis_sandbox --seed $Seed --trails
    exit $LASTEXITCODE
}
& $SandboxPython -B -m src.genesis_sandbox --seed $Seed
exit $LASTEXITCODE
