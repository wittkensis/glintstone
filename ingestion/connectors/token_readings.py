"""Token readings importer (Phase A — minimal GDL format).

Reads the minimal {"frag": "word"} GDL stored in tokens.gdl_json and
extracts form, reading, sign_function, and damage markers.

Phase B will re-import from full ORACC CDL GDL arrays for higher precision.

Depends on: atf-parser (tokens table populated)
"""

from __future__ import annotations

import json
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

BATCH_SIZE = 10_000


def _parse_minimal_gdl(gdl_json_str: str) -> dict | None:
    try:
        data = json.loads(gdl_json_str)
        form = data.get("frag", "").strip()
        if not form:
            return None
        if form.isupper():
            sign_function = "logographic"
        elif any(c.isdigit() for c in form):
            sign_function = "numeric"
        else:
            sign_function = "syllabographic"
        if "#" in form:
            damage = "damaged"
        elif "[" in form or "]" in form:
            damage = "missing"
        elif "!" in form or "?" in form:
            damage = "illegible"
        else:
            damage = "intact"
        return {
            "form": form,
            "reading": form.upper(),
            "sign_function": sign_function,
            "damage": damage,
            "confidence": 0.7,
        }
    except (json.JSONDecodeError, AttributeError, KeyError):
        return None


class TokenReadingsConnector(SourceConnector):
    id = "token-readings"
    display_name = "Token Readings (Phase A)"
    description = "Extracts form/reading/damage from ATF-derived tokens.gdl_json (heuristic phase A)."
    kind = "annotation"
    runs_after = ["atf-parser", "annotation-runs"]

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Get or create annotation_run for this import
        run = ctx.db.execute(
            "SELECT id FROM annotation_runs WHERE source_name = 'cdli-atf-minimal' LIMIT 1"
        ).fetchone()
        if run:
            run_id = run["id"] if isinstance(run, dict) else run[0]
        else:
            row = ctx.db.execute(
                "INSERT INTO annotation_runs (source_name, source_type, method, notes, created_at) "
                "VALUES ('cdli-atf-minimal', 'import', 'import', "
                "'Phase A: Token readings from ATF fragments (heuristic parsing)', NOW()) RETURNING id"
            ).fetchone()
            ctx.db.commit()
            run_id = row["id"] if isinstance(row, dict) else row[0]

        total_row = ctx.db.execute(
            "SELECT COUNT(*) AS cnt FROM tokens WHERE gdl_json IS NOT NULL"
        ).fetchone()
        total = total_row["cnt"] if isinstance(total_row, dict) else total_row[0]
        ctx.info("token_readings.total_tokens", count=total)

        offset = 0
        while True:
            tokens = ctx.db.execute(
                "SELECT id, gdl_json FROM tokens WHERE gdl_json IS NOT NULL ORDER BY id LIMIT %s OFFSET %s",
                (BATCH_SIZE, offset),
            ).fetchall()
            if not tokens:
                break
            for token in tokens:
                tid = token["id"] if isinstance(token, dict) else token[0]
                gdl = token["gdl_json"] if isinstance(token, dict) else token[1]
                parsed = _parse_minimal_gdl(gdl)
                if parsed:
                    yield {
                        "token_id": tid,
                        "form": parsed["form"],
                        "reading": parsed["reading"],
                        "sign_function": parsed["sign_function"],
                        "damage": parsed["damage"],
                        "confidence": parsed["confidence"],
                        "annotation_run_id": run_id,
                        "is_consensus": 1,
                    }
            offset += BATCH_SIZE
            if offset % 100_000 == 0:
                ctx.info("token_readings.progress", offset=offset, total=total)

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="token_readings",
            rows=rows,
            unique_key=["token_id"],
            policy=ConflictPolicy.SKIP,
            batch_size=500,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM token_readings").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("token_readings.verify", count=n)
