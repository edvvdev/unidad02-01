# Ficha del dataset · Sentiment Labelled Sentences (UCI 331)

## Identificación

| Campo | Valor |
|---|---|
| Nombre | Sentiment Labelled Sentences |
| Responsable del corpus | Dimitrios Kotzias (creador), UCI Machine Learning Repository (distribuidor) |
| Ficha original | https://archive.ics.uci.edu/dataset/331/sentiment-labelled-sentences |
| Enlace de descarga | https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip |
| DOI | 10.24432/C57604 |
| Cita recomendada | Kotzias, D. (2015). *Sentiment Labelled Sentences* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C57604 |
| Paper de origen | Kotzias, D., Denil, M., de Freitas, N. y Smyth, P. (2015). *From Group to Individual Labels using Deep Features*. KDD 2015 |
| Versión / fecha de descarga | Archivo con fecha interna 2016-07-05, descargado y verificado el 2026-11-05 |
| Licencia | **CC BY 4.0** (permite descargar, analizar y publicar resultados derivados con atribución) |
| Idioma | Inglés |
| SHA-256 del ZIP | `afc26626d710899948693e1a61405dce197f57ffa719fa1130d346b4cc095343` |
| SHA-256 del CSV normalizado | `6410f6b155301ad6a1cd47d90de2e44a5a82f938d4f13d500400a1eafea069fd` |
| Responsable académico del uso | Edwing Perez (INF-8239 Ciencia de Datos II, Unidad 02) |

## Propósito y variable objetivo

**Pregunta que responde el corpus:** ¿permite un corpus público y reproducible
clasificar automáticamente el sentimiento (positivo / negativo) de una reseña
breve en línea, y qué errores comete ese clasificador?

- **Unidad de análisis:** una frase (oración) extraída de una reseña en línea.
- **Variable objetivo (`score`):** binaria y observable en el momento de
  predecir. `0` = sentimiento negativo, `1` = sentimiento positivo.
- **Clases:** 2, balanceadas (1.500 negativas y 1.500 positivas).
- **Métrica de decisión del ejercicio:** F1 macro (promedia igual las dos clases;
  la accuracy por sí sola es engañosa si el balance cambia).
- **Variables disponibles al momento de predecir:** únicamente el texto.
  No hay metadatos de autor, fecha, producto ni puntuación, por lo que no
  existe información que solo esté disponible después de la etiqueta.

## Procedimiento de obtención

```bash
cp .env.example .env          # la configuración real ya viene en .env.example
uv run python scripts/download_data.py
```

El script `scripts/download_data.py`:

1. descarga el ZIP desde el enlace original de la ficha de UCI;
2. calcula y muestra el **SHA-256** del archivo descargado y lo compara con
   `DATASET_SHA256`; si no coincide, **no normaliza** y termina con error;
3. extrae y normaliza los tres archivos etiquetados a `data/raw/dataset.csv`
   con las columnas `sentence`, `score`, `source`;
4. escribe el manifiesto `data/raw/dataset.source.txt` con URL, licencia, hash
   del ZIP, hash del CSV normalizado, número de filas y fecha de generación.

Todo es reproducible desde el repositorio: no hay rutas absolutas, ni
credenciales, ni archivos subidos por terceros.

## Transformaciones realizadas

| # | Transformación | Motivo |
|---|---|---|
| 1 | Separación de cada línea por su **último tabulador** | El archivo de IMDb contiene comillas dobles dentro del texto; un lector CSV con comillas las toma como delimitadores y descarta filas válidas. |
| 2 | Corte de línea **solo por `\n`** | El archivo de IMDb contiene 2 caracteres U+0085 (NEXT LINE) dentro de frases; `str.splitlines()` los trata como saltos de línea y deja 2 registros huérfanos. |
| 3 | Sustitución de U+0085/U+2028/U+2029 por un espacio | Normalización de saltos de línea incrustados dentro de la frase. |
| 4 | Eliminación de espacios al inicio y al final de la frase y de la etiqueta | Evita filas con espacios sobrantes. |
| 5 | Se conservan las 3.000 filas; **0 líneas descartadas** | Verificado: 3.000 filas tras normalizar. |
| 6 | Columna `source` = `imdb` / `amazon_cells` / `yelp` | Permite auditar el desbalance y el comportamiento por fuente. |
| 7 | Eliminación de 18 textos duplicados **antes** de la partición | Prevención de fuga de información. |

