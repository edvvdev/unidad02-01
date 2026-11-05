from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd

from .config import settings

SENTIMENT_ARCHIVE_MEMBERS = {
    "imdb": "imdb_labelled.txt",
    "amazon_cells": "amazon_cells_labelled.txt",
    "yelp": "yelp_labelled.txt",
}
VALID_SCORES = ("0", "1")
NORMALIZED_COLUMNS = ["sentence", "score", "source"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_labelled_lines(raw: str, source: str) -> tuple[list[dict], list[dict]]:
    """Convierte el formato ``frase<TAB>etiqueta`` de UCI en filas tabulares.

    Dos detalles del archivo crudo condicionan esta funcion:

    1. La separacion se hace por el ULTIMO tabulador. El archivo de IMDb
       contiene comillas dobles dentro del texto; un lector CSV con comillas
       las interpreta como delimitadores y descarta filas validas.
    2. El corte de linea es solo ``\n``. El archivo de IMDb contiene dos
       caracteres U+0085 (NEXT LINE) dentro de frases; ``str.splitlines()``
       los trata como saltos de linea y separa la etiqueta de su frase,
       dejando dos registros huerfanos. Aqui se dividen por ``\n`` y el
       U+0085 se sustituye por un espacio.
    """
    rows: list[dict] = []
    rejected: list[dict] = []
    for number, line in enumerate(raw.split("\n"), start=1):
        if not line.strip():
            continue
        if "\t" not in line:
            rejected.append(
                {"source": source, "line": number, "reason": "sin tabulador", "raw": line[:120]}
            )
            continue
        text, score = line.rsplit("\t", 1)
        text = text.replace("\u0085", " ").replace("\u2028", " ").replace("\u2029", " ").strip()
        score = score.strip()
        if score not in VALID_SCORES:
            rejected.append(
                {"source": source, "line": number, "reason": "etiqueta invalida", "raw": line[:120]}
            )
            continue
        rows.append({"sentence": text, "score": score, "source": source})
    return rows, rejected


def read_sentiment_archive(archive_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee el ZIP de "Sentiment Labelled Sentences" (UCI 331) y lo normaliza."""
    rows: list[dict] = []
    rejected: list[dict] = []
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        for source, filename in SENTIMENT_ARCHIVE_MEMBERS.items():
            member = next((name for name in names if name.endswith(filename)), None)
            if member is None:
                raise FileNotFoundError(f"El archivo ZIP no contiene {filename}")
            raw = archive.read(member).decode("utf-8")
            parsed, discards = parse_labelled_lines(raw, source)
            rows.extend(parsed)
            rejected.extend(discards)
    frame = pd.DataFrame(rows, columns=NORMALIZED_COLUMNS)
    rejects = pd.DataFrame(rejected, columns=["source", "line", "reason", "raw"])
    return frame, rejects


def load_dataset(path: Path | None = None) -> pd.DataFrame:
    selected = path or settings.dataset_path
    if not selected.exists():
        raise FileNotFoundError(f"Dataset no encontrado: {selected}")
    return pd.read_csv(selected)


def validate_dataframe(df: pd.DataFrame, text_column: str, target_column: str) -> None:
    missing = {text_column, target_column} - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")
    if df.empty:
        raise ValueError("El dataset esta vacio")
    if df[text_column].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("Existen textos vacios")
    if df[target_column].nunique(dropna=True) < 2:
        raise ValueError("Se requieren al menos dos clases")


def normalize_text_key(series: pd.Series) -> pd.Series:
    """Clave de comparacion insensible a mayusculas, acentos y espacios."""
    return (
        series.astype(str)
        .str.lower()
        .str.replace(r"[^a-z0-9]+", " ", regex=True)
        .str.strip()
    )


def duplicate_report(
    df: pd.DataFrame,
    text_column: str,
    target_column: str = "score",
    source_column: str = "source",
) -> pd.DataFrame:
    """Textos repetidos con su conteo, etiquetas y procedencias."""
    columns = [text_column, "occurrences", "scores", "sources", "conflicting_label"]
    frame = df.copy()
    frame["occurrences"] = frame.groupby(text_column)[text_column].transform("size")
    duplicates = frame[frame["occurrences"] > 1]
    if duplicates.empty:
        return pd.DataFrame(columns=columns)
    records = []
    for text, group in duplicates.groupby(text_column, sort=False):
        scores = sorted({str(value) for value in group[target_column]}) if target_column in group else []
        sources = sorted({str(value) for value in group[source_column]}) if source_column in group else []
        records.append(
            {
                text_column: text,
                "occurrences": int(group["occurrences"].max()),
                "scores": "|".join(scores),
                "sources": "|".join(sources),
                "conflicting_label": len(scores) > 1,
            }
        )
    summary = pd.DataFrame.from_records(records, columns=columns)
    return summary.sort_values("occurrences", ascending=False).reset_index(drop=True)


def drop_duplicate_texts(df: pd.DataFrame, text_column: str) -> pd.DataFrame:
    """Elimina textos repetidos conservando la primera aparicion.

    Se aplica ANTES de la particion train/test para que ningun texto duplicado
    aparezca en ambos lados y las metricas no se inflen artificialmente.
    """
    return df.drop_duplicates(subset=[text_column], keep="first").reset_index(drop=True)
