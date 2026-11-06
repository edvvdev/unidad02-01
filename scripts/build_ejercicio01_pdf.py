"""Genera el PDF breve del Ejercicio 03 de la Unidad 02 (LAB04 + LAB05).

Ninguna cifra del PDF está escrita a mano: todo se lee de los artefactos
versionados (`reports/*.json`, `reports/*.csv`) y de la comparación de
candidatos (`docs/dataset_candidates.csv`). El enlace al repositorio se toma de
la variable de entorno REPO_URL.

Uso:
    REPO_URL=https://github.com/edvvdev/unidad02-01 \
      uv run --with reportlab python scripts/build_ejercicio01_pdf.py
"""

from __future__ import annotations

import csv
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

from inf8239_u02.errors import CATEGORY_DESCRIPTIONS

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
OUTPUT = DOCS / "EJERCICIO_01_PDF_BRIEF.pdf"
REPO_URL = os.getenv("REPO_URL", "https://github.com/edvvdev/unidad02-01")
STUDENT = "Edwing Perez"

NOMBRE_EJERCICIO = "Ejercicio 03 de la Unidad 02 (LAB04 + LAB05)"
NOTA_EJERCICIO = (
    "El mandato de la unidad numera este trabajo como Ejercicio 03; en el repositorio "
    "aparece como Ejercicio 01 por orden de entrega dentro de la unidad."
)

PRIMARY = colors.HexColor("#1d3557")
SECONDARY = colors.HexColor("#457b9d")
LIGHT = colors.HexColor("#f1f5f9")

NOMBRES_FUENTE = {"imdb": "IMDb", "amazon_cells": "Amazon", "yelp": "Yelp"}


def read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def miles(valor: int) -> str:
    """Entero con punto de miles: 3000 -> '3.000'."""
    return f"{valor:,}".replace(",", ".")


def build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "titulo", parent=base["Title"], fontSize=19, leading=23,
            textColor=PRIMARY, spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "subtitulo", parent=base["Normal"], fontSize=10.5, leading=14,
            alignment=TA_CENTER, textColor=SECONDARY, spaceAfter=10,
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


def table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
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


def desglose_perdidas(parse_audit: dict) -> str:
    """'261 de las 1.000 filas de IMDb, 225 de las 1.000 de Amazon y ...'."""
    partes = []
    for fuente, valores in parse_audit["por_fuente"].items():
        nombre = NOMBRES_FUENTE.get(fuente, fuente)
        partes.append(
            f"{miles(valores['perdidas_csv_ingenuo_coma'])} de las "
            f"{miles(valores['lineas_logicas'])} filas de {nombre}"
        )
    return ", ".join(partes[:-1]) + f" y {partes[-1]}"


