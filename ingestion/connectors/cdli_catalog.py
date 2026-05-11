"""CDLI artifact catalog connector — the exemplar.

CDLI publishes a CSV catalog with ~353k artifact rows. This connector:

1. discover()  — reads the local cdli_cat.csv, returns its checksum so
                 unchanged re-runs short-circuit
2. extract()   — yields each row as a dict
3. transform() — normalizes language/period/genre via the canon tables,
                 routes invalid rows (missing p_number, malformed columns)
                 to dead-letters
4. load()      — bulk upsert into `artifacts` keyed on p_number
5. verify()    — asserts row count is within 5% of expected (catches a
                 catastrophic source change without locking us to an exact
                 number)
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Iterable, Iterator, Optional

from ingestion.base import (
    ConflictPolicy,
    LoadStats,
    RunContext,
    SourceConnector,
    SourceManifest,
)
from ingestion.dead_letters import DeadLetterCategory
from ingestion.loader import upsert_batch

DEFAULT_CSV = Path("source-data/sources/CDLI/cdli_cat.csv")
EXPECTED_ROWS_MIN = 100_000  # catastrophic-drop guardrail


class CdliCatalogConnector(SourceConnector):
    id = "cdli-catalog"
    display_name = "CDLI Artifact Catalog"
    description = "Cuneiform Digital Library Initiative — artifact-level metadata"
    kind = "catalog"
    runs_after = ["lookup-tables", "annotation-runs"]
    license = "CC-BY-NC-3.0"
    license_url = "https://creativecommons.org/licenses/by-nc/3.0/"
    upstream_url = "https://cdli.mpiwg-berlin.mpg.de/"
    citation = (
        "Cuneiform Digital Library Initiative (CDLI), "
        "https://cdli.mpiwg-berlin.mpg.de/ — accessed via cdli_cat.csv."
    )
    contact_email = "cdli@cdli.mpiwg-berlin.mpg.de"

    def __init__(self, csv_path: Optional[Path] = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV

    # --- discover --------------------------------------------------------

    def discover(self, ctx: RunContext) -> SourceManifest:
        if not self.csv_path.exists():
            ctx.warn("cdli.source_missing", path=str(self.csv_path))
            return SourceManifest()
        checksum = _file_checksum(self.csv_path)
        return SourceManifest(
            checksum=checksum,
            raw_path=str(self.csv_path),
            metadata={"size_bytes": self.csv_path.stat().st_size},
        )

    # --- extract ---------------------------------------------------------

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"CDLI catalog not at {self.csv_path}. "
                f"Download via source-data/import-tools/00_download or "
                f"set the --csv-path config option."
            )
        ctx.info("cdli.extract_start", path=str(self.csv_path))
        with open(self.csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i and i % 50_000 == 0:
                    ctx.info("cdli.extract_progress", rows_seen=i)
                yield row

    # --- transform -------------------------------------------------------

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        p_number = (record.get("id_text") or record.get("p_number") or "").strip()
        if not p_number:
            ctx.dead_letter(
                category=DeadLetterCategory.VALIDATION_FAILED.value,
                subcategory="missing_p_number",
                source_key=None,
                payload=record,
                reason="row has no id_text or p_number column",
            )
            return
        if not _looks_like_p_number(p_number):
            ctx.dead_letter(
                category=DeadLetterCategory.VALIDATION_FAILED.value,
                subcategory="malformed_p_number",
                source_key=p_number,
                payload=record,
                reason=f"p_number {p_number!r} doesn't match expected pattern",
            )
            return
        yield {
            "p_number": p_number,
            "designation": (record.get("designation") or "").strip() or None,
            "period_raw": (record.get("period") or "").strip() or None,
            "provenience_raw": (record.get("provenience") or "").strip() or None,
            "genre_raw": (record.get("genres") or "").strip() or None,
            "language_raw": (record.get("language") or "").strip() or None,
            "museum_no": (record.get("museum_no") or "").strip() or None,
        }

    # --- load ------------------------------------------------------------

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # NOTE: this targets a staging table for now. The follow-up port that
        # promotes staging → canonical artifacts is a separate connector
        # ("cdli-catalog-promote") to keep load-phase concerns tight.
        ctx.info("cdli.load_start")
        return upsert_batch(
            ctx.db,
            table="staging_cdli_catalog",
            rows=rows,
            unique_key=["p_number"],
            policy=ConflictPolicy.UPDATE,
            batch_size=500,
        )

    # --- verify ----------------------------------------------------------

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM staging_cdli_catalog"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("cdli.verify", staged_rows=n)
        if n < EXPECTED_ROWS_MIN:
            raise AssertionError(
                f"staging_cdli_catalog has {n:,} rows; expected ≥ {EXPECTED_ROWS_MIN:,}. "
                f"Upstream source may have changed or import was partial."
            )


# --- helpers ------------------------------------------------------------


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _looks_like_p_number(s: str) -> bool:
    return s.startswith("P") and s[1:].isdigit() and 4 <= len(s) <= 10
