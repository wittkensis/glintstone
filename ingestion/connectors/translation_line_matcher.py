"""Translation line matcher — the connector that retires
`_progress/19_unmatched_translations.json` into `import_dead_letters`.

The v1 script (`source-data/import-tools/19_match_translation_lines.py`)
attempted to match each translation to a specific `text_line` by line number.
~45,000 rows couldn't match — they were dumped to a JSON file that lived on
one developer's disk.

The connector audits translations whose `line_id` FK doesn't resolve to a
text_line and writes every unmatchable record to `import_dead_letters` with
`category='no_match'` plus a subcategory ("no_line_ref", "missing_artifact",
"stale_line_ref"). Triage moves from "open the JSON file and squint" to:

    SELECT subcategory, COUNT(*) FROM import_dead_letters
    WHERE connector_id='translation-line-matcher' AND resolution_status='open'
    GROUP BY subcategory;

Rows can be marked 'fixed' once the upstream is corrected, 'wontfix' if the
break is permanent, or 'investigating' while a scholar reviews.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ingestion.base import (
    LoadStats,
    RunContext,
    SourceConnector,
)
from ingestion.dead_letters import DeadLetterCategory


class TranslationLineMatcher(SourceConnector):
    id = "translation-line-matcher"
    display_name = "Translation → Text Line Matcher"
    description = (
        "Routes translations whose line_id FK doesn't resolve to a text_line "
        "into import_dead_letters. Replaces v1's disk JSON of unmatched rows."
    )
    kind = "derived"
    runs_after = ["cdli-catalog", "atf-parser", "translation-import"]
    license = None  # derived data; inherits license of inputs

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield every translation row whose line_id doesn't resolve."""
        ctx.info("matcher.extract_start")
        with ctx.db.cursor() as cur:
            cur.execute(
                """
                SELECT t.id AS translation_id, t.p_number, t.line_id,
                       t.translation, t.language, t.source
                FROM translations t
                LEFT JOIN text_lines tl ON tl.id = t.line_id
                WHERE tl.id IS NULL
                """
            )
            for row in cur:
                yield dict(row) if not isinstance(row, dict) else row

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        # Classify the unmatchable reason and route to dead-letters
        if record.get("line_id") is None:
            subcategory = "no_line_ref"
        elif _has_no_artifact(ctx, record["p_number"]):
            subcategory = "missing_artifact"
        else:
            subcategory = "stale_line_ref"

        ctx.dead_letter(
            category=DeadLetterCategory.NO_MATCH.value,
            subcategory=subcategory,
            source_key=f"{record['p_number']}/{record['translation_id']}",
            payload={
                "translation_id": record["translation_id"],
                "p_number": record["p_number"],
                "line_id": record.get("line_id"),
                "translation": record.get("translation"),
                "language": record.get("language"),
                "source": record.get("source"),
            },
            reason=_reason_for(subcategory),
        )
        return  # dead-letters only; yield from [] would also work but this is clearer
        yield  # makes this a generator function so runner's `yield from` works

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # All work happened in transform via dead_letter(); no rows to load.
        # Consume the generator so transform() runs for every record.
        for _ in rows:
            pass
        return LoadStats()

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            """
            SELECT COUNT(*) AS n, COUNT(DISTINCT subcategory) AS variants
            FROM import_dead_letters
            WHERE connector_id = %s AND run_id = %s
            """,
            (self.id, ctx.run_id),
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("matcher.dead_letters_written", count=n)


def _has_no_artifact(ctx: RunContext, p_number: str) -> bool:
    row = ctx.db.execute(
        "SELECT 1 FROM artifacts WHERE p_number = %s LIMIT 1",
        (p_number,),
    ).fetchone()
    return row is None


def _reason_for(subcategory: str) -> str:
    return {
        "no_line_ref": "translation.line_id is NULL — never attached to a specific text_line",
        "missing_artifact": "p_number not in artifacts table",
        "stale_line_ref": "translation.line_id points to a non-existent text_line",
    }.get(subcategory, "unknown matching failure")
