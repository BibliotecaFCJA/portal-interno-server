$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv-1\Scripts\python.exe"
$app = Join-Path $PSScriptRoot "app.py"

if (-not (Test-Path $python -PathType Leaf)) {
    throw "Python do ambiente virtual não encontrado: $python"
}

if (-not (Test-Path $app -PathType Leaf)) {
    throw "Aplicativo não encontrado: $app"
}

while ($true) {
    $portaEmUso = @(
        Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue
    ).Count -gt 0
    if ($portaEmUso) {
        Start-Sleep -Seconds 5
        continue
    }

    & $python $app
    $exitCode = $LASTEXITCODE
    Write-Output "O servidor encerrou com código $exitCode. Nova tentativa em 5 segundos."
    Start-Sleep -Seconds 5
}
