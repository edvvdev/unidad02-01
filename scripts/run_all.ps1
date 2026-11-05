# Pipeline completo del Ejercicio 01 (LAB04 + LAB05) en Windows PowerShell.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> 1/8 Configuracion local (.env a partir de .env.example)"
if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "    .env creado desde .env.example"
} else {
  Write-Host "    .env ya existe; se conserva"
}

Write-Host "==> 2/8 Sincronizacion del entorno (uv sync)"
uv sync

Write-Host "==> 3/8 Descarga verificable del corpus (LAB04)"
uv run python scripts/download_data.py

Write-Host "==> 4/8 Auditoria del corpus (LAB04)"
uv run python scripts/audit_data.py

Write-Host "==> 5/8 Entrenamiento y evaluacion de los tres pipelines (LAB05)"
uv run python scripts/train_text.py

Write-Host "==> 6/8 Ejecucion del notebook con salidas guardadas"
uv run --with jupyter --with nbformat --with ipykernel `
  python -m jupyter nbconvert --to notebook --execute --inplace `
  notebooks/01_ejercicio01_nlp.ipynb

Write-Host "==> 7/8 PDF breve del ejercicio"
$env:REPO_URL = if ($env:REPO_URL) { $env:REPO_URL } else { "https://github.com/edvvdev/unidad02-01" }
uv run --with reportlab python scripts/build_ejercicio01_pdf.py

Write-Host "==> 8/8 Pruebas del proyecto"
uv run pytest -q

Write-Host "Pipeline completo. Artefactos en reports/, models/ y docs/EJERCICIO_01_PDF_BRIEF.pdf"
