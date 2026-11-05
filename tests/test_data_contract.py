import json
import os
from pathlib import Path

import pandas as pd
import pytest

from inf8239_u02.config import ROOT, settings
from inf8239_u02.data import (
    drop_duplicate_texts,
    duplicate_report,
    load_dataset,
    parse_labelled_lines,
    sha256,
    validate_dataframe,
)

DATASET = ROOT / "data/raw/dataset.csv"
AUDIT = ROOT / "reports/audit_summary.json"

pytestmark_data = pytest.mark.skipif(
    not DATASET.exists(),
    reason=(
        "El corpus no esta descargado. Ejecute `uv run python scripts/download_data.py` "
        "antes de ejecutar el contrato de datos."
    ),
)


def test_accepts_valid_dataframe():
    df = pd.DataFrame({"text": ["uno", "dos"], "label": ["a", "b"]})
    validate_dataframe(df, "text", "label")


def test_rejects_missing_target():
    df = pd.DataFrame({"text": ["uno"]})
    with pytest.raises(ValueError, match="Faltan columnas"):
        validate_dataframe(df, "text", "label")


def test_rejects_empty_text():
    df = pd.DataFrame({"text": [""], "label": ["a"]})
    with pytest.raises(ValueError, match="textos vacios"):
        validate_dataframe(df, "text", "label")


def test_rejects_single_class():
    df = pd.DataFrame({"text": ["uno", "dos"], "label": ["a", "a"]})
    with pytest.raises(ValueError, match="al menos dos clases"):
        validate_dataframe(df, "text", "label")


def test_parser_keeps_quoted_and_broken_records():
    """El separador es el ULTIMO tabulador y el corte de linea es solo \\n.

    Una frase con comillas dobles y una frase con un salto de linea incrustado
    (U+0085) deben conservarse con su etiqueta.
    """
    raw = 'A "great" movie.\t1\nbroken\u0085line here\t0\nno tab line\n'
    rows, rejected = parse_labelled_lines(raw, "imdb")
    assert len(rows) == 2
    assert [row["score"] for row in rows] == ["1", "0"]
    assert rows[0]["sentence"] == 'A "great" movie.'
    assert rows[1]["sentence"] == "broken line here"
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "sin tabulador"


def test_drop_duplicate_texts_removes_repeats():
    df = pd.DataFrame({"text": ["a", "b", "a"], "label": ["0", "1", "0"]})
    cleaned = drop_duplicate_texts(df, "text")
    assert len(cleaned) == 2
    assert cleaned["text"].tolist() == ["a", "b"]


def test_duplicate_report_counts_occurrences():
    df = pd.DataFrame({"text": ["a", "a", "b"], "score": ["0", "0", "1"], "source": ["x", "x", "y"]})
    report = duplicate_report(df, "text", "score", "source")
    assert report.loc[report["text"] == "a", "occurrences"].item() == 2
    assert bool(report.loc[report["text"] == "a", "conflicting_label"].item()) is False


@pytestmark_data
def test_dataset_has_the_documented_columns():
    df = load_dataset()
    assert settings.text_column in df.columns
    assert settings.target_column in df.columns
    assert len(df) >= 500


@pytestmark_data
def test_dataset_has_at_least_two_classes():
    df = load_dataset()
    assert df[settings.target_column].nunique() >= 2


@pytestmark_data
def test_dataset_has_no_nulls_and_no_empty_texts():
    df = load_dataset()
    assert int(df.isna().sum().sum()) == 0
    assert int(df[settings.text_column].astype(str).str.strip().eq("").sum()) == 0


@pytestmark_data
def test_dataset_has_no_duplicate_texts_after_deduplication():
    df = load_dataset()
    cleaned = drop_duplicate_texts(df, settings.text_column)
    assert int(cleaned[settings.text_column].duplicated().sum()) == 0
    assert len(cleaned) < len(df)


@pytestmark_data
def test_dataset_hash_matches_the_audit_report():
    df = load_dataset()
    summary = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert summary["dataset_sha256"] == sha256(DATASET)
    assert summary["rows"] == len(df)
    assert summary["classes"] == int(df[settings.target_column].nunique())


@pytestmark_data
def test_audit_declares_the_duplicates_found():
    df = load_dataset()
    summary = json.loads(AUDIT.read_text(encoding="utf-8"))
    observed = int(df[settings.text_column].astype(str).duplicated().sum())
    assert summary["duplicate_rows_exact"] == observed
    assert summary["rows_after_deduplication"] == len(df) - observed


@pytestmark_data
def test_configuration_uses_relative_paths_only():
    """La ruta configurada debe ser relativa y resolverse dentro del proyecto."""
    configured = os.getenv("DATASET_PATH", "")
    assert configured
    assert not Path(configured).is_absolute()
    assert settings.dataset_path.is_relative_to(ROOT)
    assert settings.dataset_url.startswith("https://")
    assert "C:\\" not in settings.dataset_url
