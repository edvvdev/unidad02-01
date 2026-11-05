from __future__ import annotations

from inf8239_u02.config import settings
from inf8239_u02.data import load_dataset, sha256, validate_dataframe


def main() -> None:
    df = load_dataset()
    validate_dataframe(df, settings.text_column, settings.target_column)
    text = df[settings.text_column].astype(str)
    print("Ruta:", settings.dataset_path)
    print("SHA-256:", sha256(settings.dataset_path))
    print("Filas y columnas:", df.shape)
    print("Nulos:\n", df[[settings.text_column, settings.target_column]].isna().sum())
    print("Duplicados de texto:", text.duplicated().sum())
    print("Distribución:\n", df[settings.target_column].value_counts(dropna=False, normalize=True))
    print("Longitud de textos:\n", text.str.len().describe(percentiles=[0.5, 0.9, 0.99]))


if __name__ == "__main__":
    main()
