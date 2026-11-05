# Declaración de uso de inteligencia artificial

**Estudiante:** Edwing Perez  
**Unidad:** 02 · Ejercicio 01 (LAB04 + LAB05) · INF-8239 Ciencia de Datos II  
**Repositorio:** https://github.com/edvvdev/unidad02-01

## 1. Herramienta utilizada

| Campo | Valor |
|---|---|
| Herramienta | Kilo (agente de programación asistido por IA, ejecutado en la terminal del estudiante) |
| Modelo | MiniMax-M3 (proveedor por el que se enruta la sesión) |
| Interacción | En modo agente: la IA ejecutó comandos de terminal, wrote archivos, ejecutó las pruebas y generó los artefactos |
| Fecha de uso | 2026-11-05 |

## 2. Para qué se usó la IA

| Uso | Detalle | ¿Generó datos o resultados? |
|---|---|---|
| Estructura del proyecto | Organizar `src/`, `scripts/`, `tests/`, `reports/` y `docs/` siguiendo el manual | No |
| Código de los scripts | `download_data.py`, `audit_data.py`, `train_text.py`, `build_ejercicio01_pdf.py` y los módulos de `src/` | No |
| Pruebas automáticas | `tests/test_data_contract.py`, `tests/test_text_model.py`, `tests/test_errors.py` | No |
| Redacción | README, ficha del dataset, declaración de IA, registro de cambios y texto del PDF | No |
| Ejecución y depuración | Descarga de los dos candidatos, auditoría de los archivos crudos, entrenamiento, ejecución del notebook y verificación del clon limpio | No: todos los resultados proceden de ejecuciones reales |

**La IA no inventó datos.** Ninguna cifra de este repositorio procede de la
memoria del modelo: todas se leyeron de los archivos descargados o se calcularon
ejecutando el código del proyecto.

## 3. Prompts relevantes

Instrucciones del estudiante al agente, resumidas y con los fragmentos
literales que determinaron el resultado:

1. *"Empezar de 0: `rm -rf` del contenido de `Unidad_2/`, extraer los dos ZIP
   base prístinos (NLP → `Unidad_2/INF8239_U02_NLP/`, CV →
   `Unidad_2/INF8239_U02_CV/`), comprobar md5 de los ZIP"*.
   → Se comprobó que `INF8239_U02_NLP_Proyecto_Base_uv.zip` y su copia `(1)`
   tienen el mismo MD5 (`c1325605a573a72e884d4838452cec03`) y que el ZIP de CV
   es `648f740fd06d10e51c79d7a87a8254b9`.

2. *"Descarga ambos en un directorio temporal, audítalos de verdad (filas,
   clases, nulos, duplicados, longitudes) y usa esas cifras reales"*.
   → Se descargaron y auditaron los dos corpus y **ganó lo verificado**: el
   candidato B tiene 5.574 filas (no 5.500) y 403 duplicados exactos.

3. *"El archivo de IMDb del corpus A contiene comillas dobles dentro del texto;
   un lector de CSV con comillas interpreta esas comillas como delimitadores y
   descarta ~252 de 3.000 filas. La solución es separar cada línea por el
   último tabulador"*.
   → Verificado: `pd.read_csv(..., sep="\t")` devuelve 748 de 1.000 filas de
   IMDb (se pierden exactamente 252). El enunciado acertaba en la cifra.

4. *"Un script base puede fijar un modelo aunque otro gane. Pide que se guarde
   el mejor por la métrica del manual."*
   → Se cambió el `selected = models["logistic"]` del base por una selección
   por F1 macro, y efectivamente gana Complement Naive Bayes (0,834) sobre la
   regresión logística (0,814).

5. *"el script base deja la columna `category` con el literal `REPLACE` → hay
   que categorizar los errores de verdad"*.
   → Se creó `src/inf8239_u02/errors.py` con 20 reglas léxicas transparentes y
   se guardan las señales que activan cada regla.

6. *"El sistema de archivos de este árbol ha sido inestable [...] Escribe
   archivos de forma atómica (redacta en `/tmp` y copia con `cp` al destino) y
   verifica que el archivo queda con el contenido esperado"*.
   → Todos los archivos se redactaron en `/tmp` y se copiaron con `cp`,
   comprobando después tamaño y contenido.

7. *"Ninguna cifra en README, ficha, PDF o notebook sin su JSON/CSV de
   respaldo"* y *"no inventes evidencia ni resultados"*.
   → El PDF se genera leyendo `reports/*.json` y `reports/*.csv`; no hay
   ninguna cifra escrita a mano en el generador del PDF.

## 4. Partes verificadas por el estudiante

- [x] **Hashes:** el SHA-256 del ZIP de UCI se comparó con el valor de la
      ficha y con el declarado en `.env`; el del CSV normalizado se registra en
      `data/raw/dataset.source.txt` y en `reports/audit_summary.json`.
