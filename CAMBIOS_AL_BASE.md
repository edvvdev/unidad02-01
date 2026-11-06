# Cambios respecto al proyecto base

Base de referencia: `INF8239_U02_NLP_Proyecto_Base_uv.zip` (MD5
`c1325605a573a72e884d4838452cec03`, idéntico a su copia `(1)`), extraído en
`Unidad_2/INF8239_U02_NLP/` el 2026-11-05.

## 0. Lo que NO se tocó

| Archivo | Estado |
|---|---|
| `pyproject.toml` | **Sin modificar** (mismas dependencias, mismos grupos, mismo `ruff` con `line-length = 100`) |
| `uv.lock` | **Sin modificar** (se conserva versionado, como pide el manual) |
| `.python-version` | Sin modificar (`3.12`) |
| `scripts/embeddings_network.py` | Sin modificar (pertenece a LAB06, fuera de este ejercicio) |
| `tests/test_embeddings_network.py` | Sin modificar |

Las dependencias que hacen falta para el notebook y el PDF (`jupyter`,
`nbformat`, `ipykernel`, `reportlab`) **no** se añadieron a `pyproject.toml`:
se resuelven con `uv run --with <paquete>`, que crea un entorno temporal sin
tocar el venv del proyecto ni el `uv.lock`. Motivo: `uv sync` **elimina** los
paquetes que no están en el lock, así que instalar en `.venv` haría que el
entorno dejara de ser reproducible entre ejecuciones.

## 1. Archivos nuevos

| Archivo | Qué hace |
|---|---|
| `src/inf8239_u02/experiment.py` | Experimento reproducible: limpieza, partición estratificada, entrenamiento de los tres pipelines, métricas por clase y selección del mejor modelo por F1 macro. Lo usan **el script y el notebook**, de modo que ambos caminos dan el mismo resultado. |
| `src/inf8239_u02/errors.py` | Taxonomía de 20 categorías de error con reglas léxicas transparentes. Cada error recibe una categoría y las **señales** que la activaron. Sin aprendizaje automático: las reglas son revisables. |
| `scripts/audit_candidates.py` | Audita el **formato crudo** del corpus aprobado (cuántas filas pierde un lector CSV ingenuo en cada origen, cuántos caracteres U+0085 hay y cuántas filas recupera la regla aplicada) y recalcula las cifras verificadas de los dos candidatos. Escribe `reports/parse_audit.json` y `reports/candidates_audit.json`. |
| `scripts/build_ejercicio01_pdf.py` | Genera `docs/EJERCICIO_01_PDF_BRIEF.pdf` leyendo todas las cifras de `reports/` y de `docs/dataset_candidates.csv`: el generador no contiene ninguna cifra escrita a mano. El enlace al repositorio se toma de `REPO_URL`. |
| `scripts/run_all.sh` | Pipeline completo en Linux/macOS: `.env` → `uv sync` → descarga → auditoría → auditoría del formato crudo y de los candidatos → entrenamiento → notebook → PDF → pruebas. |
| `scripts/run_all.ps1` | Equivalente para Windows PowerShell. |
| `notebooks/01_ejercicio01_nlp.ipynb` | Notebook **ejecutado** con salidas y figuras: auditoría → comparación de candidatos → comparación de modelos → métricas por clase → matriz de confusión → 20 errores con interpretación manual → conclusiones. |
| `tests/test_errors.py` | Pruebas de la taxonomía de errores (20 categorías, detección de negación/ironía/contraste, determinismo, reparto porcentual). |
| `tests/test_audit_candidates.py` | Pruebas del desglose de filas perdidas por el lector CSV ingenuo (261 de IMDb, 225 de Amazon, 294 de Yelp; 780 en total), de la recuperación completa con la regla aplicada, de los dos caracteres U+0085 y de las cifras verificadas de los dos candidatos. |
| `docs/EJERCICIO_01_PDF_BRIEF.pdf` | PDF breve de entrega (6 páginas). |
| `AI_USE_DECLARATION.md` | Declaración de uso de IA con prompts, verificaciones y correcciones. |
| `CAMBIOS_AL_BASE.md` | Este documento. |
| `requirements.txt`, `requirements-dev.txt`, `requirements-cloud.txt` | Exportaciones de `uv export` (no editadas a mano). |

## 2. Archivos ampliados

