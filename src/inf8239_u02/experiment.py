"""Ejecucion reproducible del experimento de clasificacion de texto.

El script `scripts/train_text.py` y el notebook usan estas funciones, de modo
que ambos caminos producen exactamente el mismo experimento: misma limpieza,
misma particion estratificada, mismos pipelines y misma seleccion de modelo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

from .data import drop_duplicate_texts
from .modeling import MODEL_LABELS, build_models, label_name


@dataclass
class ExperimentResult:
    frame: pd.DataFrame
    x_train: pd.Series
    x_test: pd.Series
    y_train: pd.Series
    y_test: pd.Series
    metrics: dict[str, dict]
    predictions: dict[str, pd.Series]
    best_model_name: str
    best_model: object
    labels: list[str]
    split: dict
    cleaning: dict
    models: dict = field(default_factory=dict)


def prepare_frame(
    df: pd.DataFrame, text_column: str, target_column: str
) -> tuple[pd.DataFrame, dict]:
    """Limpieza minima antes de modelar.

    Se descartan filas con nulos y se eliminan los textos duplicados ANTES de
    la particion train/test. Eliminar despues allowiria que un mismo texto
    apareciera en entrenamiento y prueba, inflando las metricas.
    """
    working = df.dropna(subset=[text_column, target_column]).copy()
    rows_before = len(working)
    working[text_column] = working[text_column].astype(str).str.strip()
    # La etiqueta se normaliza a texto: asi las clases, la matriz de confusion y
    # el modelo guardado usan exactamente los mismos identificadores.
    working[target_column] = working[target_column].astype(str)
    empty_removed = int((working[text_column] == "").sum())
    working = working[working[text_column] != ""].copy()
    rows_without_empty = len(working)
    cleaned = drop_duplicate_texts(working, text_column)
    report = {
        "filas_originales": len(df),
        "filas_tras_quitar_nulos": rows_before,
        "textos_vacios_eliminados": empty_removed,
        "filas_tras_quitar_vacios": rows_without_empty,
        "filas_duplicadas_eliminadas": rows_without_empty - len(cleaned),
        "filas_finales": len(cleaned),
    }
    return cleaned, report


def split_data(
    frame: pd.DataFrame,
    text_column: str,
    target_column: str,
    random_state: int = 42,
    test_size: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Particion estratificada 75/25 con semilla fija."""
    counts = frame[target_column].value_counts()
    stratify = frame[target_column] if counts.min() >= 2 else None
    train, test = train_test_split(
        frame, test_size=test_size, random_state=random_state, stratify=stratify
    )
    return train, test


def evaluate_predictions(
    y_test: pd.Series, predictions: pd.Series, model_name: str, labels: list[str]
) -> dict:
    """Metricas globales, por clase y matriz de confusion de un modelo."""
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    per_class = {}
    for label in labels:
        values = report.get(str(label), {})
        per_class[str(label)] = {
            "nombre": label_name(label),
            "precision": float(values.get("precision", 0.0)),
            "recall": float(values.get("recall", 0.0)),
            "f1": float(values.get("f1-score", 0.0)),
            "support": int(values.get("support", 0)),
        }
    matrix = confusion_matrix(y_test, predictions, labels=labels)
    if int(matrix.sum()) != len(y_test):
        raise ValueError(
            "La matriz de confusion no suma el numero de filas de prueba; "
            "revise que las etiquetas y las predicciones usen el mismo tipo."
        )
    return {
        "modelo": model_name,
        "nombre": MODEL_LABELS.get(model_name, model_name),
        "f1_macro": float(f1_score(y_test, predictions, average="macro")),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision_macro": float(report.get("macro avg", {}).get("precision", 0.0)),
        "recall_macro": float(report.get("macro avg", {}).get("recall", 0.0)),
        "por_clase": per_class,
        "matriz_confusion": matrix.tolist(),
        "etiquetas": labels,
        "support_test": len(y_test),
    }


def run_experiment(
    df: pd.DataFrame,
    text_column: str,
    target_column: str,
    random_state: int = 42,
    test_size: float = 0.25,
) -> ExperimentResult:
    """Entrena baseline, Naive Bayes y regresion logistica sobre el corpus limpio."""
    frame, cleaning = prepare_frame(df, text_column, target_column)
    if frame[target_column].nunique() < 2:
        raise ValueError("Se requieren al menos dos clases para entrenar")
    train, test = split_data(frame, text_column, target_column, random_state, test_size)
    x_train = train[text_column]
    x_test = test[text_column]
    y_train = train[target_column]
    y_test = test[target_column]
    labels = sorted(str(value) for value in frame[target_column].unique())
    models = build_models(random_state)
    metrics: dict[str, dict] = {}
    predictions: dict[str, pd.Series] = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        predicted = model.predict(x_test)
        predictions[name] = pd.Series(predicted, index=test.index)
        metrics[name] = evaluate_predictions(y_test, predictions[name], name, labels)
    order = list(models)
    best_name = max(order, key=lambda name: (metrics[name]["f1_macro"], metrics[name]["accuracy"]))
    split = {
        "semilla": int(random_state),
        "proporcion_prueba": test_size,
        "estratificada": True,
        "filas_entrenamiento": len(train),
        "filas_prueba": len(test),
        "distribucion_entrenamiento": {
            str(key): int(value) for key, value in y_train.value_counts().sort_index().items()
        },
        "distribucion_prueba": {
            str(key): int(value) for key, value in y_test.value_counts().sort_index().items()
        },
    }
    return ExperimentResult(
        frame=frame,
        x_train=x_train,
        x_test=x_test,
        y_train=y_train,
        y_test=y_test,
        metrics=metrics,
        predictions=predictions,
        best_model_name=best_name,
        best_model=models[best_name],
        labels=labels,
        split=split,
        cleaning=cleaning,
        models=models,
    )


def build_error_frame(
    result: ExperimentResult, text_column: str = "text", target_column: str = "score"
) -> pd.DataFrame:
    """Filas mal clasificadas por el modelo seleccionado."""
    predicted = result.predictions[result.best_model_name]
    errors = pd.DataFrame(
        {
            text_column: result.x_test,
            "etiqueta_real": result.y_test,
            "etiqueta_predicha": predicted,
        }
    )
    errors["nombre_real"] = errors["etiqueta_real"].map(label_name)
    errors["nombre_predicho"] = errors["etiqueta_predicha"].map(label_name)
    if "source" in result.frame.columns:
        sources = result.frame.loc[result.x_test.index, "source"]
        errors["origen"] = sources.values
    return errors[errors["etiqueta_real"] != errors["etiqueta_predicha"]].reset_index(drop=True)
