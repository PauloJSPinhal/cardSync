"""Nomenclatura de pastas e sanitização (secção 2)."""

import re
import unicodedata
from datetime import date, datetime


def sanitize(text: str) -> str:
    """Sanitiza texto para uso em nomes de pasta: espaços -> '-', remove especiais."""
    if text is None:
        return ""
    text = str(text).strip()
    # normaliza acentos? Mantemos acentos? Spec diz remove caracteres especiais.
    # Vamos manter letras/números/hífen/underscore, converter espaços em '-'.
    # Remover caracteres não alfanuméricos (exceto hífen/underscore/espaço).
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-_")
    return text


def format_date_yyyymmdd(d) -> str:
    if isinstance(d, str):
        # tenta parse
        for fmt in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                d = datetime.strptime(d, fmt).date()
                break
            except ValueError:
                continue
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return d.strftime("%Y%m%d")
    raise ValueError(f"Data inválida: {d!r}")


def folder_name(date_value, event: str, location: str) -> str:
    """yyyymmdd_evento_local"""
    d = format_date_yyyymmdd(date_value)
    ev = sanitize(event)
    loc = sanitize(location)
    return f"{d}_{ev}_{loc}"


def display_title(date_value, event: str, location: str) -> str:
    """DD/MM/AAAA — Evento, Local"""
    d = format_date_yyyymmdd(date_value)
    dt = datetime.strptime(d, "%Y%m%d").date()
    ev = sanitize(event).replace("-", " ") if False else event.strip()
    loc = location.strip()
    return f"{dt.strftime('%d/%m/%Y')} — {ev}, {loc}"


def project_id(date_value, event: str) -> str:
    d = format_date_yyyymmdd(date_value)
    ev = sanitize(event).lower().replace("-", "_")
    return f"proj_{d}_{ev}"