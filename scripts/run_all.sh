#!/usr/bin/env bash
# Pipeline completo del Ejercicio 01 (LAB04 + LAB05).
# Uso:  bash scripts/run_all.sh
# Es reproducible desde un clon limpio: no necesita pasos manuales.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> 1/8 Configuracion local (.env a partir de .env.example)"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    .env creado desde .env.example"
else
  echo "    .env ya existe; se conserva"
fi

echo "==> 2/8 Sincronizacion del entorno (uv sync)"
uv sync

echo "==> 3/8 Descarga verificable del corpus (LAB04)"
uv run python scripts/download_data.py

echo "==> 4/8 Auditoria del corpus (LAB04)"
uv run python scripts/audit_data.py

echo "==> 5/8 Entrenamiento y evaluacion de los tres pipelines (LAB05)"
uv run python scripts/train_text.py

echo "==> 6/8 Ejecucion del notebook con salidas guardadas"
uv run --with jupyter --with nbformat --with ipykernel \
  python -m jupyter nbconvert --to notebook --execute --inplace \
  notebooks/01_ejercicio01_nlp.ipynb

echo "==> 7/8 PDF breve del ejercicio"
REPO_URL="${REPO_URL:-https://github.com/edvvdev/unidad02-01}" \
  uv run --with reportlab python scripts/build_ejercicio01_pdf.py

echo "==> 8/8 Pruebas del proyecto"
uv run pytest -q

echo
echo "Pipeline completo. Artefactos en reports/, models/ y docs/EJERCICIO_01_PDF_BRIEF.pdf"
