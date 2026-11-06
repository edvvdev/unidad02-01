"""Auditoria del corpus: imprime el resumen y guarda los artefactos en reports/.

Artefactos generados:
  reports/audit_summary.json    resumen numerico de la auditoria
  reports/audit_table.csv       tabla por columna (tipo, nulos, unicos, ejemplo)
  reports/audit_duplicates.csv  textos duplicados con su conteo y etiquetas
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pandas as pd

from inf8239_u02.config import ROOT, settings
from inf8239_u02.data import (
    duplicate_report,
    load_dataset,
    normalize_text_key,
    sha256,
    validate_dataframe,
)

REPORTS = ROOT / "reports"


def build_summary(df: pd.DataFrame) -> dict:
    text_column = settings.text_column
    target_column = settings.target_column
    text = df[text_column].astype(str)
    lengths = text.str.len()
    words = text.str.split().str.len()
    classes = df[target_column].value_counts(dropna=False)
    duplicates = duplicate_report(df, text_column, target_column, "source")
    normalized = normalize_text_key(text)
    archive_path = settings.dataset_path.parent / "dataset.zip"
    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_path": str(settings.dataset_path.relative_to(ROOT)),
        "dataset_sha256": sha256(settings.dataset_path),
        "archive_path": (
            str(archive_path.relative_to(ROOT)) if archive_path.exists() else None
        ),
        "archive_sha256": sha256(archive_path) if archive_path.exists() else None,
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "nulls": {column: int(value) for column, value in df.isna().sum().items()},
        "empty_texts": int(text.str.strip().eq("").sum()),
        "classes": int(df[target_column].nunique(dropna=True)),
        "class_distribution": {
            str(key): {"count": int(value), "share": round(float(value) / len(df), 6)}
            for key, value in classes.items()
        },
        "duplicate_rows_exact": int(text.duplicated().sum()),
        "duplicate_groups_exact": len(duplicates),
        "duplicate_rows_normalized": int(normalized.duplicated().sum()),
        "rows_after_deduplication": int(len(df) - text.duplicated().sum()),
        "text_length_chars": {
            "min": int(lengths.min()),
            "mean": round(float(lengths.mean()), 2),
            "p50": float(lengths.quantile(0.50)),
            "p90": float(lengths.quantile(0.90)),
            "p99": float(lengths.quantile(0.99)),
            "max": int(lengths.max()),
        },
        "text_length_words": {
            "min": int(words.min()),
            "mean": round(float(words.mean()), 2),
            "p50": float(words.quantile(0.50)),
            "p90": float(words.quantile(0.90)),
            "p99": float(words.quantile(0.99)),
            "max": int(words.max()),
        },
    }
    if "source" in df.columns:
        summary["source_distribution"] = {
            str(key): int(value) for key, value in df["source"].value_counts().items()
        }
    if not duplicates.empty:
        summary["duplicate_rows_in_groups"] = int(duplicates["occurrences"].sum())
        summary["duplicates_with_conflicting_label"] = int(duplicates["conflicting_label"].sum())
    return summary


def build_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.columns:
        series = df[column]
        example = series.dropna().astype(str).iloc[0] if series.notna().any() else ""
        rows.append({
            "columna": column,
            "tipo": str(series.dtype),
            "filas": len(series),
            "no_nulos": int(series.notna().sum()),
            "nulos": int(series.isna().sum()),
            "valores_unicos": int(series.nunique(dropna=True)),
            "ejemplo": example[:120],
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = load_dataset()
    validate_dataframe(df, settings.text_column, settings.target_column)
    summary = build_summary(df)
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    build_table(df).to_csv(REPORTS / "audit_table.csv", index=False)
    duplicates = duplicate_report(df, settings.text_column, settings.target_column, "source")
    duplicates.to_csv(REPORTS / "audit_duplicates.csv", index=False)
    text = df[settings.text_column].astype(str)
    print("Ruta:", settings.dataset_path)
    print("SHA-256:", summary["dataset_sha256"])
    print("Filas y columnas:", df.shape)
    print("Nulos:\n", df[[settings.text_column, settings.target_column]].isna().sum())
    print("Duplicados de texto:", summary["duplicate_rows_exact"])
    print("Distribución:\n", df[settings.target_column].value_counts(dropna=False, normalize=True))
    print("Longitud de textos:\n", text.str.len().describe(percentiles=[0.5, 0.9, 0.99]))
    print("\nArtefactos guardados en reports/: audit_summary.json, audit_table.csv, "
          "audit_duplicates.csv")


if __name__ == "__main__":
    main()
