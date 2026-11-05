import pandas as pd
import pytest

from inf8239_u02.data import validate_dataframe


def test_accepts_valid_dataframe():
    df = pd.DataFrame({"text": ["uno", "dos"], "label": ["a", "b"]})
    validate_dataframe(df, "text", "label")


def test_rejects_missing_target():
    df = pd.DataFrame({"text": ["uno"]})
    with pytest.raises(ValueError, match="Faltan columnas"):
        validate_dataframe(df, "text", "label")


def test_rejects_empty_text():
    df = pd.DataFrame({"text": [""], "label": ["a"]})
    with pytest.raises(ValueError, match="textos vacíos"):
        validate_dataframe(df, "text", "label")