### Hallazgo sobre los datos crudos (evidencia de revisión manual)

Un lector CSV ingenuo habría reducido el corpus de forma silenciosa:

| Lectura | Filas obtenidas de 3.000 | Pérdida |
|---|---|---|
| `pd.read_csv(..., sep=",")` | error de parseo (`ParserError`) | — |
| `pd.read_csv(..., sep=",")` con `on_bad_lines="warn"` | 2.220 | 780 filas |
| `pd.read_csv(..., sep="\t")` (lector por defecto con comillas) | 2.748 | 252 filas, todas de IMDb |
| `split("\n")` + separación por el último tabulador (implementación propia) | **3.000** | **0** |

La pérdida de 252 filas en el archivo de IMDb coincide exactamente con el
número indicado en el enunciado del ejercicio y se verificó sobre el archivo
descargado.

## Diccionario de datos

| Columna | Tipo | Descripción | Valores o unidad | Fuente | Momento de disponibilidad | Transformación | Riesgo |
|---|---|---|---|---|---|---|---|
| `sentence` | texto (object) | Frrase de reseña de la que se predice el sentimiento | Texto libre en inglés; longitud p50 = 55 caracteres, p90 = 121, p99 = 213, máximo 477; p50 = 10 palabras, p90 = 22, p99 = 36 | Frases extraídas de reseñas de IMDb, Amazon (celulares) y Yelp | Disponible en el momento de predecir (es la entrada del modelo) | Recorte por tabulador, normalización de espacios y de saltos de línea incrustados | Riesgo bajo de información personal: 0 correos, 0 teléfonos y 0 URLs; sí aparecen palabras coloquiales o groseras puntuales |
| `score` | entero (int64) | Etiqueta de sentimiento | `0` = negativo (1.500 filas), `1` = positivo (1.500 filas) | Etiquetado manual del equipo del paper (Kotzias et al., 2015) | Etiqueta disponible solo después de la predicción (es el objetivo) | Sin transformación | Riesgo medio: el criterio de etiquetado es binario y automatizado sobre opiniones; no admite matices ni "neutral" |
| `source` | texto (object) | Subsitio de origen de la frase | `imdb` (1.000), `amazon_cells` (1.000), `yelp` (1.000) | Metadato del archivo de origen | Disponible en el momento de predecir (se usa solo para auditoría, no como característica del modelo) | Etiqueta añadida al normalizar | Riesgo bajo; no se usa como variable predictora |

**No existen** variables de fecha, autor, producto, precio, lugar ni demografía.
El corpus no contiene datos personales identificables.

## Calidad observada

Cifras verificadas sobre el archivo real (respaldo: `reports/audit_summary.json`):

| Comprobación | Resultado |
|---|---|
| Filas y columnas | 3.000 filas × 3 columnas |
| Nulos | 0 en las tres columnas |
| Textos vacíos | 0 |
| Clases | 2 (1.500 / 1.500, 50 % / 50 %) |
| Duplicados exactos de texto | 18 filas eliminadas (36 filas implicadas en 18 grupos) |
| Duplicados tras normalizar (minúsculas, sin acentos ni signos) | 28 |
| Duplicados con **etiqueta contradictoria** | 0 |
| Distribución por fuente | 1.000 / 1.000 / 1.000 |
| Longitud de texto (caracteres) | mínimo 5, media 64,6, p50 55, p90 121, p99 213, máximo 477 |
| Longitud de texto (palabras) | mínimo 1, media 11,8, p50 10, p90 22, p99 36, máximo 71 |
| Filas útiles tras deduplicar | 2.982 |

## Cinco ejemplos anonimizados

Fragmentos reales del corpus, reproducidos tal cual aparecen en
`data/raw/dataset.csv` (son reseñas públicas; no contienen nombres de personas,
correos, teléfonos ni identificadores). La columna `score` es la etiqueta
original.

| # | `sentence` | `score` | `source` |
|---|---|---|---|
| 1 | A very, very, very slow-moving, aimless movie about a distressed, drifting young man. | 0 | imdb |
| 2 | The best scene in the movie was when Gerardo is trying to find a song that keeps running through his head. | 1 | imdb |
| 3 | So there is no way for me to plug it in here in the US unless I go by a converter. | 0 | amazon_cells |
| 4 | Good case, Excellent value. | 1 | amazon_cells |
| 5 | Crust is not good. | 0 | yelp |

