$ErrorActionPreference = "Stop"
$RaizProyecto = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Spec = Join-Path $PSScriptRoot "centro_devoluciones.spec"
$Dist = Join-Path $RaizProyecto "dist"

Push-Location $RaizProyecto
try {
    python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath (Join-Path $RaizProyecto "build") $Spec
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "config.example.json") -Destination (Join-Path $Dist "config.json") -Force
    Write-Host "Ejecutable generado en: $(Join-Path $Dist 'CentroDevoluciones.exe')"
} finally {
    Pop-Location
}
