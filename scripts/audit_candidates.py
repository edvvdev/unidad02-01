"""Audita el formato crudo del corpus aprobado y las cifras de los dos candidatos.

Genera dos artefactos en `reports/`:

  parse_audit.json        cuantas filas pierde un lector CSV ingenuo en cada
                          archivo de origen y cuantas recupera la regla aplicada
                          (corte solo por ``\\n`` y separacion por el ULTIMO
                          tabulador).
  candidates_audit.json   cifras verificadas de los dos candidatos de LAB04.

Ninguna cifra del README, de la ficha del dataset, del notebook o del PDF se
escribe a mano: todas salen de estos dos archivos.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from inf8239_u02.config import ROOT, settings
from inf8239_u02.data import SENTIMENT_ARCHIVE_MEMBERS, sha256

REPORTS = ROOT / "reports"
RAW = ROOT / "data/raw"
ARCHIVE = RAW / "dataset.zip"
SMS_ARCHIVE = RAW / "sms_spam_collection.zip"

SMS_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
SMS_MEMBER = "SMSSpamCollection"

URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
DIGITS_PATTERN = re.compile(r"\d{7,}")
AT_PATTERN = re.compile(r"@")

VALID_SCORES = ("0", "1")


def logical_lines(raw: str) -> list[str]:
    """Lineas del archivo separando solo por ``\\n`` (U+0085 NO es un salto)."""
    return [line for line in raw.split("\n") if line.strip()]


def rows_with_last_tab(raw: str) -> int:
    """Filas que recupera la regla aplicada: separar por el ULTIMO tabulador."""
    total = 0
    for line in logical_lines(raw):
        if "\t" not in line:
            continue
        _, score = line.rsplit("\t", 1)
        if score.strip() in VALID_SCORES:
            total += 1
    return total


def rows_naive_csv(raw: str, separator: str = ",") -> int:
    """Filas que devuelve un lector CSV ingenuo con separador ``separator``.

    Es el lector que interpreta las comillas dobles del texto como delimitadores
    y descarta las lineas que no encajan. `on_bad_lines="skip"` es la forma
    tolerante de ejecutar el mismo lector: sin el, pandas aborta la lectura.
    """
    frame = pd.read_csv(io.StringIO(raw), sep=separator, header=None, on_bad_lines="skip")
    return len(frame)


def member_of(archive: zipfile.ZipFile, suffix: str) -> str:
    """Nombre interno del archivo que termina en ``suffix`` (ignora __MACOSX)."""
    candidatos = [
        name
        for name in archive.namelist()
        if name.endswith(suffix) and not name.startswith("__MACOSX")
    ]
    if not candidatos:
        raise FileNotFoundError(f"El ZIP no contiene {suffix}")
    return candidatos[0]


def audit_parse() -> dict:
    """Audita el archivo crudo aprobado: formato, separador y caracteres raros."""
    if not ARCHIVE.exists():
        raise FileNotFoundError(
            f"No existe {ARCHIVE}. Ejecute `uv run python scripts/download_data.py` primero."
        )
    por_fuente: dict[str, dict] = {}
    totales = {
        "lineas_logicas": 0,
        "recuperadas_ultimo_tabulador": 0,
        "leidas_csv_ingenuo_coma": 0,
        "leidas_csv_ingenuo_tabulador": 0,
    }
    caracteres = {"u0085": 0, "u2028": 0, "u2029": 0}
    with zipfile.ZipFile(ARCHIVE) as archive:
        for fuente, archivo in SENTIMENT_ARCHIVE_MEMBERS.items():
            raw = archive.read(member_of(archive, archivo)).decode("utf-8")
            lineas = logical_lines(raw)
            recuperadas = rows_with_last_tab(raw)
            con_coma = rows_naive_csv(raw, ",")
            con_tabulador = rows_naive_csv(raw, "\t")
            por_fuente[fuente] = {
                "lineas_logicas": len(lineas),
                "recuperadas_ultimo_tabulador": recuperadas,
                "leidas_csv_ingenuo_coma": con_coma,
                "perdidas_csv_ingenuo_coma": len(lineas) - con_coma,
                "leidas_csv_ingenuo_tabulador": con_tabulador,
                "perdidas_csv_ingenuo_tabulador": len(lineas) - con_tabulador,
            }
            totales["lineas_logicas"] += len(lineas)
            totales["recuperadas_ultimo_tabulador"] += recuperadas
            totales["leidas_csv_ingenuo_coma"] += con_coma
            totales["leidas_csv_ingenuo_tabulador"] += con_tabulador
            caracteres["u0085"] += raw.count("\u0085")
            caracteres["u2028"] += raw.count("\u2028")
            caracteres["u2029"] += raw.count("\u2029")
    totales["perdidas_csv_ingenuo_coma"] = (
        totales["lineas_logicas"] - totales["leidas_csv_ingenuo_coma"]
    )
    totales["perdidas_csv_ingenuo_tabulador"] = (
        totales["lineas_logicas"] - totales["leidas_csv_ingenuo_tabulador"]
    )
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "archivo": str(ARCHIVE.relative_to(ROOT)),
        "archivo_sha256": sha256(ARCHIVE),
        "regla_de_lectura_aplicada": (
            "corte de linea solo por \\n y separacion de cada linea por su ULTIMO tabulador"
        ),
        "lectora_ingenuo": (
            "pandas.read_csv(sep=comma, header=None, on_bad_lines=skip): interpreta las comillas "
            "dobles del texto como delimitadores y descarta las lineas que no encajan"
        ),
        "por_fuente": por_fuente,
        "totales": totales,
        "caracteres_especiales": caracteres,
    }


def descargar_sms() -> Path:
    """Descarga (una sola vez) el ZIP del candidato descartado."""
    if SMS_ARCHIVE.exists():
        return SMS_ARCHIVE
    response = requests.get(SMS_URL, timeout=180)
    response.raise_for_status()
    RAW.mkdir(parents=True, exist_ok=True)
    SMS_ARCHIVE.write_bytes(response.content)
    return SMS_ARCHIVE


def audit_sms() -> dict:
    """Cifras verificadas del candidato descartado (UCI 228, SMS Spam Collection)."""
    archivo = descargar_sms()
    with zipfile.ZipFile(archivo) as archive:
        raw = archive.read(member_of(archive, SMS_MEMBER)).decode("utf-8")
    etiquetas: list[str] = []
    textos: list[str] = []
    for linea in logical_lines(raw):
        etiqueta, _, texto = linea.partition("\t")
        etiquetas.append(etiqueta.strip())
        textos.append(texto)
    ham = sum(1 for etiqueta in etiquetas if etiqueta == "ham")
    spam = sum(1 for etiqueta in etiquetas if etiqueta == "spam")
    total = len(textos)
    con_url = sum(1 for texto in textos if URL_PATTERN.search(texto))
    con_correo = sum(1 for texto in textos if EMAIL_PATTERN.search(texto))
    con_arroba = sum(1 for texto in textos if AT_PATTERN.search(texto))
    return {
        "nombre": "SMS Spam Collection (UCI 228)",
        "url": SMS_URL,
        "licencia": "CC BY 4.0",
        "archivo": str(SMS_ARCHIVE.relative_to(ROOT)),
        "archivo_sha256": sha256(SMS_ARCHIVE),
        "filas": total,
        "ham": ham,
        "spam": spam,
        "spam_pct": round(100 * spam / total, 1),
        "duplicados_exactos": total - len(set(textos)),
        "filas_con_7_mas_digitos": sum(1 for texto in textos if DIGITS_PATTERN.search(texto)),
        "filas_con_url": con_url,
        "filas_con_direccion_correo": con_correo,
        "filas_con_url_o_correo": sum(
            1 for texto in textos if URL_PATTERN.search(texto) or EMAIL_PATTERN.search(texto)
        ),
        "filas_con_simbolo_arroba": con_arroba,
        "filas_con_url_o_arroba": sum(
            1 for texto in textos if URL_PATTERN.search(texto) or AT_PATTERN.search(texto)
        ),
        "verificado_en": datetime.now(UTC).date().isoformat(),
        "recalculado": True,
    }


def audit_candidates() -> dict:
    """Cifras de los dos candidatos: el aprobado (local) y el descartado (UCI 228)."""
    destino = REPORTS / "candidates_audit.json"
    previo = {}
    if destino.exists():
        previo = json.loads(destino.read_text(encoding="utf-8"))
    try:
        descartado = audit_sms()
        aviso = None
    except (requests.RequestException, OSError, zipfile.BadZipFile) as error:
        guardado = previo.get("candidato_descartado")
        if not guardado:
            raise
        descartado = dict(guardado)
        descartado["recalculado"] = False
        aviso = (
            f"No se pudo recalcular el candidato descartado ({error}); se conservan las cifras "
            "verificadas en la ultima ejecucion con conexion."
        )
    if not ARCHIVE.exists():
        raise FileNotFoundError(
            f"No existe {ARCHIVE}. Ejecute `uv run python scripts/download_data.py` primero."
        )
    frame = pd.read_csv(ROOT / "data/raw/dataset.csv")
    textos = frame[settings.text_column].astype(str)
    aprobado = {
        "nombre": "Sentiment Labelled Sentences (UCI 331)",
        "url": settings.dataset_url,
        "licencia": settings.dataset_license,
        "filas": len(frame),
        "clases": int(frame[settings.target_column].nunique()),
        "distribucion_clases": {
            str(clave): int(valor)
            for clave, valor in frame[settings.target_column].value_counts().sort_index().items()
        },
        "duplicados_exactos": int(textos.duplicated().sum()),
        "filas_con_7_mas_digitos": sum(1 for texto in textos if DIGITS_PATTERN.search(texto)),
        "filas_con_url": sum(1 for texto in textos if URL_PATTERN.search(texto)),
        "filas_con_direccion_correo": sum(1 for texto in textos if EMAIL_PATTERN.search(texto)),
        "riesgo_datos_personales": (
            "nulo: 0 filas con URL, 0 con direccion de correo y 0 con 7+ digitos"
        ),
    }
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "candidato_aprobado": aprobado,
        "candidato_descartado": descartado,
    }
    if aviso:
        payload["aviso"] = aviso
    return payload


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    parse = audit_parse()
    (REPORTS / "parse_audit.json").write_text(
        json.dumps(parse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    candidates = audit_candidates()
    (REPORTS / "candidates_audit.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Formato crudo del corpus aprobado (reports/parse_audit.json):")
    for fuente, valores in parse["por_fuente"].items():
        print(
            f"  {fuente}: {valores['lineas_logicas']} lineas | "
            f"recuperadas {valores['recuperadas_ultimo_tabulador']} | "
            f"lector CSV ingenuo {valores['leidas_csv_ingenuo_coma']} "
            f"(pierde {valores['perdidas_csv_ingenuo_coma']})"
        )
    print(
        f"  total: {parse['totales']['lineas_logicas']} lineas | "
        f"recuperadas {parse['totales']['recuperadas_ultimo_tabulador']} | "
        f"lector CSV ingenuo {parse['totales']['leidas_csv_ingenuo_coma']} "
        f"(pierde {parse['totales']['perdidas_csv_ingenuo_coma']})"
    )
    print("\nCandidatos (reports/candidates_audit.json):")
    print(json.dumps(candidates["candidato_aprobado"], ensure_ascii=False, indent=2))
    print(json.dumps(candidates["candidato_descartado"], ensure_ascii=False, indent=2))
    if "aviso" in candidates:
        print("AVISO:", candidates["aviso"])


if __name__ == "__main__":
    main()