Los ejemplos 1, 3 y 5 muestran los dos casos que concentran los errores del
modelo: la negación ("is not good") y el énfasis negativo. El ejemplo 5
muestra por qué la etiqueta puede ser discutible: "Crust is not good" se
etiquetó como negativo aunque la reseña completa pudiera ser positiva.

## Prevención de fuga de información

| Riesgo | Mitigación implementada | Dónde se verifica |
|---|---|---|
| Texto duplicado en entrenamiento y prueba | Los 18 duplicados se eliminan **antes** de la partición | `src/inf8239_u02/experiment.py::prepare_frame`; prueba `test_experiment_deduplicates_before_splitting` |
| Vocabulario o pesos IDF calculados con todo el corpus | El `TfidfVectorizer` está **dentro** del `Pipeline` | `src/inf8239_u02/modeling.py::build_models`; prueba `test_vectorizer_stays_inside_the_pipeline` |
| Partición no reproducible | `train_test_split` estratificado con `random_state = 42` | `src/inf8239_u02/experiment.py::split_data` |
| Selección de modelo sobre el conjunto de prueba | Los tres modelos se comparan con la **misma** partición y se elige el mejor por F1 macro; la comparación se reporta completa en `reports/text_metrics.csv` | `scripts/train_text.py` |
| Métricas infladas por clases desbalanceadas | Se reporta F1 macro, recall por clase y matriz de confusión, no solo accuracy | `reports/text_metrics.json` |

## Sesgos previsibles

1. **Sesgo de fuente y de contexto.** Las tres fuentes son sitios de reseñas
   en línea de habla inglesa; no representan voz hablada, documentos, redes
   sociales ni textos de apoyo al cliente.
2. **Sesgo temporal.** Las reseñas son anteriores a 2015 (el dataset se publicó
   en 2015), por lo que el vocabulario de productos y el lenguaje no reflejan
   la realidad actual.
3. **Sesgo de longitud.** Las frases son cortas (p50 = 10 palabras). El modelo
   se apoya en señales léxicas locales y no en contexto discursivo.
4. **Sesgo de polaridad artificial.** El balance exacto 50/50 es producto de la
   selección del equipo de UCI ("500 positivas y 500 negativas por sitio"), no
   de la distribución real de reseñas.
5. **Sesgo de registro.** El corpus es mayoritariamente formal; aparecen
   algunas expressions coloquiales y palabras groseras puntuales, y no hay
   ironía marcada ni textos en dialecto.
6. **Sesgo de etiquetado.** La etiqueta es binaria: no existe clase neutral.
   Una reseña tibia, sarcástica o mixta se fuerza a un extremo.

## Población no cubierta

- Hablantes no nativos de inglés y cualquier texto fuera del inglés.
- Reseñas posteriores a 2015 y productos que no existían entonces.
- Reseñas con sentimiento **neutro**, mixto o sin valoración.
- Texto largo, párrafos, mensajes privados, llamadas, correos o redes sociales.
- Usuarios reales de los sistemas: el corpus no contiene datos de personas y
  no permite evaluar riesgo por grupo demográfico.

## Usos prohibidos

- **No** usar el modelo (ni este corpus) para decidir sobre personas: contrataciones,
  puntuaciones punitivas, evaluación de calidad laboral, crédito o servicios.
- **No** presentar la predicción como una verdad o como una medida de calidad
  de una persona, obra o negocio.
- **No** generalizar las métricas a español, a otros dominios, a otras fuentes
  o a periodos posteriores sin volver a evaluar.
- **No** redistribuir el corpus con una licencia distinta de CC BY 4.0 ni
 omitir la atribución a UCI y al paper de Kotzias et al. (2015).
- **No** usar el corpus con fines de vigilancia, perfilado o decisión
  automatizada sobre personas.

## Referencias

- UCI Machine Learning Repository. *Sentiment Labelled Sentences* (dataset 331).
  https://archive.ics.uci.edu/dataset/331/sentiment-labelled-sentences
- Kotzias, D., Denil, M., de Freitas, N. y Smyth, P. (2015). *From Group to
  Individual Labels using Deep Features*. KDD 2015.
- Maas, A. L. et al. (2011). *Learning Word Vectors for Sentiment Analysis* (origen IMDb).
- McAuley, D. et al. (2013). *Hidden Factors and Hidden Topics* (origen Amazon).
- Manual de laboratorios guiados, Unidad 02, INF-8239 Ciencia de Datos II.
