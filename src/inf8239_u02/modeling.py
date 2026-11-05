from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline

TARGET_LABEL_NAMES = {"0": "negativo", "1": "positivo"}

MODEL_LABELS = {
    "dummy": "DummyClassifier (linea base)",
    "naive_bayes": "Complement Naive Bayes",
    "logistic": "Regresion logistica con TF-IDF",
}


def label_name(value: object) -> str:
    """Nombre legible de la clase a partir de su codigo en el corpus."""
    return TARGET_LABEL_NAMES.get(str(value), str(value))


def build_vectorizer() -> TfidfVectorizer:
    """Vectorizador TF-IDF que se usa DENTRO de cada pipeline.

    Mantener el vectorizador dentro del pipeline evita fuga de informacion:
    el vocabulario y los pesos IDF se calculan solo con el conjunto de
    entrenamiento.
    """
    return TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)


def build_models(random_state: int = 42) -> dict[str, Pipeline]:
    return {
        "dummy": Pipeline(
            [("tfidf", build_vectorizer()), ("model", DummyClassifier(strategy="most_frequent"))]
        ),
        "naive_bayes": Pipeline([("tfidf", build_vectorizer()), ("model", ComplementNB())]),
        "logistic": Pipeline([
            ("tfidf", build_vectorizer()),
            ("model", LogisticRegression(
                max_iter=2000, class_weight="balanced", random_state=random_state
            )),
        ]),
    }
