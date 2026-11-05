"""Descarga verificable del corpus elegido y normalizacion a data/raw/dataset.csv.

Modos admitidos (segun DATA_SOURCE en .env):
  * local: usa el archivo local configurado en DATASET_PATH.
  * url  : descarga un CSV publico o un ZIP de UCI, verifica su SHA-256,
           lo normaliza y escribe el manifiesto de procedencia.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import requests

from inf8239_u02.config import ROOT, settings
from inf8239_u02.data import read_sentiment_archive, sha256


def write_manifest(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def download_plain_csv(url: str) -> int:
    output = ROOT / "data/raw/dataset.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    output.write_bytes(response.content)
    print(f"Guardado: {output}")
    print(f"SHA-256: {sha256(output)}")
    return 0


def download_zip_corpus(url: str) -> int:
    raw_dir = ROOT / "data/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive_path = raw_dir / "dataset.zip"
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    archive_path.write_bytes(response.content)
    digest = sha256(archive_path)
    print(f"ZIP descargado: {archive_path}")
    print(f"SHA-256 del ZIP: {digest}")
    expected = settings.dataset_sha256.strip().lower()
    if expected:
        if digest != expected:
            print(
                "ERROR: el SHA-256 descargado no coincide con DATASET_SHA256 "
                f"({expected}). No se normaliza el archivo.",
                file=sys.stderr,
            )
            return 3
        print("SHA-256 verificado contra DATASET_SHA256.")
    else:
        print("AVISO: DATASET_SHA256 vacio; el hash queda registrado como referencia.")
    frame, rejects = read_sentiment_archive(archive_path)
    output = raw_dir / "dataset.csv"
    frame.to_csv(output, index=False)
    print(f"Filas normalizadas: {len(frame)}")
    print(f"Columnas: {', '.join(frame.columns)}")
    print(f"Filas descartadas por formato invalido: {len(rejects)}")
    if not rejects.empty:
        rejects.to_csv(raw_dir / "rejected_rows.csv", index=False)
    csv_digest = sha256(output)
    print(f"SHA-256 del CSV normalizado: {csv_digest}")
    manifest = raw_dir / "dataset.source.txt"
    write_manifest(
        manifest,
        [
            f"dataset: {settings.dataset_name or 'Sentiment Labelled Sentences (UCI 331)'}",
            f"dataset_page: {settings.dataset_page}",
            f"download_url: {url}",
            f"license: {settings.dataset_license}",
            f"archive_sha256: {digest}",
            f"normalized_csv_sha256: {csv_digest}",
            f"rows: {len(frame)}",
            f"columns: {','.join(frame.columns)}",
            f"text_column: {settings.text_column}",
            f"target_column: {settings.target_column}",
            f"rejected_rows: {len(rejects)}",
            f"generated_at_utc: {datetime.now(UTC).isoformat(timespec='seconds')}",
            "generator: scripts/download_data.py",
        ],
    )
    print(f"Manifiesto de procedencia: {manifest}")
    return 0


def main() -> int:
    if settings.data_source == "local":
        print(f"Modo local. Archivo configurado: {settings.dataset_path}")
        return 0
    if settings.data_source != "url" or not settings.dataset_url:
        print("Configure DATA_SOURCE=url y DATASET_URL en .env", file=sys.stderr)
        return 2
    url = settings.dataset_url.strip()
    if url.lower().endswith(".zip"):
        return download_zip_corpus(url)
    return download_plain_csv(url)


if __name__ == "__main__":
    raise SystemExit(main())
