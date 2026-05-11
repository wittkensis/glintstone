"""ORACC per-text credits importer.

Reads credits field from each ORACC catalogue.json and stores one row per
(p_number, oracc_project) in artifact_credits. Q-numbers are resolved to
P-numbers via the artifact_composites table.

Depends on: cdli-catalog (artifacts must be loaded)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

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
    "etcsl",
    "ribo",
    "rime",
    "amgg",
    "hbtin",
]


def _find_catalogue(project: str) -> Path | None:
    for candidate in [
        ORACC_BASE / project / "json" / project / "catalogue.json",
        ORACC_BASE / project / "json" / "catalogue.json",
    ]:
        if candidate.exists():
            return candidate
    return None


class OraccCreditsConnector(SourceConnector):
    id = "oracc-credits"
    display_name = "ORACC Per-Text Credits"
    description = (
        "Imports artifact_credits rows from ORACC catalogue.json credit fields."
    )
    kind = "catalog"
    runs_after = ["cdli-catalog"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Load Q→P and valid-P maps once
        q_to_p: dict[str, list[str]] = {}
        for row in ctx.db.execute(
            "SELECT q_number, p_number FROM artifact_composites"
        ).fetchall():
            q, p = (
                (row["q_number"], row["p_number"])
                if isinstance(row, dict)
                else (row[0], row[1])
            )
            q_to_p.setdefault(q, []).append(p)

        valid_p = {
            (row["p_number"] if isinstance(row, dict) else row[0])
            for row in ctx.db.execute("SELECT p_number FROM artifacts").fetchall()
        }
        ctx.info(
            "oracc_credits.loaded_maps", q_numbers=len(q_to_p), p_numbers=len(valid_p)
        )

        for project in ORACC_PROJECTS:
            cat_path = _find_catalogue(project)
            if not cat_path:
                continue
            try:
                with open(cat_path, encoding="utf-8") as f:
                    catalogue = json.load(f)
            except (json.JSONDecodeError, ValueError):
                ctx.warn("oracc_credits.bad_json", project=project)
                continue

            for text_id, entry in catalogue.get("members", {}).items():
                credits = entry.get("credits", "").strip()
                if not credits:
                    continue
                p_numbers: list[str] = []
                if text_id.startswith("P"):
                    p_numbers = [text_id]
                elif text_id.startswith("Q"):
                    p_numbers = q_to_p.get(text_id, [])
                for p_number in p_numbers:
                    if p_number not in valid_p:
                        continue
                    yield {
                        "p_number": p_number,
                        "oracc_project": project,
                        "credits_text": credits,
                    }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="artifact_credits",
            rows=rows,
            unique_key=["p_number", "oracc_project"],
            policy=ConflictPolicy.SKIP,
            batch_size=500,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM artifact_credits").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_credits.verify", count=n)
