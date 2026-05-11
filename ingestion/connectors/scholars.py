"""Scholar importer — collects author/ATF-source names from CDLI + ORACC.

Sources:
  - CDLI catalog CSV: atf_source and author fields
  - ORACC catalogue.json: author / atf_source per project

Names are normalized (unicode NFC, whitespace collapsed) and inserted once.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

DEFAULT_CSV = Path("source-data/sources/CDLI/metadata/cdli_cat.csv")
ORACC_BASE = Path("source-data/sources/ORACC")

ORACC_PROJECTS = [
    "dcclt",
    "epsd2",
    "rinap",
    "saao",
    "blms",
    "cams",
    "etcsri",
    "riao",
    "rimanum",
]


def _normalize_name(raw: str) -> str:
    name = raw.strip()
    name = re.sub(r"\s*(et al\.|& others|and others)\s*", "", name, flags=re.IGNORECASE)
    name = name.strip().strip(",").strip()
    if not name:
        return ""
    name = unicodedata.normalize("NFC", name)
    return re.sub(r"\s+", " ", name)


def _parse_name_list(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    parts = re.split(r"\s*[&;]\s*|\s+and\s+", raw)
    return [n for p in parts if len(n := _normalize_name(p)) > 2]


def _find_catalogue(project: str) -> Path | None:
    for candidate in [
        ORACC_BASE / project / "json" / project / "catalogue.json",
        ORACC_BASE / project / "json" / "catalogue.json",
    ]:
        if candidate.exists():
            return candidate
    return None


class ScholarsConnector(SourceConnector):
    id = "scholars"
    display_name = "Scholars (CDLI + ORACC)"
    description = (
        "Collects scholar names from CDLI catalog and ORACC project catalogues."
    )
    kind = "catalog"
    runs_after = ["annotation-runs"]
    upstream_url = "https://cdli.mpiwg-berlin.mpg.de/"
    license = "CC-BY-NC-3.0"

    def __init__(self, csv_path: Path | None = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        names: set[str] = set()

        if self.csv_path.exists():
            ctx.info("scholars.scan_cdli", path=str(self.csv_path))
            with open(self.csv_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    for field in ("atf_source", "author"):
                        for name in _parse_name_list(row.get(field, "")):
                            names.add(name)

        for proj in ORACC_PROJECTS:
            cat_path = _find_catalogue(proj)
            if not cat_path:
                continue
            try:
                with open(cat_path, encoding="utf-8") as f:
                    catalogue = json.load(f)
            except (json.JSONDecodeError, ValueError):
                continue
            for entry in catalogue.get("members", {}).values():
                for field in ("author", "atf_source"):
                    for name in _parse_name_list(entry.get(field, "")):
                        names.add(name)

        ctx.info("scholars.collected", count=len(names))
        for name in sorted(names):
            yield {"name": name}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="scholars",
            rows=rows,
            unique_key=["name"],
            policy=ConflictPolicy.SKIP,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM scholars").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        if n < 100:
            raise AssertionError(f"scholars has {n} rows; expected ≥ 100")
