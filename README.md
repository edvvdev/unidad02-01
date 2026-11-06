# INF-8239 Ciencia de Datos II · Unidad 02 · Ejercicio 03 (LAB04 + LAB05)

**Estudiante:** Edwing Perez  
**Repositorio de entrega:** https://github.com/edvvdev/unidad02-01  
**Unidad:** 02 · Procesamiento de Lenguaje Natural, redes y visión

> **Nota sobre el nombre del ejercicio.** El mandato de la unidad numera este
> trabajo como **Ejercicio 03** (LAB04 + LAB05). En el repositorio y en el PDF
> aparece como **Ejercicio 01** por orden de entrega dentro de la unidad: es el
> mismo trabajo, con el mismo contenido.

Este proyecto resuelve el **Ejercicio 03 de la Unidad 02** (el Ejercicio 01 del
repositorio): seleccionar, aprobar,
descargar y auditar un corpus público de texto (LAB04) y, sobre ese corpus,
entrenar y evaluar tres clasificadores de sentimiento, analizar sus errores y
publicar una aplicación local reproducible (LAB05).

- **Corpus aprobado:** *Sentiment Labelled Sentences* de UCI (dataset 331),
  licencia **CC BY 4.0**, 3.000 frases en inglés con etiqueta binaria
  `score` (0 = negativo, 1 = positivo).
- **Métrica de decisión:** F1 macro.
- **Modelo publicado:** **Complement Naive Bayes** (F1 macro 0,834), elegido por
  métrica y no por el script base, que fijaba la regresión logística.

---

## 1. Requisitos

