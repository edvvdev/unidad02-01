"""Aplicacion local de demostracion (LAB05).

La interfaz deja claro que la salida es una PREDICCION condicionada por el
corpus documentado, no una verdad sobre el texto escrito por la persona.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models/text_model.joblib"
AUDIT_PATH = ROOT / "reports/audit_summary.json"
METRICS_PATH = ROOT / "reports/text_metrics.json"

st.title("INF-8239 · Unidad 02 · Clasificador de sentimiento")
st.caption(
    "Demostracion academica. La prediccion no constituye una decision automatica "
    "ni una verdad sobre el texto."
)

if not MODEL_PATH.exists():
    st.error(
        "No existe el modelo. Ejecute la secuencia del README: "
        "`uv run python scripts/download_data.py`, `uv run python scripts/audit_data.py` "
        "y `uv run python scripts/train_text.py`."
    )
    st.stop()

model = joblib.load(MODEL_PATH)

if METRICS_PATH.exists():
    payload = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    best = payload["modelo_seleccionado"]
    metrics = payload["modelos"][best]
    st.sidebar.markdown("### Modelo en servicio")
    st.sidebar.write(f"**{metrics['nombre']}**")
    st.sidebar.write(f"- F1 macro: **{metrics['f1_macro']:.3f}**")
    st.sidebar.write(f"- Accuracy: **{metrics['accuracy']:.3f}**")
    st.sidebar.write(f"- Filas de prueba: {metrics['support_test']}")
    if AUDIT_PATH.exists():
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        st.sidebar.markdown("### Corpus")
        st.sidebar.write(f"- Filas: **{audit['rows']}**")
        st.sidebar.write(f"- Clases: **{audit['classes']}**")
        st.sidebar.write(f"- SHA-256: `{audit['dataset_sha256'][:16]}...`")

st.subheader("Texto para clasificar")
text = st.text_area(
    "Escriba una opinion breve sobre un producto, una pelicula o un restaurante",
    height=120,
)

if st.button("Clasificar"):
    if not text.strip():
        st.warning("Ingrese un texto.")
    else:
        prediction = str(model.predict([text])[0])
        nombres = {"0": "Negativo (0)", "1": "Positivo (1)"}
        st.metric("Clase predicha", nombres.get(prediction, prediction))
        if hasattr(model, "predict_proba"):
            try:
                probability = float(max(model.predict_proba([text])[0]))
                st.progress(min(probability, 1.0))
                st.caption(f"Confianza del clasificador: {probability:.3f}")
            except (AttributeError, ValueError):
                pass
        st.info(
            "Interprete la salida dentro del dominio y las limitaciones del dataset "
            "documentado en `docs/DATASET_CARD.md`. El corpus es ingles, de resenas "
            "en linea y de 2015 o anteriores; el modelo no esta validado para otros "
            "idiomas, otras Fuentes ni otros periodos."
        )

st.subheader("Alcance del modelo")
st.markdown(
    "- El corpus contiene reseñas cortas en ingles con sentimiento positivo o negativo.\n"
    "- El texto se vectoriza con TF-IDF dentro del pipeline; no hay senales de "
    "contexto largo.\n"
    "- Las negaciones, el contraste, la ironia y los textos cortos concentran los "
    "errores observados (vease `reports/error_analysis.csv`).\n"
    "- Una prediccion no debe usarse para decidir sobre personas, obras o servicios."
)
