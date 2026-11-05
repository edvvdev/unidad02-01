import json

import pandas as pd
import pytest

from inf8239_u02.config import ROOT
from inf8239_u02.errors import (
    CATEGORY_NAMES,
    annotate_errors,
    categorize_error,
    summarize_by_category,
)
from inf8239_u02.experiment import run_experiment
from inf8239_u02.modeling import build_models

METRICS_JSON = ROOT / "reports/text_metrics.json"
METRICS_CSV = ROOT / "reports/text_metrics.csv"


def test_each_pipeline_predicts_one_label():
    texts = ["excelente servicio", "mala atención", "servicio rápido", "atención lenta"]
    labels = ["positive", "negative", "positive", "negative"]
    for model in build_models().values():
        model.fit(texts, labels)
        assert len(model.predict(["excelente atención"])) == 1
        assert "tfidf" in model.named_steps
        assert "model" in model.named_steps


def test_vectorizer_stays_inside_the_pipeline():
    """El vectorizador debe estar dentro del pipeline para evitar fuga."""
    for model in build_models().values():
        steps = list(model.named_steps)
        assert steps == ["tfidf", "model"]
        assert model.named_steps["tfidf"].__class__.__name__ == "TfidfVectorizer"


def test_experiment_selects_the_best_model_by_macro_f1():
    frame = pd.DataFrame({
        "sentence": [
            "excelente producto muy bueno", "terrible producto muy malo",
            "me encanta la calidad", "horrible la calidad",
            "muy recomendado excelente", "no recomendado horrible",
            "buenissimo servicio", "peisimo servicio",
            "excelente resultado", "horrible resultado",
            "muy bueno excelente", "muy malo horrible",
        ],
        "score": ["1", "0", "1", "0", "1", "0", "1", "0", "1", "0", "1", "0"],
    })
    result = run_experiment(frame, "sentence", "score", random_state=42)
    scores = {name: metrics["f1_macro"] for name, metrics in result.metrics.items()}
    best = max(scores, key=lambda name: (scores[name], result.metrics[name]["accuracy"]))
    assert result.best_model_name == best
    assert result.metrics[result.best_model_name]["f1_macro"] >= result.metrics["dummy"]["f1_macro"]


def test_experiment_deduplicates_before_splitting():
    frame = pd.DataFrame({
        "sentence": [
            "bueno", "bueno", "malo", "malo",
            "excelente", "horrible", "magnifico", "terrible",
        ],
        "score": ["1", "1", "0", "0", "1", "0", "1", "0"],
    })
    result = run_experiment(frame, "sentence", "score", random_state=42)
    assert result.cleaning["filas_duplicadas_eliminadas"] == 2
    assert result.cleaning["filas_finales"] == 6
    assert result.split["filas_entrenamiento"] + result.split["filas_prueba"] == 6


def test_confusion_matrix_matches_the_class_supports():
    """La matriz de confusion debe usar las mismas etiquetas que las predicciones."""
    frame = pd.DataFrame({
        "sentence": [
            "excelente producto muy bueno", "terrible producto muy malo",
            "me encanta la calidad", "horrible la calidad",
            "muy recomendado excelente", "no recomendado horrible",
            "buenissimo servicio", "peisimo servicio",
            "excelente resultado", "horrible resultado",
            "muy bueno excelente", "muy malo horrible",
        ],
        "score": ["1", "0", "1", "0", "1", "0", "1", "0", "1", "0", "1", "0"],
    })
    result = run_experiment(frame, "sentence", "score", random_state=42)
    metricas = result.metrics[result.best_model_name]
    matriz = pd.DataFrame(metricas["matriz_confusion"], index=metricas["etiquetas"],
                          columns=metricas["etiquetas"])
    assert int(matriz.values.sum()) == len(result.y_test)
    for etiqueta, valores in metricas["por_clase"].items():
        assert int(matriz.loc[etiqueta].sum()) == valores["support"]


def test_categorization_returns_a_known_category():
    category, signals = categorize_error("This is not good at all.")
    assert category in CATEGORY_NAMES
    assert signals


def test_categorization_is_deterministic():
    text = "The service was great but the food was cold."
    assert categorize_error(text) == categorize_error(text)


def test_annotate_and_summarize_errors():
    errors = pd.DataFrame({
        "text": ["This is not good at all.", "However the food was cold and bland."],
        "etiqueta_real": ["1", "1"],
        "etiqueta_predicha": ["0", "0"],
    })
    annotated = annotate_errors(errors, "text")
    assert {"category", "category_description", "signals"} <= set(annotated.columns)
    summary = summarize_by_category(annotated, "text")
    assert int(summary["errores"].sum()) == 2
    assert round(float(summary["porcentaje"].sum()), 0) == 100


@pytest.mark.skipif(not METRICS_JSON.exists(), reason="Ejecute scripts/train_text.py primero")
def test_reports_are_consistent_with_the_selected_model():
    payload = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    table = pd.read_csv(METRICS_CSV)
    best = payload["modelo_seleccionado"]
    assert best in set(table["modelo"])
    assert bool(table.loc[table["modelo"] == best, "seleccionado"].item()) is True
    assert table.loc[table["modelo"] == best, "f1_macro"].item() == pytest.approx(
        payload["modelos"][best]["f1_macro"], abs=1e-6
    )
    assert payload["modelos"][best]["f1_macro"] >= payload["modelos"]["dummy"]["f1_macro"]
