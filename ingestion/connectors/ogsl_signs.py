"""OGSL sign list importer — signs and phonetic readings.

Source: source-data/sources/ORACC/ogsl/json/ogsl/ogsl-sl.json

Populates:
  signs      — one row per sign (sign_id = OGSL name, e.g. "A", "KA", "|A.B|")
  sign_values — one row per phonetic reading per sign
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import (
    ConflictPolicy,
    LoadStats,
    RunContext,
    SourceConnector,
    SourceManifest,
)
from ingestion.loader import upsert_batch

DEFAULT_OGSL = Path("source-data/sources/ORACC/ogsl/json/ogsl/ogsl-sl.json")

_TABLE_KEYS = {
    "signs": ["sign_id"],
    "sign_values": ["sign_id", "value"],
}


def _classify_sign(sign_id: str) -> str:
    if sign_id.startswith("|") and sign_id.endswith("|"):
        return "compound"
    if "@" in sign_id:
        return "modified"
    return "simple"


def _parse_unicode_decimal(hex_str: str) -> int | None:
    if not hex_str:
        return None
    first = hex_str.split(".")[0]
    try:
        return int(first.lstrip("x"), 16)
    except ValueError:
        return None


def _extract_sub_index(v: str) -> int | None:
    m = re.search(r"[₀₁₂₃₄₅₆₇₈₉]+$", v)
    if m:
        subs = "₀₁₂₃₄₅₆₇₈₉"
        result = "".join(str(subs.find(c)) for c in m.group(0) if subs.find(c) >= 0)
        return int(result) if result else None
    m = re.search(r"(\d+)$", v)
    return int(m.group(1)) if m else None


def _infer_value_type(v: str) -> str:
    clean = re.sub(r"[₀-₉\d]", "", v).strip()
    if re.match(r"^[0-9()]+$", v):
        return "numeric"
    if len(clean) <= 4 and clean.islower():
        return "syllabic"
    if clean.isupper() and clean:
        return "logographic"
    return "syllabic"


class OgslSignsConnector(SourceConnector):
    id = "ogsl-signs"
    display_name = "OGSL Sign List"
    description = "Imports ORACC Global Sign List into signs and sign_values tables."
    kind = "lexicon"
    runs_after = ["annotation-runs"]
    upstream_url = "https://oracc.museum.upenn.edu/ogsl/"
    license = "CC-BY-SA-3.0"
    citation = "ORACC Global Sign List (OGSL), https://oracc.museum.upenn.edu/ogsl/"

    def __init__(self, ogsl_path: Path | None = None) -> None:
        self.ogsl_path = Path(ogsl_path) if ogsl_path else DEFAULT_OGSL

    def discover(self, ctx: RunContext) -> SourceManifest:
        if not self.ogsl_path.exists():
            return SourceManifest()
        import hashlib

        h = hashlib.sha256()
        with open(self.ogsl_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return SourceManifest(checksum=h.hexdigest()[:32], raw_path=str(self.ogsl_path))

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        if not self.ogsl_path.exists():
            ctx.warn("ogsl.source_missing", path=str(self.ogsl_path))
            return
        with open(self.ogsl_path, encoding="utf-8") as f:
            data = json.load(f)
        signs_data = data.get("signs", {})
        ctx.info("ogsl.extract_start", sign_count=len(signs_data))

        for sign_id, sign_data in signs_data.items():
            hex_str = sign_data.get("hex", "") or ""
            values_list = sign_data.get("values", [])
            gdl = sign_data.get("gdl")

            yield {
                "_target": "signs",
                "sign_id": sign_id,
                "utf8": sign_data.get("utf8"),
                "unicode_hex": hex_str or None,
                "unicode_decimal": _parse_unicode_decimal(hex_str),
                "uname": sign_data.get("uname"),
                "uphase": sign_data.get("uphase"),
                "sign_type": _classify_sign(sign_id),
                "gdl_definition": json.dumps(gdl) if gdl else None,
                "most_common_value": values_list[0] if values_list else None,
            }

            for v in values_list:
                value = v.strip()
                if not value:
                    continue
                yield {
                    "_target": "sign_values",
                    "sign_id": sign_id,
                    "value": value,
                    "sub_index": _extract_sub_index(value),
                    "value_type": _infer_value_type(value),
                }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        by_target: dict[str, list[dict]] = {}
        for row in rows:
            target = row.pop("_target")
            by_target.setdefault(target, []).append(row)

        # signs must be inserted before sign_values (FK)
        total = LoadStats()
        for table in ("signs", "sign_values"):
            batch = by_target.get(table, [])
            if not batch:
                continue
            stats = upsert_batch(
                ctx.db,
                table=table,
                rows=batch,
                unique_key=_TABLE_KEYS[table],
                policy=ConflictPolicy.SKIP,
            )
            ctx.info(f"ogsl.loaded.{table}", inserted=stats.inserted)
            total = total.merge(stats)
        return total

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM signs").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        if n < 1000:
            raise AssertionError(f"signs has {n} rows; expected ≥ 1000")
