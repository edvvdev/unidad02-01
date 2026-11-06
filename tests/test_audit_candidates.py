"""Pruebas del formato crudo del corpus y de las cifras de los candidatos.

These tests guard the figures published in the README, in the dataset card and in
the PDF: the breakdown of rows lost by a naive CSV reader, and the metrics of
both candidate corpora.
"""

import json

import pytest

from inf8239_u02.config import ROOT

PARSE_AUDIT = ROOT / "reports/parse_audit.json"
CANDIDATES_AUDIT = ROOT / "reports/candidates_audit.json"

pytestmark_audit = pytest.mark.skipif(
    not PARSE_AUDIT.exists() or not CANDIDATES_AUDIT.exists(),
    reason=(
        "Faltan los artefactos de la auditoria. Ejecute "
        "`uv run python scripts/audit_candidates.py` antes de estas pruebas."
    ),
)


@pytestmark_audit
def test_parse_audit_reports_the_loss_per_source():
    audit = json.loads(PARSE_AUDIT.read_text(encoding="utf-8"))
    por_fuente = audit["por_fuente"]
    assert set(por_fuente) == {"imdb", "amazon_cells", "yelp"}
    perdidas = {
        fuente: valores["perdidas_csv_ingenuo_coma"] for fuente, valores in por_fuente.items()
    }
    assert perdidas == {"imdb": 261, "amazon_cells": 225, "yelp": 294}
    assert audit["totales"]["perdidas_csv_ingenuo_coma"] == 780
    assert audit["totales"]["lineas_logicas"] == 3000


@pytestmark_audit
def test_parse_audit_shows_that_the_applied_rule_recovers_every_row():
    audit = json.loads(PARSE_AUDIT.read_text(encoding="utf-8"))
    for valores in audit["por_fuente"].values():
        assert valores["recuperadas_ultimo_tabulador"] == valores["lineas_logicas"]
    assert audit["totales"]["recuperadas_ultimo_tabulador"] == audit["totales"]["lineas_logicas"]


@pytestmark_audit
def test_parse_audit_counts_the_u0085_characters():
    audit = json.loads(PARSE_AUDIT.read_text(encoding="utf-8"))
    assert audit["caracteres_especiales"]["u0085"] == 2


@pytestmark_audit
def test_candidates_audit_matches_the_published_candidate_figures():
    audit = json.loads(CANDIDATES_AUDIT.read_text(encoding="utf-8"))
    descartado = audit["candidato_descartado"]
    assert descartado["filas"] == 5574
    assert descartado["ham"] == 4827
    assert descartado["spam"] == 747
    assert descartado["spam_pct"] == 13.4
    assert descartado["duplicados_exactos"] == 403
    assert descartado["filas_con_7_mas_digitos"] == 419
    assert descartado["filas_con_url_o_correo"] == 113
    assert descartado["filas_con_url_o_arroba"] == 141


@pytestmark_audit
def test_candidates_audit_documents_the_approved_corpus():
    audit = json.loads(CANDIDATES_AUDIT.read_text(encoding="utf-8"))
    aprobado = audit["candidato_aprobado"]
    assert aprobado["filas"] == 3000
    assert aprobado["clases"] == 2
    assert aprobado["distribucion_clases"] == {"0": 1500, "1": 1500}
    assert aprobado["filas_con_url"] == 0
    assert aprobado["filas_con_direccion_correo"] == 0
    assert aprobado["filas_con_7_mas_digitos"] == 0
