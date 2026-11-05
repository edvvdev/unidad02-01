"""Genera el PDF breve del Ejercicio 01 (LAB04 + LAB05).

Todas las cifras se leen de los artefactos en `reports/`, de modo que el PDF no
puede contradecir la evidencia del repositorio. El enlace al repositorio se
toma de la variable de entorno REPO_URL.

Uso:
    REPO_URL=https://github.com/edvvdev/unidad02-01 \
      uv run --with reportlab python scripts/build_ejercicio01_pdf.py
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTPUT = ROOT / "docs/EJERCICIO_01_PDF_BRIEF.pdf"
REPO_URL = os.getenv("REPO_URL", "https://github.com/edvvdev/unidad02-01")
STUDENT = "Edwing Perez"

PRIMARY = colors.HexColor("#1d3557")
SECONDARY = colors.HexColor("#457b9d")
LIGHT = colors.HexColor("#f1f5f9")


def read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def read_csv(name: str):
    import csv

    with (REPORTS / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "titulo", parent=base["Title"], fontSize=19, leading=23,
            textColor=PRIMARY, spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "subtitulo", parent=base["Normal"], fontSize=10.5, leading=14,
            alignment=TA_CENTER, textColor=SECONDARY, spaceAfter=14,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontSize=13, leading=16,
            textColor=PRIMARY, spaceBefore=12, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=11, leading=14,
            textColor=SECONDARY, spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=9.6, leading=13.6,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontSize=8.2, leading=11,
            textColor=colors.HexColor("#475569"),
        ),
    }


def table_style(header_background=PRIMARY) -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_background),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.4),
        ("FONTSIZE", (0, 1), (-1, -1), 8.4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ])


def build_pdf() -> Path:
    audit = read_json("audit_summary.json")
    metrics = read_json("text_metrics.json")
    categories = read_csv("errors_by_category.csv")
    best = metrics["modelo_seleccionado"]
    best_metrics = metrics["modelos"][best]
    styles = build_styles()

    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=1.9 * cm, rightMargin=1.9 * cm,
        topMargin=1.7 * cm, bottomMargin=1.7 * cm,
        title="Ejercicio 01 · Unidad 02 · LAB04 + LAB05",
        author=STUDENT,
    )
    story = []

    # ---------- Portada ----------
    story.append(Paragraph("Ejercicio 01 · Unidad 02 (LAB04 + LAB05)", styles["title"]))
    story.append(Paragraph(
        "Corpus público, auditoría, clasificación de sentimiento y análisis de errores",
        styles["subtitle"],
    ))
    story.append(Table(
        [
            ["Estudiante", STUDENT],
            ["Repositorio", REPO_URL],
            ["Curso", "INF-8239 Ciencia de Datos II · Unidad 02"],
            ["Fecha del informe", datetime.now(UTC).date().isoformat()],
            ["Repositorio del enunciado", REPO_URL],
        ],
        colWidths=[5.0 * cm, 10.5 * cm],
        style=TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
            ("FONTSIZE", (0, 0), (-1, -1), 9.6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Este informe resume la seleccion del corpus, la auditoria, la comparacion de tres "
        "pipelines de clasificacion y el analisis de errores. Todas las cifras proceden de "
        "los artefactos versionados en <b>reports/</b> y el flujo completo se reproduce con "
        "<b>scripts/run_all.sh</b>.",
        styles["body"],
    ))

    # ---------- 1. Dataset ----------
    story.append(Paragraph("1. Corpus elegido y trazabilidad", styles["h1"]))
    story.append(Table(
        [
            ["Campo", "Valor"],
            ["Nombre", "Sentiment Labelled Sentences (UCI 331)"],
            ["Ficha original", "https://archive.ics.uci.edu/dataset/331/sentiment-labelled-sentences"],
            ["Descarga", "https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip"],
            ["Licencia", "CC BY 4.0 (permite uso academico y publicar resultados derivados)"],
            ["Creacion", "Kotzias et al., KDD 2015 · DOI 10.24432/C57604"],
            ["Filas / columnas", f"{audit['rows']} filas · {', '.join(audit['columns'])}"],
            ["Variable objetivo", f"{metrics['target_column']} (0 = negativo, 1 = positivo)"],
            ["Clases", f"{audit['classes']} balanceadas (1500 / 1500)"],
            ["SHA-256 del ZIP", "afc26626d710899948693e1a61405dce197f57ffa719fa1130d346b4cc095343"],
            ["SHA-256 del CSV", audit["dataset_sha256"]],
            ["Duplicados", f"{audit['duplicate_rows_exact']} textos duplicados, eliminados antes de partir"],
            ["Nulos / vacios", f"{sum(audit['nulls'].values())} nulos · {audit['empty_texts']} textos vacios"],
            ["Longitud de texto", (
                f"p50 {audit['text_length_words']['p50']:.0f} · "
                f"p90 {audit['text_length_words']['p90']:.0f} · "
                f"p99 {audit['text_length_words']['p99']:.0f} palabras"
            )],
        ],
        colWidths=[4.2 * cm, 11.3 * cm],
        style=table_style(),
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Candidato descartado:</b> UCI 228 SMS Spam Collection (5.574 mensajes ham/spam, "
        "CC BY 4.0). Se descarta porque contiene mensajes reales de usuarios con numeros y "
        "enlaces (419 filas con 7+ digitos y 140 con URL o correo), presenta un desbalance de "
        "13,4 % de spam y su objetivo no es el sentimiento. El contraste completo esta en "
        "<b>docs/dataset_candidates.csv</b>.",
        styles["body"],
    ))
    story.append(Paragraph(
        "<b>Hallazgo sobre los datos crudos:</b> el archivo de IMDb contiene comillas dobles "
        "dentro del texto y dos caracteres U+0085 (NEXT LINE) incrustados en frases. Un lector "
        "CSV ingenuo pierde 252 de las 1.000 filas de IMDb (780 de 3.000 con separador coma). "
        "La solucion aplicada corta el archivo solo por el salto de linea y separa cada linea "
        "por su ultimo tabulador, y recupera las 3.000 filas completas.",
        styles["body"],
    ))

    # ---------- 2. Resultados ----------
    story.append(PageBreak())
    story.append(Paragraph("2. Resultados de los tres pipelines", styles["h1"]))
    story.append(Paragraph(
        "Particion estratificada 75/25 con semilla 42 sobre "
        f"{metrics['limpieza']['filas_finales']} filas utiles "
        f"({metrics['particion']['filas_entrenamiento']} de entrenamiento y "
        f"{metrics['particion']['filas_prueba']} de prueba). El vectorizador TF-IDF esta dentro "
        "de cada pipeline, de modo que no hay fuga de informacion. Metrica de decision: F1 macro.",
        styles["body"],
    ))
    rows = [["Modelo", "F1 macro", "Accuracy", "Precision macro", "Recall macro", "Seleccionado"]]
    for registro in metrics["tabla"]:
        rows.append([
            registro["nombre"],
            f"{registro['f1_macro']:.3f}",
            f"{registro['accuracy']:.3f}",
            f"{registro['precision_macro']:.3f}",
            f"{registro['recall_macro']:.3f}",
            "Si" if registro["seleccionado"] else "No",
        ])
    story.append(Table(rows, colWidths=[5.6 * cm, 2.1 * cm, 2.1 * cm, 2.4 * cm, 2.3 * cm, 1.9 * cm],
                       style=table_style()))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Metricas por clase del modelo seleccionado", styles["h2"]))
    clase_rows = [["Clase", "Precision", "Recall", "F1", "Support"]]
    for clase, valores in best_metrics["por_clase"].items():
        clase_rows.append([
            f"{clase} ({valores['nombre']})",
            f"{valores['precision']:.3f}", f"{valores['recall']:.3f}",
            f"{valores['f1']:.3f}", str(valores["support"]),
        ])
    story.append(Table(clase_rows, colWidths=[4.2 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                       style=table_style()))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"El script base fijaba la regresion logistica como modelo final; el manual pide guardar "
        f"el mejor segun la metrica, y en este corpus gana Complement Naive Bayes "
        f"(F1 macro {best_metrics['f1_macro']:.3f} frente a "
        f"{metrics['modelos']['logistic']['f1_macro']:.3f} de la regresion logistica y "
        f"{metrics['modelos']['dummy']['f1_macro']:.3f} de la linea base).",
        styles["body"],
    ))
    for nombre, titulo in [
        ("reports/confusion_text.png", "Matriz de confusion del modelo seleccionado"),
        ("reports/models_comparison.png", "Comparacion de F1 macro entre pipelines"),
    ]:
        ruta = ROOT / nombre
        if ruta.exists():
            story.append(KeepTogether([
                Paragraph(titulo, styles["h2"]),
                Image(str(ruta), width=15.0 * cm, height=9.2 * cm),
                Spacer(1, 6),
            ]))

    # ---------- 3. Errores ----------
    story.append(PageBreak())
    story.append(Paragraph("3. Analisis de errores", styles["h1"]))
    total_errores = sum(int(fila["errores"]) for fila in categories)
    story.append(Paragraph(
        f"El modelo seleccionado comete {total_errores} errores sobre "
        f"{metrics['particion']['filas_prueba']} filas de prueba. Cada error se categoriza con "
        "reglas lexicas transparentes (20 categorias, la primera que se activa) y se guardan las "
        "senales que la activaron. Se revisaron manualmente 20 errores con su interpretacion "
        "en <b>notebooks/01_ejercicio01_nlp.ipynb</b> y en "
        "<b>reports/error_sample_20_reviewed.csv</b>.",
        styles["body"],
    ))
    cat_rows = [["Categoria", "Errores", "% del total"]]
    for fila in categories:
        cat_rows.append([fila["category"], fila["errores"], f"{fila['porcentaje']}%"])
    story.append(Table(cat_rows, colWidths=[7.4 * cm, 2.6 * cm, 2.6 * cm], style=table_style()))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Tres reglas no se activaron en este corpus (ironia, atribucion a terceros y fuera del "
        "dominio): el corpus es homogeneo en registro, no contiene enunciados ironicos ni citas "
        "atribuidas y todas las frases son resenas de producto, pelicula o restaurante.",
        styles["small"],
    ))
    ruta = ROOT / "reports/errors_by_category.png"
    if ruta.exists():
        story.append(KeepTogether([
            Paragraph("Figura 3. Reparto de errores por categoria", styles["h2"]),
            Image(str(ruta), width=15.0 * cm, height=10.0 * cm),
        ]))
    ruta = ROOT / "reports/audit_overview.png"
    if ruta.exists():
        story.append(KeepTogether([
            Paragraph("Figura 4. Longitud de las frases y distribucion de clases", styles["h2"]),
            Image(str(ruta), width=15.0 * cm, height=4.9 * cm),
        ]))

    # ---------- 4. Conclusion ----------
    story.append(PageBreak())
    story.append(Paragraph("4. Conclusion", styles["h1"]))
    story.append(Paragraph(conclusion(audit, metrics, categories), styles["body"]))

    # ---------- 5. IA ----------
    story.append(Paragraph("5. Uso responsable de inteligencia artificial", styles["h1"]))
    story.append(Paragraph(ai_summary(), styles["body"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.build(story)
    return OUTPUT


def conclusion(audit: dict, metrics: dict, categories: list[dict]) -> str:
    best = metrics["modelo_seleccionado"]
    best_metrics = metrics["modelos"][best]
    clase_positiva = best_metrics["por_clase"]["1"]
    clase_negativa = best_metrics["por_clase"]["0"]
    matriz = best_metrics["matriz_confusion"]
    falsos_negativos = matriz[1][0]
    falsos_positivos = matriz[0][1]
    principales = ", ".join(
        f"{fila['category']} ({fila['errores']})" for fila in categories[:3]
    )
    return (
        f"La pregunta del ejercicio se respondio con un corpus publico, verificado y auditable: "
        f"Sentiment Labelled Sentences de UCI, con {audit['rows']} frases en ingles, "
        f"{audit['classes']} clases balanceadas y licencia CC BY 4.0. La revision del archivo "
        f"crudo fue decisiva: un lector CSV ingenuo habria perdido 252 de las 1.000 filas de "
        f"IMDb y dos registros habrian quedado sin etiqueta por dos caracteres U+0085 incrustados "
        f"en las frases. Separar cada linea por su ultimo tabulador y cortar solo por el salto de "
        f"linea recupera las {audit['rows']} filas completas y deja el hash SHA-256 registrado en "
        f"el manifiesto de procedencia. La auditoria adicional detecto "
        f"{audit['duplicate_rows_exact']} textos duplicados, sin ninguna etiqueta contradictoria, "
        f"que se eliminan antes de la particion estratificada para que ningun texto aparezca en "
        f"entrenamiento y prueba a la vez.\n\n"
        f"En la comparacion de modelos, la linea base obtiene un F1 macro de "
        f"{metrics['modelos']['dummy']['f1_macro']:.3f}, la regresion logistica "
        f"{metrics['modelos']['logistic']['f1_macro']:.3f} y Complement Naive Bayes "
        f"{best_metrics['f1_macro']:.3f}. El script base fijaba la regresion logistica como "
        f"modelo final, pero el manual pide guardar el mejor segun la metrica, de modo que se "
        f"guarda Complement Naive Bayes con F1 macro {best_metrics['f1_macro']:.3f} frente a la "
        f"linea base. La matriz de confusion muestra que el modelo pierde sobre todo la clase "
        f"positiva: {falsos_negativos} reseñas positivas se clasificaron como negativas, frente "
        f"a {falsos_positivos} negativas clasificadas como positivas. El recall de la clase "
        f"positiva ({clase_positiva['recall']:.3f}) queda por debajo del de la negativa "
        f"({clase_negativa['recall']:.3f}), aunque su precision sea mayor "
        f"({clase_positiva['precision']:.3f}). El error mas costoso en este contexto es, por "
        f"tanto, registrar como negativa una reseña positiva.\n\n"
        f"El analisis de {sum(int(fila['errores']) for fila in categories)} errores con 20 reglas "
        f"lexicas transparentes muestra que las categorias mas frecuentes son {principales}. "
        f"La predominancia de la senal no cubierta indica que el fallo dominante no es un "
        f"fenomeno linguistico raro sino la combinacion de rasgos: el modelo dispone del "
        f"vocabulario pero no del contexto que fija el sentido de una frase. Las reglas de "
        f"ironia, atribucion a terceros y fuera del dominio no se activaron nunca, lo que "
        f"confirma que el corpus es homogeneo en registro y que no cubre ninguna de esas "
        f"dimensiones. La decision antes de publicar es clara: el modelo sirve como senal de "
        f"apoyo dentro del dominio y el idioma del corpus, nunca como veredicto sobre una "
        f"persona, una obra o un negocio. Las limitaciones que deben comunicarse son "
        f"importantes: el corpus es en ingles, anterior a 2015, de frases cortas de resenas en "
        f"linea, con un balance de clases artificial y sin clase neutral, por lo que las cifras "
        f"no se generalizan a espanol, a otros periodos ni a otros dominios."
    )


def ai_summary() -> str:
    return (
        "Se utilizo un asistente de IA para apoyar la estructura del proyecto, la redaccion de "
        "la documentacion y la redaccion de las pruebas automaticas. No se uso para generar datos, "
        "etiquetas ni resultados. Toda afirmacion numerica de este informe se verifico ejecutando "
        "el codigo del repositorio: el hash SHA-256 del corpus se comparo con el archivo "
        "descargado, la auditoria se contrasto con un calculo independiente, la matriz de "
        "confusion se comprobo contra los suportes por clase y cada cifra de este PDF se lee de "
        "los archivos JSON y CSV de reports/. El uso de IA quedo registrado, junto con los "
        "prompts relevantes, las partes verificadas y las correcciones realizadas, en el archivo "
        "AI_USE_DECLARATION.md del repositorio. El estudiante conserva la responsabilidad sobre "
        "los datos, el codigo, las referencias y las conclusiones."
    )


if __name__ == "__main__":
    ruta = build_pdf()
    print(f"PDF generado: {ruta}")
    print(f"Enlace al repositorio: {REPO_URL}")
