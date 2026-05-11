"""Translation line matcher — the connector that retires
`_progress/19_unmatched_translations.json` into `import_dead_letters`.

The v1 script (`source-data/import-tools/19_match_translation_lines.py`)
attempted to match each translation to a specific `text_line` by line number.
~45,000 rows couldn't match — they were dumped to a JSON file that lived on
one developer's disk.

The v2 connector does the same matching but writes every unmatchable record
to `import_dead_letters` with `category='no_match'` plus a subcategory
("broken", "fragmentary", "missing_artifact", "missing_line"). Triage moves
from "open the JSON file and squint" to:

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
        "Matches translation rows to specific text_lines by (p_number, line_no). "
        "Replaces v1's disk JSON of unmatched rows with import_dead_letters."
    )
    kind = "derived"
    runs_after = ["cdli-catalog", "atf-parser", "translation-import"]
    license = None  # derived data; inherits license of inputs

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield every translation row that hasn't been matched yet."""
        ctx.info("matcher.extract_start")
        with ctx.db.cursor() as cur:
            cur.execute(
                """
                SELECT t.id AS translation_id, t.p_number, t.line_no, t.text,
                       t.is_broken, t.is_fragmentary
                FROM translations t
                LEFT JOIN text_lines tl
                  ON tl.p_number = t.p_number AND tl.line_no = t.line_no
                WHERE tl.id IS NULL
                """
            )
            for row in cur:
                yield dict(row) if not isinstance(row, dict) else row

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        # Classify the unmatchable reason and route to dead-letters
        if record.get("is_broken"):
            subcategory = "broken"
        elif record.get("is_fragmentary"):
            subcategory = "fragmentary"
        elif _has_no_artifact(ctx, record["p_number"]):
            subcategory = "missing_artifact"
        else:
            subcategory = "missing_line"

        ctx.dead_letter(
            category=DeadLetterCategory.NO_MATCH.value,
            subcategory=subcategory,
            source_key=f"{record['p_number']}/{record['translation_id']}",
            payload={
                "translation_id": record["translation_id"],
                "p_number": record["p_number"],
                "line_no": record.get("line_no"),
                "text": record.get("text"),
            },
            reason=_reason_for(subcategory),
        )
        # No row yielded — dead-letters only

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
        "broken": "translation marked broken — no specific line to attach to",
        "fragmentary": "fragmentary translation spanning unclear lines",
        "missing_artifact": "p_number not in artifacts table",
        "missing_line": "line_no not present in text_lines for this artifact",
    }.get(subcategory, "unknown matching failure")
