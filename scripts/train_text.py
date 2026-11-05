"""Entrena baseline, Complement Naive Bayes y regresion logistica; y guarda el mejor.

Artefactos generados:
  reports/text_metrics.csv       metricas globales por modelo (seleccion por F1 macro)
  reports/text_metrics.json      metricas por clase, matriz de confusion y limpieza
  reports/confusion_text.png     matriz de confusion del modelo seleccionado
  reports/models_comparison.png  comparacion de F1 macro entre los tres pipelines
  reports/error_analysis.csv     todos los errores con categoria y señales
  reports/error_sample_20.csv    muestra aleatoria de 20 errores para revision manual
  reports/errors_by_category.csv reparto de errores por categoria
  reports/errors_by_category.png  figura del reparto por categoria
  models/text_model.joblib       pipeline ganador (vectorizador incluido)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay

from inf8239_u02.config import ROOT, settings
from inf8239_u02.data import load_dataset, sha256
from inf8239_u02.errors import annotate_errors, sample_errors, summarize_by_category
from inf8239_u02.experiment import build_error_frame, run_experiment

REPORTS = ROOT / "reports"
MODELS = ROOT / "models"
TEXT_COLUMN = settings.text_column
TARGET_COLUMN = settings.target_column


def save_metrics(result, path_csv, path_json) -> None:
    rows = []
    for name, metrics in result.metrics.items():
        rows.append({
            "modelo": name,
            "nombre": metrics["nombre"],
            "f1_macro": round(metrics["f1_macro"], 6),
            "accuracy": round(metrics["accuracy"], 6),
            "precision_macro": round(metrics["precision_macro"], 6),
            "recall_macro": round(metrics["recall_macro"], 6),
            "filas_prueba": metrics["support_test"],
            "seleccionado": name == result.best_model_name,
        })
    table = pd.DataFrame(rows).sort_values("f1_macro", ascending=False).reset_index(drop=True)
    table.to_csv(path_csv, index=False)
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_path": str(settings.dataset_path.relative_to(ROOT)),
        "dataset_sha256": sha256(settings.dataset_path),
        "text_column": TEXT_COLUMN,
        "target_column": TARGET_COLUMN,
        "random_state": settings.random_state,
        "limpieza": result.cleaning,
        "particion": result.split,
        "modelo_seleccionado": result.best_model_name,
        "criterio_seleccion": "mayor F1 macro; desempate por accuracy",
        "modelos": result.metrics,
        "tabla": table.to_dict(orient="records"),
    }
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def plot_confusion(result, path):
    metrics = result.metrics[result.best_model_name]
    labels = metrics["etiquetas"]
    matrix = pd.DataFrame(
        metrics["matriz_confusion"], index=labels, columns=labels
    )
    figure, axis = plt.subplots(figsize=(6, 5))
    display = ConfusionMatrixDisplay(confusion_matrix=matrix.values, display_labels=labels)
    display.plot(ax=axis, cmap="Blues", values_format="d")
    axis.set_title(f"Matriz de confusion · {metrics['nombre']} (F1 macro={metrics['f1_macro']:.3f})")
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    return figure


def plot_models_comparison(result, path):
    names = [metrics["nombre"] for metrics in result.metrics.values()]
    scores = [metrics["f1_macro"] for metrics in result.metrics.values()]
    colors = ["#8d99ae" if name != result.best_model_name else "#2a9d8f" for name in names]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    bars = axis.bar(names, scores, color=colors)
    axis.set_ylabel("F1 macro")
    axis.set_ylim(0, 1)
    axis.set_title("Comparacion de pipelines (mismo preprocesamiento y misma particion)")
    axis.axhline(
        result.metrics["dummy"]["f1_macro"], color="#e76f51", linestyle="--", linewidth=1,
        label="Linea base (DummyClassifier)",
    )
    for bar, score in zip(bars, scores):
        axis.text(bar.get_x() + bar.get_width() / 2, score + 0.02, f"{score:.3f}",
                  ha="center", fontsize=9)
    axis.legend(loc="lower right")
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    return figure


def plot_errors_by_category(summary, path):
    data = summary.sort_values("errores")
    figure, axis = plt.subplots(figsize=(9, 6))
    bars = axis.barh(data["category"], data["errores"], color="#457b9d")
    for bar, value in zip(bars, data["errores"]):
        axis.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2, str(value),
                  va="center", fontsize=8)
    axis.set_xlabel("Errores")
    axis.set_title("Reparto de errores por categoria (modelo seleccionado)")
    axis.grid(axis="x", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    return figure


def main() -> None:
    df = load_dataset()
    result = run_experiment(
        df, TEXT_COLUMN, TARGET_COLUMN, random_state=settings.random_state, test_size=0.25
    )
    REPORTS.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    print("Limpieza previa:", result.cleaning)
    print("Particion:", result.split)
    for name, metrics in result.metrics.items():
        print(f"\n{name} · F1 macro={metrics['f1_macro']:.3f} · accuracy={metrics['accuracy']:.3f}")
        for label, values in metrics["por_clase"].items():
            print(
                f"   clase {label} ({values['nombre']}): precision={values['precision']:.3f} "
                f"recall={values['recall']:.3f} f1={values['f1']:.3f} support={values['support']}"
            )
    print(f"\nModelo seleccionado por F1 macro: {result.best_model_name}")
    save_metrics(result, REPORTS / "text_metrics.csv", REPORTS / "text_metrics.json")
    plt.close(plot_confusion(result, REPORTS / "confusion_text.png"))
    plt.close(plot_models_comparison(result, REPORTS / "models_comparison.png"))
    errors = build_error_frame(result, TEXT_COLUMN, TARGET_COLUMN)
    annotated = annotate_errors(errors, TEXT_COLUMN)
    annotated.to_csv(REPORTS / "error_analysis.csv", index=False)
    sample = sample_errors(annotated, TEXT_COLUMN, size=20, random_state=settings.random_state)
    sample.to_csv(REPORTS / "error_sample_20.csv", index=False)
    summary = summarize_by_category(annotated, TEXT_COLUMN)
    summary.to_csv(REPORTS / "errors_by_category.csv", index=False)
    plt.close(plot_errors_by_category(summary, REPORTS / "errors_by_category.png"))
    import joblib

    joblib.dump(result.best_model, MODELS / "text_model.joblib")
    print(f"\nErrores del modelo seleccionado: {len(annotated)}")
    print(summary.to_string(index=False))
    print("\nArtefactos guardados en reports/ y models/")


if __name__ == "__main__":
    main()
