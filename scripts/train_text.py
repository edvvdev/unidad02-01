from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, f1_score
from sklearn.model_selection import train_test_split

from inf8239_u02.config import ROOT, settings
from inf8239_u02.data import load_dataset, validate_dataframe
from inf8239_u02.modeling import build_models


def main() -> None:
    df = load_dataset().dropna(subset=[settings.text_column, settings.target_column])
    df = df.drop_duplicates(subset=[settings.text_column])
    validate_dataframe(df, settings.text_column, settings.target_column)
    counts = df[settings.target_column].value_counts()
    stratify = df[settings.target_column] if counts.min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        df[settings.text_column], df[settings.target_column], test_size=0.25,
        random_state=settings.random_state, stratify=stratify,
    )
    models = build_models(settings.random_state)
    rows = []
    predictions = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        predictions[name] = pred
        score = f1_score(y_test, pred, average="macro")
        rows.append({"model": name, "f1_macro": score})
        print(f"\n{name} · F1 macro={score:.3f}")
        print(classification_report(y_test, pred, zero_division=0))
    reports = ROOT / "reports"
    models_dir = ROOT / "models"
    reports.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)
    pd.DataFrame(rows).sort_values("f1_macro", ascending=False).to_csv(reports / "text_metrics.csv", index=False)
    selected = models["logistic"]
    selected_pred = predictions["logistic"]
    ConfusionMatrixDisplay.from_predictions(y_test, selected_pred, xticks_rotation=45, cmap="Blues")
    plt.tight_layout()
    plt.savefig(reports / "confusion_text.png", dpi=170)
    errors = pd.DataFrame({"text": x_test, "real": y_test, "predicted": selected_pred})
    errors = errors[errors["real"] != errors["predicted"]].copy()
    errors["category"] = "REVISAR"
    errors.to_csv(reports / "error_analysis.csv", index=False)
    joblib.dump(selected, models_dir / "text_model.joblib")
    print("\nArtefactos guardados en reports/ y models/")


if __name__ == "__main__":
    main()
