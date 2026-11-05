from pathlib import Path

import joblib
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models/text_model.joblib"

st.title("INF-8239 · Clasificador de texto")
st.caption("Demostración académica. La predicción no constituye una decisión automática.")

if not MODEL_PATH.exists():
    st.error("No existe el modelo. Ejecute: uv run python scripts/train_text.py")
    st.stop()

model = joblib.load(MODEL_PATH)
text = st.text_area("Texto para clasificar")
if st.button("Clasificar"):
    if not text.strip():
        st.warning("Ingrese un texto.")
    else:
        prediction = model.predict([text])[0]
        st.metric("Clase predicha", str(prediction))
        st.info("Interprete la salida dentro del dominio y las limitaciones del dataset documentado.")