def build_pdf() -> Path:
    audit = read_json("audit_summary.json")
    metrics = read_json("text_metrics.json")
    parse_audit = read_json("parse_audit.json")
    candidates = read_json("candidates_audit.json")
    categories = read_csv_rows(REPORTS / "errors_by_category.csv")
    revisados = read_csv_rows(REPORTS / "error_sample_20_reviewed.csv")
    comparativa = read_csv_rows(DOCS / "dataset_candidates.csv")
    aprobado_csv = next(fila for fila in comparativa if fila["decision"] == "APROBADO")
    descartado_csv = next(fila for fila in comparativa if fila["decision"] == "DESCARTADO")

    best = metrics["modelo_seleccionado"]
    best_metrics = metrics["modelos"][best]
    styles = build_styles()
    num_reglas = len(CATEGORY_DESCRIPTIONS)

    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=1.9 * cm, rightMargin=1.9 * cm,
        topMargin=1.7 * cm, bottomMargin=1.7 * cm,
        title=f"{NOMBRE_EJERCICIO} · INF-8239",
        author=STUDENT,
    )
    story = []

    # ---------- Portada ----------
    story.append(Paragraph(NOMBRE_EJERCICIO, styles["title"]))
    story.append(Paragraph(
        "Corpus público, auditoría, clasificación de sentimiento y análisis de errores",
        styles["subtitle"],
    ))
    story.append(Table(
        [
            ["Estudiante", STUDENT],
            ["Repositorio", REPO_URL],
            ["Curso", "INF-8239 Ciencia de Datos II · Unidad 02"],
            ["Ejercicio", NOMBRE_EJERCICIO],
            ["Fecha del informe", datetime.now(UTC).date().isoformat()],
        ],
        colWidths=[4.2 * cm, 11.3 * cm],
        style=TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
            ("FONTSIZE", (0, -1), (-1, -1), 9.6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Nota sobre el nombre del ejercicio.</b> {NOTA_EJERCICIO}", styles["small"]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Este informe resume la selección del corpus, la auditoría, la comparación de tres "
        "pipelines de clasificación y el análisis de errores. Todas las cifras proceden de los "
        "artefactos versionados en <b>reports/</b> y el flujo completo se reproduce con "
        "<b>scripts/run_all.sh</b>.",
        styles["body"],
    ))

    # ---------- 1. Corpus ----------
    story.append(Paragraph("1. Corpus elegido y trazabilidad", styles["h1"]))
    distribucion = audit["class_distribution"]
    story.append(Table(
        [
            ["Campo", "Valor"],
            ["Nombre", aprobado_csv["name"]],
            ["Ficha original", aprobado_csv["page"]],
            ["Descarga", aprobado_csv["url"]],
            ["Licencia", aprobado_csv["license"]],
            ["Filas / columnas", f"{miles(audit['rows'])} filas · {', '.join(audit['columns'])}"],
            ["Variable objetivo", aprobado_csv["target"]],
            ["Clases", (
                f"{audit['classes']} balanceadas ("
                f"{' / '.join(miles(valor['count']) for valor in distribucion.values())})"
            )],
            ["SHA-256 del ZIP", audit["archive_sha256"]],
            ["SHA-256 del CSV", audit["dataset_sha256"]],
            ["Duplicados", f"{audit['duplicate_rows_exact']} textos duplicados, eliminados antes de partir"],
            ["Nulos / vacíos", f"{sum(audit['nulls'].values())} nulos · {audit['empty_texts']} textos vacíos"],
            ["Longitud de texto", (
                f"p50 {audit['text_length_words']['p50']:.0f} · "
                f"p90 {audit['text_length_words']['p90']:.0f} · "
                f"p99 {audit['text_length_words']['p99']:.0f} palabras"
            )],
            ["Datos personales", aprobado_csv["personal_data"]],
        ],
        colWidths=[4.2 * cm, 11.3 * cm],
        style=table_style(),
    ))
    story.append(Spacer(1, 6))

    descartado = candidates["candidato_descartado"]
    story.append(Paragraph(
        f"<b>Candidato descartado:</b> {descartado['nombre']} "
        f"({miles(descartado['filas'])} mensajes: {miles(descartado['ham'])} ham y "
        f"{miles(descartado['spam'])} spam, {descartado['spam_pct']} % de spam, "
        f"{descartado['licencia']}). "
        f"Se descarta porque contiene mensajes reales de usuarios con números y enlaces "
        f"({descartado['filas_con_7_mas_digitos']} filas con 7 o más dígitos y "
        f"{descartado['filas_con_url_o_correo']} con URL o dirección de correo; "
        f"{descartado['filas_con_url_o_arroba']} si se cuenta cualquier mensaje con un símbolo @), "
        f"presenta un desbalance de {descartado['spam_pct']} % de spam y su objetivo no es el "
        f"sentimiento. El contraste completo está en <b>docs/dataset_candidates.csv</b>: "
        f"{descartado_csv['reason']}",
        styles["body"],
    ))

    totales = parse_audit["totales"]
    imdb = parse_audit["por_fuente"]["imdb"]
    story.append(Paragraph(
        "<b>Hallazgo sobre los datos crudos:</b> el archivo de IMDb contiene comillas dobles "
        f"dentro del texto y {parse_audit['caracteres_especiales']['u0085']} caracteres U+0085 "
        "(NEXT LINE) incrustados en frases. Un lector CSV ingenuo con separador coma pierde "
        f"{desglose_perdidas(parse_audit)}: {miles(totales['perdidas_csv_ingenuo_coma'])} de las "
        f"{miles(totales['lineas_logicas'])} filas del corpus. Con separador tabulador se pierden "
        f"{miles(imdb['perdidas_csv_ingenuo_tabulador'])} de las "
        f"{miles(imdb['lineas_logicas'])} filas de IMDb. La solución aplicada corta el archivo "
        "solo por el salto de línea y separa cada línea por su último tabulador, y recupera las "
        f"{miles(totales['recuperadas_ultimo_tabulador'])} filas completas.",
        styles["body"],
    ))

    # ---------- 2. Resultados ----------
    story.append(PageBreak())
    story.append(Paragraph("2. Resultados de los tres pipelines", styles["h1"]))
    proporcion = metrics["particion"]["proporcion_prueba"]
    story.append(Paragraph(
        f"Partición estratificada {round((1 - proporcion) * 100)}/{round(proporcion * 100)} con "
        f"semilla {metrics['particion']['semilla']} sobre "
        f"{miles(metrics['limpieza']['filas_finales'])} filas útiles "
        f"({miles(metrics['particion']['filas_entrenamiento'])} de entrenamiento y "
        f"{miles(metrics['particion']['filas_prueba'])} de prueba). El vectorizador TF-IDF está "
        "dentro de cada pipeline, de modo que no hay fuga de información. Métrica de decisión: "
        "F1 macro.",
        styles["body"],
    ))
    rows = [["Modelo", "F1 macro", "Accuracy", "Precisión macro", "Recall macro", "Seleccionado"]]
    for registro in metrics["tabla"]:
        rows.append([
            registro["nombre"],
            f"{registro['f1_macro']:.3f}",
            f"{registro['accuracy']:.3f}",
            f"{registro['precision_macro']:.3f}",
            f"{registro['recall_macro']:.3f}",
            "Sí" if registro["seleccionado"] else "No",
        ])
    story.append(Table(rows, colWidths=[5.4 * cm, 2.0 * cm, 2.0 * cm, 2.5 * cm, 2.4 * cm, 2.5 * cm],
                       style=table_style()))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Métricas por clase del modelo seleccionado", styles["h2"]))
    clase_rows = [["Clase", "Precisión", "Recall", "F1", "Support"]]
    for clase, valores in best_metrics["por_clase"].items():
        clase_rows.append([
            f"{clase} ({valores['nombre']})",
            f"{valores['precision']:.3f}", f"{valores['recall']:.3f}",
            f"{valores['f1']:.3f}", miles(valores["support"]),
        ])
    story.append(Table(clase_rows, colWidths=[4.2 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                       style=table_style()))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "El script base fijaba la regresión logística como modelo final; el manual pide guardar "
        "el mejor según la métrica, y en este corpus gana "
        f"{best_metrics['nombre']} (F1 macro {best_metrics['f1_macro']:.3f} frente a "
        f"{metrics['modelos']['logistic']['f1_macro']:.3f} de la regresión logística y "
        f"{metrics['modelos']['dummy']['f1_macro']:.3f} de la línea base).",
        styles["body"],
    ))
    for nombre, titulo in [
        ("reports/confusion_text.png", "Matriz de confusión del modelo seleccionado"),
        ("reports/models_comparison.png", "Comparación de F1 macro entre pipelines"),
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
    story.append(Paragraph("3. Análisis de errores", styles["h1"]))
    total_errores = sum(int(fila["errores"]) for fila in categories)
    story.append(Paragraph(
        f"El modelo seleccionado comete {total_errores} errores sobre "
        f"{miles(metrics['particion']['filas_prueba'])} filas de prueba. Cada error se categoriza "
        f"con {num_reglas} categorías de reglas léxicas transparentes (la primera que se activa) y "
        "se guardan las señales que la activaron. Se revisaron manualmente "
        f"{len(revisados)} errores con su interpretación en "
        "<b>notebooks/01_ejercicio01_nlp.ipynb</b> y en "
        "<b>reports/error_sample_20_reviewed.csv</b>.",
        styles["body"],
    ))
    cat_rows = [["Categoría", "Errores", "% del total"]]
    for fila in categories:
        cat_rows.append([fila["category"], fila["errores"], f"{fila['porcentaje']} %"])
    story.append(Table(cat_rows, colWidths=[7.4 * cm, 2.6 * cm, 2.6 * cm], style=table_style()))
    story.append(Spacer(1, 6))
    inactivas = num_reglas - len(categories)
    story.append(Paragraph(
        f"{inactivas} reglas no se activaron en este corpus (ironía, atribución a terceros y fuera "
        "del dominio): el corpus es homogéneo en registro, no contiene enunciados irónicos ni citas "
        "atribuidas y todas las frases son reseñas de producto, película o restaurante.",
        styles["small"],
    ))
    ruta = ROOT / "reports/errors_by_category.png"
    if ruta.exists():
        story.append(KeepTogether([
            Paragraph("Figura 3. Reparto de errores por categoría", styles["h2"]),
            Image(str(ruta), width=15.0 * cm, height=10.0 * cm),
        ]))
    ruta = ROOT / "reports/audit_overview.png"
    if ruta.exists():
        story.append(KeepTogether([
            Paragraph("Figura 4. Longitud de las frases y distribución de clases", styles["h2"]),
            Image(str(ruta), width=15.0 * cm, height=4.9 * cm),
        ]))

    # ---------- 4. Conclusion ----------
    story.append(PageBreak())
    story.append(Paragraph("4. Conclusión", styles["h1"]))
    story.append(Paragraph(
        conclusion(audit, metrics, categories, parse_audit, num_reglas), styles["body"]
    ))

    # ---------- 5. IA ----------
    story.append(Paragraph("5. Uso responsable de inteligencia artificial", styles["h1"]))
    story.append(Paragraph(ai_summary(), styles["body"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.build(story)
    return OUTPUT


def conclusion(audit: dict, metrics: dict, categories: list[dict], parse_audit: dict, num_reglas: int) -> str:
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
    totales = parse_audit["totales"]
    caracteres = parse_audit["caracteres_especiales"]
    return (
        f"La pregunta del ejercicio se respondió con un corpus público, verificado y auditable: "
        f"Sentiment Labelled Sentences de UCI, con {miles(audit['rows'])} frases en inglés, "
        f"{audit['classes']} clases balanceadas y licencia CC BY 4.0. La revisión del archivo "
        f"crudo fue decisiva: un lector CSV ingenuo habría perdido "
        f"{desglose_perdidas(parse_audit)}, es decir {miles(totales['perdidas_csv_ingenuo_coma'])} "
        f"de las {miles(totales['lineas_logicas'])} filas, y {caracteres['u0085']} caracteres U+0085 "
        "(NEXT LINE) incrustados en las frases habrían dejado otros registros sin etiqueta. "
        f"Separar cada línea por su último tabulador y cortar solo por el salto de línea recupera "
        f"las {miles(totales['recuperadas_ultimo_tabulador'])} filas completas y deja el hash "
        "SHA-256 registrado en el manifiesto de procedencia. La auditoría adicional detectó "
        f"{audit['duplicate_rows_exact']} textos duplicados, sin ninguna etiqueta contradictoria, "
        "que se eliminan antes de la partición estratificada para que ningún texto aparezca en "
        "entrenamiento y prueba a la vez.\n\n"
        f"En la comparación de modelos, la línea base obtiene un F1 macro de "
        f"{metrics['modelos']['dummy']['f1_macro']:.3f}, la regresión logística "
        f"{metrics['modelos']['logistic']['f1_macro']:.3f} y {best_metrics['nombre']} "
        f"{best_metrics['f1_macro']:.3f}. El script base fijaba la regresión logística como modelo "
        f"final, pero el manual pide guardar el mejor según la métrica, de modo que se guarda "
        f"{best_metrics['nombre']} con F1 macro {best_metrics['f1_macro']:.3f} frente a la línea "
        f"base. La matriz de confusión muestra que el modelo pierde sobre todo la clase positiva: "
        f"{falsos_negativos} reseñas positivas se clasificaron como negativas, frente a "
        f"{falsos_positivos} negativas clasificadas como positivas. El recall de la clase positiva "
        f"({clase_positiva['recall']:.3f}) queda por debajo del de la negativa "
        f"({clase_negativa['recall']:.3f}), aunque su precisión sea mayor "
        f"({clase_positiva['precision']:.3f}). El error más costoso en este contexto es, por tanto, "
        "registrar como negativa una reseña positiva.\n\n"
        f"El análisis de {sum(int(fila['errores']) for fila in categories)} errores con {num_reglas} "
        f"reglas léxicas transparentes muestra que las categorías más frecuentes son {principales}. "
        "La predominancia de la señal no cubierta indica que el fallo dominante no es un fenómeno "
        "lingüístico raro sino la combinación de rasgos: el modelo dispone del vocabulario pero no "
        "del contexto que fija el sentido de una frase. Las reglas de ironía, atribución a terceros "
        "y fuera del dominio no se activaron nunca, lo que confirma que el corpus es homogéneo en "
        "registro y que no cubre ninguna de esas dimensiones. La decisión antes de publicar es "
        "clara: el modelo sirve como señal de apoyo dentro del dominio y el idioma del corpus, "
        "nunca como veredicto sobre una persona, una obra o un negocio. Las limitaciones que deben "
        "comunicarse son importantes: el corpus es en inglés, anterior a 2015, de frases cortas de "
        "reseñas en línea, con un balance de clases artificial y sin clase neutral, por lo que las "
        "cifras no se generalizan a español, a otros periodos ni a otros dominios."
    )


def ai_summary() -> str:
    return (
        "Se utilizó un asistente de IA para apoyar la estructura del proyecto, la redacción de la "
        "documentación y la redacción de las pruebas automáticas. No se usó para generar datos, "
        "etiquetas ni resultados. Toda afirmación numérica de este informe se verificó ejecutando "
        "el código del repositorio: el hash SHA-256 del corpus se comparó con el archivo "
        "descargado, la auditoría se contrastó con un cálculo independiente, la matriz de "
        "confusión se comprobó contra los soportes por clase y cada cifra de este PDF se lee de "
        "los archivos JSON y CSV de reports/ y de la comparación de candidatos. El uso de IA quedó "
        "registrado, junto con los prompts relevantes, las partes verificadas y las correcciones "
        "realizadas, en el archivo AI_USE_DECLARATION.md del repositorio. El estudiante conserva la "
        "responsabilidad sobre los datos, el código, las referencias y las conclusiones."
    )


if __name__ == "__main__":
    ruta = build_pdf()
    print(f"PDF generado: {ruta}")
    print(f"Enlace al repositorio: {REPO_URL}")