| Archivo | Cambio | Motivo |
|---|---|---|
| `src/inf8239_u02/config.py` | Se añadieron `dataset_name`, `dataset_page`, `dataset_license` y `dataset_sha256` a `Settings`. | Identificar y verificar el corpus sin cambiar las variables que ya usaba el base. |
| `src/inf8239_u02/data.py` | Se añadieron `parse_labelled_lines`, `read_sentiment_archive`, `normalize_text_key`, `duplicate_report` y `drop_duplicate_texts`. Se conservaron `sha256`, `load_dataset` y `validate_dataframe` sin cambios de comportamiento. | El base no podía leer el formato `frase<TAB>etiqueta` ni auditar duplicados. `parse_labelled_lines` resuelve el problema verificado de las 252 filas y de los dos caracteres U+0085. |
| `src/inf8239_u02/modeling.py` | `build_models` se conserva con los mismos tres pipelines; se extrajo `build_vectorizer()` y se añadieron `MODEL_LABELS` y `label_name()`. | Compartir el vectorizador y poder nombrar las clases (`0` → negativo) en informes y en la aplicación. |
| `scripts/download_data.py` | Se añadió el modo ZIP de UCI: descarga, **verifica el SHA-256 contra `DATASET_SHA256`**, normaliza a `data/raw/dataset.csv` y escribe `data/raw/dataset.source.txt`. El modo local y el modo CSV se conservan. | El manual exige mostrar el hash y dejar constancia de la procedencia. |
| `scripts/audit_data.py` | Se conservó toda la salida por consola y se añadieron `reports/audit_summary.json`, `reports/audit_table.csv` y `reports/audit_duplicates.csv`. | El manual pide evidenciar la auditoría; el base solo imprimía. |
| `scripts/train_text.py` | Se reescribió como CLI sobre `src/inf8239_u02/experiment.py`. Ahora: guarda **el mejor modelo por F1 macro** (el base fijaba la regresión logística), escribe `text_metrics.csv` **y** `text_metrics.json` con métricas por clase, añade `models_comparison.png`, y sustituye la columna `category = "REPLACE"` por la categorización real con `reports/error_analysis.csv`, `error_sample_20.csv`, `errors_by_category.csv` y `.png`. | Correcciones exigidas por el manual y por el enunciado del ejercicio. |
| `tests/test_data_contract.py` | Se conservaron las tres pruebas del base y se añadieron el contrato del corpus real (columnas, ≥500 filas, 2 clases, sin nulos ni textos vacíos, hash coherente con la auditoría, duplicados declarados, rutas relativas), la prueba del parser y la de deduplicación. | El contrato del base solo validaba marcos sintéticos. |
| `tests/test_text_model.py` | Se conservó la prueba del base y se añadieron: vectorizador dentro del pipeline, selección del mejor modelo por F1 macro, deduplicación antes de partir, coherencia de la matriz de confusión con los soportes por clase, coherencia entre `text_metrics.csv` y `text_metrics.json`, y pruebas de la taxonomía. | Cubrir los puntos que la rúbrica evalúa (fuga, baseline, evaluación). |
| `app/streamlit_app.py` | Muestra la clase con nombre legible, la confianza si existe, el resumen del corpus y del modelo en la barra lateral, y un aviso explícito sobre el alcance del modelo. | El manual pide advertir que la predicción no es una verdad. |
| `.env.example` | Sustituido por la configuración **real** (URL de UCI, columnas `sentence`/`score`, SHA-256 esperado). | El base apuntaba a la muestra `demo_text.csv`. Con esta versión, un clon limpio reproduce el experimento sin editar nada. |
| `requirements-colab.txt` | Se conservó la lista y se añadieron comentarios de uso en Colab (instalación y `PYTHONPATH` para `src`). | El manual pide preparar la nube con este archivo. |
| `docs/DATASET_CARD.md` | Completado: identificación, procedencia, objetivo, diccionario con momento de disponibilidad y riesgo, procedimiento de obtención, transformaciones, calidad observada, cinco ejemplos reales, prevención de fuga, sesgos, población no cubierta, usos prohibidos y referencias. | El base solo tenía las cabeceras vacías. |
| `docs/dataset_candidates.csv` | Columnas ampliadas y los dos candidatos con cifras **verificadas** y el motivo de la decisión. | El base tenía dos filas `pending` sin datos. |
| `README.md` | Reemplazado por la guía reproducible completa: instalación, configuración, descarga, auditoría, entrenamiento, notebook, PDF, aplicación, `run_all`, pruebas, resultados, dataset, estructura, límites y licencia. | El base era una guía de 12 líneas. |

## 3. Decisiones que cambian el resultado del base

| Decisión | Base | Ahora | Por qué |
|---|---|---|---|
| Modelo guardado | `models["logistic"]` fijo | El de mayor F1 macro | El manual lo pide de forma expresa; en este corpus gana Complement Naive Bayes (0,834 frente a 0,814). |
| Categoría de los errores | Literal `REPLACE` | 20 reglas léxicas con señales | El base no cumplía el requisito de analizar los errores de verdad. |
| Lectura del corpus | CSV genérico por URL | ZIP de UCI verificado por SHA-256 y normalizado | El base habría leído un CSV; el corpus real es un ZIP con formato TSV y problemas de comillas. |
| Configuración de datos | Muestra `demo_text.csv` | Corpus público real con hash | La muestra del base solo sirve para comprobar la arquitectura. |
| Artefactos de auditoría | Solo salida por consola | JSON + 2 CSV en `reports/` | Sin artefactos no hay evidencia verificable ni cifras respaldadas. |

