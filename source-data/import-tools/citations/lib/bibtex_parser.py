#!/usr/bin/env python3
"""
BibTeX parsing utilities for Assyriology citation import.

Maps BibTeX entry types to v2 schema publication_type values
and extracts structured author lists.
"""

import re
from pathlib import Path
from typing import Optional

from .name_normalizer import parse_author_string

# BibTeX entry type -> v2 publication_type mapping
ENTRY_TYPE_MAP = {
    "article": "journal_article",
    "book": "monograph",
    "inbook": "chapter",
    "incollection": "chapter",
    "inproceedings": "conference_paper",
    "proceedings": "proceedings",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
    "techreport": "report",
    "misc": "other",
    "unpublished": "unpublished",
    "online": "digital_edition",
}

# CDLI entry_type_id -> v2 publication_type mapping
CDLI_ENTRY_TYPE_MAP = {
    1: "journal_article",
    2: "monograph",
    3: "chapter",
    4: "proceedings",
    5: "thesis",
    6: "report",
    7: "chapter",  # incollection
    8: "other",
}

# Known Assyriology series abbreviations -> full series keys
SERIES_ABBREVIATIONS = {
    "RIME": "Royal Inscriptions of Mesopotamia, Early Periods",
    "SAA": "State Archives of Assyria",
    "RINAP": "Royal Inscriptions of the Neo-Assyrian Period",
    "VAB": "Vorderasiatische Bibliothek",
    "ABL": "Assyrian and Babylonian Letters",
    "CT": "Cuneiform Texts from Babylonian Tablets",
    "ATU": "Archaische Texte aus Uruk",
    "UET": "Ur Excavation Texts",
    "PBS": "Publications of the Babylonian Section",
    "BE": "Babylonian Expedition",
    "OIP": "Oriental Institute Publications",
    "OECT": "Oxford Editions of Cuneiform Texts",
    "MSL": "Materialien zum sumerischen Lexikon",
    "ETCSL": "Electronic Text Corpus of Sumerian Literature",
}


def parse_bibtex_file(path: Path) -> list[dict]:
    """
    Parse a BibTeX file into a list of entry dicts.

    Each entry dict has keys: entry_type, bibtex_key, and all BibTeX fields.
    Uses a simple regex parser (no external dependency).
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    entries = []

    # Match @type{key, ... }
    pattern = re.compile(
        r"@(\w+)\s*\{\s*([^,]+)\s*,\s*(.*?)\n\s*\}",
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        entry_type = match.group(1).lower()
        bibtex_key = match.group(2).strip()
        fields_str = match.group(3)

        entry = {
            "entry_type": entry_type,
            "bibtex_key": bibtex_key,
        }

        # Parse fields: key = {value} or key = "value" or key = number
        field_pattern = re.compile(
            r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\"|(\d+))",
        )
        for fm in field_pattern.finditer(fields_str):
            key = fm.group(1).lower()
            value = fm.group(2) or fm.group(3) or fm.group(4)
            if value is not None:
                entry[key] = value.strip()

        entries.append(entry)

    return entries


def bibtex_to_publication(entry: dict, source_prefix: str = "") -> dict:
    """
    Convert a parsed BibTeX entry to a v2 publications table record.

    Args:
        entry: Parsed BibTeX entry dict
        source_prefix: Prefix for bibtex_key to avoid collisions (e.g., "keibi:")

    Returns:
        Dict matching publications table columns
    """
    bk = entry.get("bibtex_key", "")
    if source_prefix and not bk.startswith(source_prefix):
        bk = f"{source_prefix}{bk}"

    pub_type = ENTRY_TYPE_MAP.get(entry.get("entry_type", ""), "other")

    # Extract series info from designation/series field
    series_key = None
    volume_in_series = None
    designation = entry.get("designation", "") or entry.get("series", "")
    if designation:
        series_key, volume_in_series = parse_series_designation(designation)

    return {
        "bibtex_key": bk,
        "title": entry.get("title"),
        "short_title": entry.get("designation") or entry.get("shorttitle"),
        "publication_type": pub_type,
        "year": entry.get("year"),
        "publisher": entry.get("publisher"),
        "doi": entry.get("doi"),
        "url": entry.get("url"),
        "series_key": series_key,
        "volume_in_series": volume_in_series,
        "authors_raw": entry.get("author", ""),
        "editors_raw": entry.get("editor", ""),
    }


def parse_series_designation(designation: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract series key and volume from a designation string.

    "ATU 3" -> ("ATU", "3")
    "RIME 4" -> ("RIME", "4")
    "SAA 01" -> ("SAA", "01")
    """
    if not designation:
        return None, None

    # Try known abbreviation + volume pattern
    match = re.match(r"^([A-Z]{2,6})\s+(\d+\S*)", designation)
    if match:
        abbrev = match.group(1)
        vol = match.group(2)
        if abbrev in SERIES_ABBREVIATIONS:
            return abbrev, vol

    return None, None


def parse_authors_to_records(
    authors_raw: str,
    publication_id: int,
    role: str = "author",
) -> list[dict]:
    """
    Parse raw author string into publication_authors table records.

    Returns list of dicts with: publication_id, scholar_name, role, position
    """
    names = parse_author_string(authors_raw)
    records = []
    for i, name in enumerate(names):
        records.append(
            {
                "publication_id": publication_id,
                "scholar_name_raw": name.raw,
                "scholar_name_normalized": name.normalized_key,
                "role": role,
                "position": i + 1,
            }
        )
    return records


def cdli_entry_type_to_publication_type(entry_type_id: int) -> str:
    """Map CDLI's numeric entry_type_id to v2 publication_type."""
    return CDLI_ENTRY_TYPE_MAP.get(entry_type_id, "other")
