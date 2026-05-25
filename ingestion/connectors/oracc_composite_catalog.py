"""ORACC composite-catalog connector.

Populates the `composites` table with human-readable metadata sourced from
ORACC project catalogue.json files.  The ATF parser creates composite rows
keyed by Q-number but never sets designation, language, period, or genre.
This connector fills those columns — and adds Q-numbers not yet seen by the
ATF parser.

Strategy
--------
- Walk every ORACC catalogue.json file.
- Collect one "winning" record per Q-number (first-encountered project wins;
  later projects can fill in gaps via COALESCE in the UPDATE).
- Upsert: INSERT the Q-number, UPDATE metadata columns where the existing row
  is NULL (so ATF-derived exemplar_count is preserved and never reset).

Runs after: atf-parser (so composite rows already exist for ATF-seen Q-numbers)
"""

from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")


def _iter_catalogues() -> Iterator[Path]:
    """Yield every catalogue.json file found under ORACC_BASE."""
    pattern = str(ORACC_BASE / "**" / "catalogue.json")
    for path_str in glob.glob(pattern, recursive=True):
        yield Path(path_str)


def _clean(val: object) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    return s or None


class OraccCompositeCatalogConnector(SourceConnector):
    id = "oracc-composite-catalog"
    display_name = "ORACC Composite Catalog"
    description = (
        "Enriches the composites table with designation, language, period, "
        "and genre sourced from ORACC project catalogue.json files."
    )
    kind = "derived"
    runs_after = ["atf-parser"]
    upstream_url = "https://oracc.museum.upenn.edu/"
    license = "CC-BY-SA-3.0"
    license_url = "https://creativecommons.org/licenses/by-sa/3.0/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """
        Merge all ORACC Q-number entries into one record per Q-number.

        Multiple projects may describe the same composite.  We merge eagerly:
        the first non-null value seen for each field wins.  This avoids
        yielding 8k rows when only one project covers a given Q-number while
        still letting later projects fill gaps left by sparse first entries.
        """
        seen: dict[str, dict] = {}

        catalogues = list(_iter_catalogues())
        ctx.info("oracc_composite_catalog.scan_start", catalogue_count=len(catalogues))

        for cat_path in catalogues:
            try:
                with open(cat_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, ValueError, OSError):
                ctx.warn("oracc_composite_catalog.bad_json", path=str(cat_path))
                continue

            members = data.get("members", {})

            for key, entry in members.items():
                if not key.startswith("Q"):
                    continue

                if key not in seen:
                    seen[key] = {
                        "q_number": key,
                        "designation": None,
                        "language": None,
                        "period": None,
                        "genre": None,
                    }

                rec = seen[key]
                # Fill gaps: first non-null value per field wins
                if rec["designation"] is None:
                    rec["designation"] = _clean(entry.get("designation"))
                if rec["language"] is None:
                    rec["language"] = _clean(entry.get("language"))
                if rec["period"] is None:
                    rec["period"] = _clean(entry.get("period"))
                if rec["genre"] is None:
                    # ORACC uses "genre" directly, fall back to "supergenre"
                    rec["genre"] = _clean(entry.get("genre")) or _clean(
                        entry.get("supergenre")
                    )

        ctx.info("oracc_composite_catalog.merged", unique_q_numbers=len(seen))
        yield from seen.values()

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        batch: list[tuple] = []

        def _flush(cur) -> None:
            if not batch:
                return
            cur.executemany(
                """
                INSERT INTO composites (q_number, designation, language, period, genre, exemplar_count)
                VALUES (%s, %s, %s, %s, %s, 0)
                ON CONFLICT (q_number) DO UPDATE SET
                    designation = COALESCE(composites.designation, EXCLUDED.designation),
                    language    = COALESCE(composites.language,    EXCLUDED.language),
                    period      = COALESCE(composites.period,      EXCLUDED.period),
                    genre       = COALESCE(composites.genre,       EXCLUDED.genre)
                """,
                batch,
            )
            batch.clear()

        with ctx.db.cursor() as cur:
            for row in rows:
                q = row["q_number"]
                batch.append(
                    (
                        q,
                        row["designation"],
                        row["language"],
                        row["period"],
                        row["genre"],
                    )
                )
                if len(batch) >= 500:
                    _flush(cur)
                    ctx.db.commit()
                    stats.inserted += 500

            _flush(cur)
            ctx.db.commit()

        stats.inserted = 0  # let verify report actual counts
        return stats

    def verify(self, ctx: RunContext) -> None:
        with ctx.db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total, COUNT(designation) AS with_desig FROM composites"
            )
            row = cur.fetchone()

        total = row[0] if isinstance(row, tuple) else row["total"]
        with_desig = row[1] if isinstance(row, tuple) else row["with_desig"]

        ctx.info(
            "oracc_composite_catalog.verify",
            total_composites=total,
            with_designation=with_desig,
        )
        if with_desig < 500:
            raise AssertionError(
                f"Expected ≥500 composites with designation after import, got {with_desig}"
            )