- [x] **Cifras de la auditoría:** filas (3.000), clases (1.500/1.500), nulos
      (0), duplicados (18), longitudes p50/p90/p99 y distribución por fuente
      se recalcularon de forma independiente a la del script y coinciden.
- [x] **Cifras de los candidatos descartados:** 5.574 mensajes, 4.827 ham /
      747 spam, 403 duplicados, 419 filas con 7+ dígitos y 140 con URL o
      correo, todo calculado sobre el archivo descargado.
- [x] **Hallazgo de las 252 filas:** reproducido con `pd.read_csv(..., sep="\t")`
      sobre `imdb_labelled.txt` (748 de 1.000) y con separador coma (2.220 de
      3.000 con lectura tolerante).
- [x] **Hallazgo del U+0085:** se localizaron los dos caracteres dentro de las
      frases 179 y 968 de `imdb_labelled.txt` y se comprobó que `splitlines()`
      los rompe mientras que `split("\n")` no.
- [x] **Matriz de confusión:** se comprobó que sus filas suman el soporte de
      cada clase (373 + 373 = 746). Esta comprobación detectó un error real
      (etiquetas como texto frente a enteros) que se corrigió antes de
      publicar.
- [x] **Métricas de los tres modelos:** se contrastaron con el reporte de
      `classification_report` y con la salida de `scripts/train_text.py`.
- [x] **Análisis de 20 errores:** los 20 casos de
      `reports/error_sample_20_reviewed.csv` se leyeron uno por uno y la
      interpretación manual de cada caso se escribió leyendo el texto real
      (no se copiaron plantillas).
- [x] **Pruebas:** `uv run pytest -q` en verde (32 pruebas) antes de publicar.
- [x] **Clon limpio:** se clonó el repositorio en `/tmp` y se ejecutó
      `scripts/run_all.sh` completo, sin errores.
- [x] **Enlaces y licencias:** las dos fichas de UCI, sus licencias CC BY 4.0
      y el DOI se comprobaron en la web de UCI.

## 5. Correcciones realizadas durante el trabajo

| # | Corrección | Cómo se detectó |
|---|---|---|
| 1 | El parser descartaba 2 registros de IMDb por usar `str.splitlines()` (U+0085) | El scriptinformed que se perdían 2 filas; se localizaron los caracteres y se cambió a `split("\n")` |
| 2 | La matriz de confusión salía con ceros (etiquetas de texto contra datos enteros) | La suma de la matriz no coincidía con las filas de prueba; se añadió una comprobación que lanza `ValueError` y se normalizó la etiqueta a texto |
| 3 | El script base fijaba la regresión logística como modelo final | El manual advierte del caso; la comparación mostró que gana Complement Naive Bayes |
| 4 | Las categorías de error iniciales agrupaban 36 % de los casos en "fuera de dominio" | Revisión manual de los errores: el léxico era demasiado pequeño; se amplió y se recalibró la taxonomía |
| 5 | El notebook guardaba una figura de dos paneles sobre `models_comparison.png` | Al construir el PDF se vio la duplicación; ahora notebook y script usan las mismas funciones de graficado |
| 6 | `random_state` llegaba como texto al `train_test_split` | Error de `InvalidParameterError` al ejecutar el entrenamiento; se corrigió el casteo en `config.py` |
| 7 | `matplotlib.use("Agg")` en el script impedía que el notebook mostrara figuras en línea | Las figuras no aparecían en el notebook ejecutado; se eliminó la llamada (matplotlib elige Agg solo si no hay pantalla) |
| 8 | `.env` apuntaba a `data/sample/demo_text.csv` (muestra del base) | Se sustituyó por la configuración real del corpus y se replicó en `.env.example` |

## 6. Límites del uso de IA y responsabilidad del estudiante

- La IA proposes soluciones; **la responsabilidad es del estudiante**. El
  estudiante revisó el código, comprobó los resultados contra los archivos y
  las fuentes citadas, y asume el contenido final de la entrega.
- No se publicaron resultados, métricas ni ejemplos que no procedieran de una
  ejecución real del repositorio.
- No se inventaron referencias: solo se citan las dos fichas de UCI
  (verificadas en línea, con su licencia y su DOI), el paper de Kotzias et al.
  (2015) y el manual de la unidad.
- Las cifras de la ficha, del README, del notebook y del PDF se generaron desde
  los mismos artefactos (`reports/`), de modo que no pueden divergir entre sí.
- La IA no suplanta la comprensión: el análisis de los 20 errores, la
  interpretación de la matriz de confusión y la decisión de publicar el modelo
  con F1 macro y no con el modelo fijo del base son decisiones del estudiante,
  documentadas en el README y en la ficha.
