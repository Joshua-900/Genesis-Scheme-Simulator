param([long]$Seed = 7, [ValidateSet('Silk','Estuary','Filigree')][string]$Preset = 'Silk',
      [switch]$Membrane, [int]$Size = 512, [int]$Agents = 90000)
$ErrorActionPreference = 'Stop'
$PhysarumRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PhysarumPython = Join-Path $PhysarumRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $PhysarumPython)) {
    throw 'The project .venv is missing. Install the project requirements first.'
}
Set-Location $PhysarumRoot
$env:OPENBLAS_NUM_THREADS = '1'
if ($Membrane) {
    & $PhysarumPython -B -m src.physarum_lab.adapters.membrane_studio --seed $Seed
    exit $LASTEXITCODE
}
& $PhysarumPython -B -m src.physarum_lab --seed $Seed --preset $Preset --size $Size --agents $Agents
exit $LASTEXITCODE