## 4. Segunda ronda de correcciones (2026-11-06)

Correcciones sobre la entrega ya publicada, todas verificadas ejecutando el
código del repositorio.

| # | Defecto | Corrección | Evidencia |
|---|---|---|---|
| 1 | La figura `reports/audit_overview.png` etiquetaba las dos clases como "negativo" (`clave == '1' and 'positivo' or 'negativo'` compara un `numpy.int64` con una cadena y siempre es `False`). | Etiquetado por mapeo de valor de clase (`{0: "negativo", 1: "positivo"}`) en la celda que genera la figura. | La figura publicada muestra `1 (positivo)`; `notebooks/01_ejercicio01_nlp.ipynb` regenerada. |
| 2 | El desglose por fuente del hallazgo del formato crudo era falso (53 de Amazon y 70 de Yelp). | `scripts/audit_candidates.py` reproduce la pérdida del lector CSV ingenuo archivo por archivo: **261 de IMDb, 225 de Amazon y 294 de Yelp, 780 de 3.000 en total**, y explica que las comillas del archivo de IMDb y los caracteres U+0085 son la causa. | `reports/parse_audit.json`; README, `docs/DATASET_CARD.md` y PDF actualizados. |
| 3 | `README.md` decía "las 13 restantes" con 17 categorías activadas y 8 listadas. | "las 9 restantes" (20 errores). | `reports/errors_by_category.csv`. |
| 4 | La declaración afirmaba que no había ninguna cifra escrita a mano en el generador del PDF, pero el generador tenía literales numéricos. | El generador lee ahora `reports/*.json`, `reports/*.csv` y `docs/dataset_candidates.csv`: no queda ninguna cifra escrita a mano. La afirmación de la declaración se reescribió con precisión. | `scripts/build_ejercicio01_pdf.py`. |
| 5 | Erratas en `AI_USE_DECLARATION.md` ("wrote archivos", "El scriptinformed", "La IA proposes"). | Corregidas y revisado el archivo entero en busca de texto corrupto o no latino. | `grep` de rangos CJK sin resultados. |
| 6 | El título de `reports/confusion_text.png` quedaba pegado al borde y se recortaba la "M" inicial. | Figura más ancha, título con tamaño de fuente explícito y guardado con `bbox_inches="tight"`. | `reports/confusion_text.png` regenerado y revisado. |
| 7 | El PDF se publicaba sin tildes ("Conclusion", "Analisis de errores", "Regresion logistica", "Metricas por clase"). | Todo el texto del generador va con tildes y los nombres de los modelos llevan acentos en `src/inf8239_u02/modeling.py`. | `pdftotext` del PDF regenerado. |
| 8 | El PDF repetía la misma URL en dos filas ("Repositorio" y "Repositorio del enunciado"). | Una sola fila de repositorio. | `pdftotext` del PDF regenerado. |
| 9 | El mandato llama a este trabajo "Ejercicio 03" y el repositorio lo llama "Ejercicio 01". | Nota aclaratoria en el README, en la portada del PDF y en la declaración de IA. | README y PDF. |
| 10 | El árbol git tenía un export HTML del notebook sin versionar. | `*.html` añadido a `.gitignore`; el export se conserva en local pero no se versiona. | `git status --short`. |
| 11 | El candidato descartado publicaba "140 con URL o correo", cifra que no se reproduce con ninguna definición comprobable. | `scripts/audit_candidates.py` calcula 113 filas con URL o dirección de correo y 141 si se cuenta cualquier mensaje con un símbolo `@`; el PDF y la documentación usan esas cifras. | `reports/candidates_audit.json`. |

## 5. Elementos no incluidos y por qué

| Elemento | Motivo |
|---|---|
| `data/raw/dataset.csv`, `data/raw/dataset.zip`, `data/raw/dataset.source.txt` | El `.gitignore` del base excluye `data/raw/*`. El corpus se obtiene con `scripts/download_data.py` y su hash queda en el manifiesto y en `reports/audit_summary.json`. |
| `.env` | No se versiona por indicación del manual. `.env.example` sí está versionado con la configuración real. |
| `.venv/` | Excluido por el `.gitignore` del base; `uv.lock` sí está versionado. |
| `models/word2vec.model` | Pertenece a LAB06 (embeddings y redes) y no se usa en este ejercicio. |