- [uv](https://docs.astral.sh/uv/) 0.12 o superior.
- Python 3.12 (lo instala `uv`).
- Conexión a internet para la **primera** descarga del corpus.

## 2. Instalación

```bash
uv python install 3.12
uv sync
uv run pytest -q
```

`uv sync` crea `.venv/` a partir de `uv.lock` (versionado en el repositorio).
No se copia `.venv/` a ningún sitio y no hay rutas absolutas ni credenciales.

## 3. Configuración de la fuente de datos

El archivo `.env` **no se versiona** (está en `.gitignore`). La configuración
real del corpus aprobado ya está en `.env.example`, de modo que basta con:

```bash
cp .env.example .env
```

Contenido relevante de `.env` (rutas **relativas**, sin `C:\Users\...`):

```bash
DATA_SOURCE=url
DATASET_PATH=data/raw/dataset.csv
DATASET_URL=https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip
TEXT_COLUMN=sentence
TARGET_COLUMN=score
RANDOM_STATE=42
DATASET_SHA256=afc26626d710899948693e1a61405dce197f57ffa719fa1130d346b4cc095343
```

## 4. Descarga reproducible del corpus (LAB04)

```bash
uv run python scripts/download_data.py
```

Descarga el ZIP desde el enlace original de la ficha de UCI, **muestra el
SHA-256**, lo verifica contra `DATASET_SHA256` (si no coincide, no normaliza y
termina con error), lo convierte en `data/raw/dataset.csv` y escribe el
manifiesto `data/raw/dataset.source.txt`.

## 5. Auditoría (LAB04)

```bash
uv run python scripts/audit_data.py
```

Imprime filas, columnas, nulos, duplicados, clases y longitudes p50/p90/p99, y
escribe:

| Artefacto | Contenido |
|---|---|
| `reports/audit_summary.json` | resumen numérico de la auditoría |
| `reports/audit_table.csv` | una fila por columna (tipo, nulos, únicos, ejemplo) |
| `reports/audit_duplicates.csv` | textos duplicados con conteo y etiquetas |

## 5.1 Formato crudo y candidatos comparados

```bash
uv run python scripts/audit_candidates.py
```

Comprueba el archivo crudo aprobado y las cifras verificadas del candidato
descartado, y escribe:

| Artefacto | Contenido |
|---|---|
| `reports/parse_audit.json` | filas que pierde un lector CSV ingenuo en cada origen, caracteres U+0085 y filas recuperadas por la regla aplicada |
| `reports/candidates_audit.json` | cifras verificadas de los dos candidatos (filas, clases, duplicados y señales de datos personales) |

Todas las cifras del README, del PDF y del notebook salen de `reports/`: ningún
documento las escribe a mano.

## 6. Entrenamiento y evaluación (LAB05)

```bash
uv run python scripts/train_text.py
```

Entrena `DummyClassifier` (línea base), `ComplementNB` y
`LogisticRegression` con la **misma** partición estratificada 75/25 y semilla
42, con el vectorizador TF-IDF **dentro** de cada pipeline (sin fuga). Guarda el
**mejor** modelo según F1 macro y produce:

| Artefacto | Contenido |
|---|---|
| `reports/text_metrics.csv` | F1 macro, accuracy, precisión y recall macro por modelo |
| `reports/text_metrics.json` | métricas por clase, matriz de confusión, limpieza y partición |
| `reports/confusion_text.png` | matriz de confusión del modelo seleccionado |
| `reports/models_comparison.png` | comparación de F1 macro entre pipelines |
| `reports/error_analysis.csv` | todos los errores con `category` y `signals` |
| `reports/error_sample_20.csv` | muestra aleatoria (semilla 42) de 20 errores |
| `reports/errors_by_category.csv` / `.png` | reparto de errores por categoría |
| `models/text_model.joblib` | pipeline ganador (incluye el vectorizador) |

Verificación manual del modelo guardado:

```bash
uv run python -c "import joblib; m=joblib.load('models/text_model.joblib'); print(m.predict(['Excellent service, very nice']))"
```

## 7. Notebook ejecutado

```bash
uv run --with jupyter --with nbformat --with ipykernel \
  python -m jupyter nbconvert --to notebook --execute --inplace \
  notebooks/01_ejercicio01_nlp.ipynb
```

`notebooks/01_ejercicio01_nlp.ipynb` contiene el flujo completo (auditoría →
comparación de modelos → métricas por clase → matriz de confusión → análisis
de **20 errores con categoría, señales e interpretación manual** → figuras) y
está versionado **con sus salidas y sus figuras**. `jupyter` se instala como
dependencia temporal (`--with`), de modo que no se modifica `pyproject.toml` ni
`uv.lock`.

## 8. PDF breve del ejercicio

```bash
REPO_URL=https://github.com/edvvdev/unidad02-01 \
  uv run --with reportlab python scripts/build_ejercicio01_pdf.py
```

Genera `docs/EJERCICIO_01_PDF_BRIEF.pdf` (6 páginas: portada con el enlace al
repositorio, trazabilidad del corpus, tabla de resultados, figuras, conclusión
de 412 palabras y resumen de la declaración de IA). Todas las cifras del PDF se
leen de `reports/*.json` y `reports/*.csv`.

## 9. Aplicación local

```bash
uv run streamlit run app/streamlit_app.py
```

La interfaz muestra la clase predicha con su nombre legible, la confianza si el
modelo la expone y un aviso explícito sobre el alcance del modelo: la salida es
una **predicción condicionada por el corpus documentado**, no una verdad.

## 10. Reproducir todo de una vez

```bash
bash scripts/run_all.sh              # Linux / macOS
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1   # Windows
```

El script hace: `.env` → `uv sync` → descarga → auditoría → auditoría del
formato crudo y de los candidatos → entrenamiento → notebook ejecutado → PDF →
pruebas. En un clon limpio termina sin errores y regenera `reports/`,
`models/` y `docs/EJERCICIO_01_PDF_BRIEF.pdf`.

## 11. Pruebas

```bash
uv run pytest -q
```

32 pruebas cubren el contrato de datos (columnas reales, ≥500 filas, 2 clases,
sin nulos ni textos vacíos, hash coherente con la auditoría, duplicados
declarados), la presencia del vectorizador dentro del pipeline, la
selección del mejor modelo por F1 macro, la coherencia de la matriz de
confusión con los soportes por clase, la taxonomía de errores y la coherencia
entre `reports/text_metrics.csv` y `reports/text_metrics.json`.

Las pruebas que necesitan el corpus se omiten con un mensaje explícito si el
archivo todavía no se ha descargado.

## 12. Resultados

Partición estratificada 75/25, semilla 42, 2.236 filas de entrenamiento y 746
de prueba (373 por clase):

| Modelo | F1 macro | Accuracy | Precisión macro | Recall macro | Seleccionado |
|---|---|---|---|---|---|
| Complement Naive Bayes | **0,834** | 0,834 | 0,834 | 0,834 | **Sí** |
| Regresión logística con TF-IDF | 0,814 | 0,814 | 0,814 | 0,814 | No |
| DummyClassifier (línea base) | 0,333 | 0,500 | 0,250 | 0,500 | No |

Métricas por clase del modelo seleccionado:

| Clase | Precisión | Recall | F1 | Support |
|---|---|---|---|---|
| 0 (negativo) | 0,823 | 0,850 | 0,836 | 373 |
| 1 (positivo) | 0,845 | 0,818 | 0,831 | 373 |

Matriz de confusión: `[[317, 56], [68, 305]]`. La celda fuera de la diagonal
más frequentada es *real = positivo → predicho = negativo* con 68 casos: la
clase que se pierde es la **positiva** (recall 0,818 < 0,850).

Errores del modelo seleccionado: **124** sobre 746 filas de prueba, con 20
categorías de reglas léxicas transparentes (17 con al menos un caso):

| Categoría | Errores | % |
|---|---|---|
| `senal_no_cubierta` | 37 | 29,84 |
| `hecho_sin_valoracion` | 18 | 14,52 |
| `contraste` | 12 | 9,68 |
| `negacion` | 12 | 9,68 |
| `comparacion` | 8 | 6,45 |
| `hiperbole` | 6 | 4,84 |
| `dialecto_registro_informal` | 6 | 4,84 |
| `texto_corto` | 5 | 4,03 |
| las 9 restantes | 20 | 16,13 |

> Cada cifra de esta tabla procede de `reports/text_metrics.json` y
> `reports/errors_by_category.csv`, y es la misma que muestra el PDF.

## 13. Dataset

| Campo | Valor |
|---|---|
| Nombre | Sentiment Labelled Sentences (UCI 331) |
| Ficha | https://archive.ics.uci.edu/dataset/331/sentiment-labelled-sentences |
| Descarga | https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip |
| Licencia | CC BY 4.0 |
| Creador | Dimitrios Kotzias (KDD 2015), DOI 10.24432/C57604 |
| Filas / columnas | 3.000 · `sentence`, `score`, `source` |
| Objetivo | `score`: 0 = negativo, 1 = positivo (1.500 / 1.500) |
| SHA-256 ZIP | `afc26626d710899948693e1a61405dce197f57ffa719fa1130d346b4cc095343` |
| SHA-256 CSV | `6410f6b155301ad6a1cd47d90de2e44a5a82f938d4f13d500400a1eafea069fd` |
| Duplicados | 18 (eliminados antes de partir), 0 con etiqueta contradictoria |
| Nulos / vacíos | 0 / 0 |

Ficha completa (diccionario de datos, transformaciones, cinco ejemplos reales,
sesgos, población no cubierta y usos prohibidos): **`docs/DATASET_CARD.md`**.
Comparación con el candidato descartado: **`docs/dataset_candidates.csv`**.

### Hallazgo sobre los datos crudos

El archivo de IMDb contiene comillas dobles dentro del texto y **dos
caracteres U+0085 (NEXT LINE)** dentro de frases. Un lector CSV ingenuo con
separador coma pierde **261 de las 1.000 filas de IMDb**, **225 de las 1.000 de
Amazon** y **294 de las 1.000 de Yelp**: **780 de las 3.000 filas** del corpus.
Con separador tabulador se pierden **252 de las 1.000 filas de IMDb** y
`str.splitlines()` deja dos registros sin etiqueta. La implementación de
`src/inf8239_u02/data.py` corta el archivo solo por `\n` y separa cada línea
por su **último tabulador**, y con esa regla recupera las **3.000 filas**
completas. El desglose por fuente y el total se calculan en
`scripts/audit_candidates.py` y quedan en `reports/parse_audit.json`.

## 14. Estructura del proyecto

```
.
├── app/streamlit_app.py              Aplicación local (LAB05)
├── data/
│   ├── raw/dataset.csv                Corpus normalizado (no se versiona)
│   ├── raw/dataset.source.txt         Manifiesto de procedencia (no se versiona)
│   └── sample/demo_text.csv           Muestra del base (solo arquitectura)
├── docs/
│   ├── DATASET_CARD.md                Ficha completa del corpus
│   ├── dataset_candidates.csv         Comparación de los dos candidatos
│   └── EJERCICIO_01_PDF_BRIEF.pdf     PDF breve de entrega
├── models/text_model.joblib           Pipeline seleccionado (incluye el vectorizador)
├── notebooks/01_ejercicio01_nlp.ipynb Notebook ejecutado con salidas y figuras
├── reports/                           Métricas, tablas y figuras (versionados)
│   ├── audit_summary.json             Auditoría numérica
│   ├── audit_table.csv                Auditoría por columna
│   ├── audit_duplicates.csv           Auditoría de duplicados
│   ├── parse_audit.json               Formato crudo: pérdidas del lector CSV ingenuo
│   ├── candidates_audit.json          Cifras verificadas de los dos candidatos
│   ├── audit_overview.png             Longitud de frases y clases
│   ├── text_metrics.csv / .json       Métricas globales y por clase
│   ├── confusion_text.png             Matriz de confusión
│   ├── models_comparison.png          Comparación de pipelines
│   ├── error_analysis.csv             Errores con categoría y señales
│   ├── error_sample_20.csv            Muestra de 20 errores
│   ├── error_sample_20_reviewed.csv   La misma muestra con interpretación manual
│   └── errors_by_category.csv / .png  Reparto por categoría
├── scripts/
│   ├── download_data.py               Descarga verificada y normalización
│   ├── audit_data.py                  Auditoría
│   ├── audit_candidates.py            Formato crudo del corpus y cifras de los candidatos
│   ├── train_text.py                  Entrenamiento, métricas y análisis de errores
│   ├── build_ejercicio01_pdf.py       Generador del PDF breve
│   ├── run_all.sh / run_all.ps1       Pipeline completo
│   └── embeddings_network.py          Base (LAB06, no usado en este ejercicio)
├── src/inf8239_u02/
│   ├── config.py                      Configuración por variables de entorno
│   ├── data.py                        Carga, validación, parsing y deduplicación
│   ├── modeling.py                    Pipelines y vectorizador
│   ├── experiment.py                  Experimento reproducible (partición, métricas)
│   └── errors.py                      Taxonomía de 20 categorías de error
├── tests/                             Pruebas del contrato, del modelo y de los errores
├── AI_USE_DECLARATION.md              Declaración de uso de IA
├── CAMBIOS_AL_BASE.md                 Cambios respecto al proyecto base
├── requirements.txt / -dev.txt / -cloud.txt / -colab.txt
├── pyproject.toml                     Sin modificar respecto al base
└── uv.lock                            Sin modificar respecto al base
```

## 15. Límites y uso responsable

- El corpus es **en inglés**, **anterior a 2015**, de frases cortas de reseñas
  en línea y con un balance de clases artificial (50/50) que no refleja la
  realidad. No hay clase neutral.
- El modelo **no** debe usarse para decidir sobre personas, obras o negocios.
  Es una señal de apoyo dentro del dominio y el idioma del corpus.
- La ironía, la atribución a terceros y los textos fuera del dominio no están
  cubiertos: son las limitaciones que el análisis de errores deja abiertas.
- `data/raw/` no se versiona: el corpus se obtiene siempre desde el enlace
  original con verificación de hash.
- `.env` no se versiona; no contiene secretos, pero así se mantiene el patrón
  de portabilidad del manual.

## 16. Licencia y atribución

El código de este repositorio se entrega para uso académico en el marco de
INF-8239. El corpus **no** se redistribuye: se descarga desde UCI y se cita
como *Kotzias, D. (2015). Sentiment Labelled Sentences [Dataset]. UCI Machine
Learning Repository. https://doi.org/10.24432/C57604* (CC BY 4.0).

## 17. Documentos del ejercicio

| Documento | Contenido |
|---|---|
| `docs/DATASET_CARD.md` | ficha, diccionario, transformaciones, sesgos, usos prohibidos |
| `docs/dataset_candidates.csv` | comparación verificada de los dos candidatos |
| `docs/EJERCICIO_01_PDF_BRIEF.pdf` | PDF breve de entrega |
| `AI_USE_DECLARATION.md` | herramienta, prompts, verificaciones y correcciones |
| `CAMBIOS_AL_BASE.md` | todos los cambios respecto al proyecto base y su motivo |
