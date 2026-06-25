"""CDLI Translation Resolver — Dead Letter Fix 3 (#522).

7,658 CDLI translations landed in import_dead_letters with line_id=NULL
because the original import had no line-number field in the source JSON.

Fix: positional heuristic. CDLI translations are in document order; text_lines
are in (surface_rank, column, line_number) order. For any tablet where
trans_count <= line_count, we assign translation[i] → line[i] and patch
translations.line_id.

Coverage: 1,352 tablets, 7,218 translations (~94%). The remaining 440 rows
where the tablet has fewer lines than translations (data inconsistency) are
re-dead-lettered as 'positional_overflow' for manual triage.

This connector is idempotent: it re-skips rows whose line_id is already set.
"""

from __future__ import annotations

from typing import Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector
from ingestion.dead_letters import DeadLetterCategory

_SURFACE_RANK = {
    "obverse": 1, "reverse": 2, "left_edge": 3, "right_edge": 4,
    "top_edge": 5, "bottom_edge": 6, "seal": 7, "envelope": 8,
    "tablet": 9, "object": 10, "prism": 11, "cylinder": 12,
    "brick": 13, "cone": 14, "bulla": 15, "column": 16, "face": 17,
}


class CDLITranslationResolver(SourceConnector):
    id = "cdli-translation-resolver"
    display_name = "CDLI Translation Line Resolver (Fix 3)"
    description = (
        "Positional heuristic to assign line_id to CDLI translations that "
        "arrived with line_id=NULL. Patches translations.line_id in-place. "
        "Resolves Dead Letter Fix 3 (#522)."
    )
    kind = "derived"
    runs_after = ["translation-line-matcher", "atf-parser"]
    license = None

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield one record per p_number group of unresolved CDLI translations."""
        ctx.info("resolver.extract_start", action="extracting")
        with ctx.db.cursor() as cur:
            cur.execute(
                """
                SELECT t.p_number,
                       ARRAY_AGG(t.id ORDER BY t.id) AS translation_ids,
                       (
                           SELECT COUNT(*)
                           FROM text_lines tl2
                           WHERE tl2.p_number = t.p_number
                             AND tl2.is_ruling = 0
                             AND tl2.is_blank = 0
                       ) AS line_count
                FROM translations t
                WHERE t.line_id IS NULL
                  AND t.source = 'cdli'
                GROUP BY t.p_number
                """
            )
            for row in cur:
                if isinstance(row, dict):
                    yield row
                else:
                    yield dict(zip(["p_number", "translation_ids", "line_count"], row))

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        p_number = record["p_number"]
        translation_ids: list[int] = record["translation_ids"]
        line_count: int = record["line_count"] or 0
        trans_count = len(translation_ids)

        if line_count == 0:
            # No text_lines for this tablet — positional match impossible
            for tid in translation_ids:
                ctx.dead_letter(
                    category=DeadLetterCategory.NO_MATCH.value,
                    subcategory="no_text_lines",
                    source_key=f"{p_number}/{tid}",
                    payload={"translation_id": tid, "p_number": p_number},
                    reason=f"tablet {p_number} has no text_lines",
                )
            return

        if trans_count > line_count:
            # More translations than lines — can't assign safely
            for tid in translation_ids:
                ctx.dead_letter(
                    category=DeadLetterCategory.NO_MATCH.value,
                    subcategory="positional_overflow",
                    source_key=f"{p_number}/{tid}",
                    payload={"translation_id": tid, "p_number": p_number,
                             "trans_count": trans_count, "line_count": line_count},
                    reason=f"{p_number}: {trans_count} translations but only {line_count} lines",
                )
            return

        # Fetch text_lines in canonical order
        with ctx.db.cursor() as cur:
            cur.execute(
                """
                SELECT tl.id
                FROM text_lines tl
                LEFT JOIN surfaces s ON s.id = tl.surface_id
                WHERE tl.p_number = %s
                  AND tl.is_ruling = 0
                  AND tl.is_blank = 0
                ORDER BY
                    COALESCE((
                        SELECT rank FROM (
                            VALUES ('obverse',1),('reverse',2),('left_edge',3),
                                   ('right_edge',4),('top_edge',5),('bottom_edge',6),
                                   ('seal',7),('envelope',8),('tablet',9),('object',10),
                                   ('prism',11),('cylinder',12),('brick',13),('cone',14),
                                   ('bulla',15),('column',16),('face',17)
                        ) t(surface_type, rank)
                        WHERE t.surface_type = s.surface_type
                    ), 99),
                    tl.column_number,
                    CASE WHEN tl.line_number ~ '^[0-9]+$' THEN tl.line_number::int ELSE 9999 END,
                    tl.line_number
                """,
                (p_number,),
            )
            rows = cur.fetchall()
            line_ids = [r["id"] if isinstance(r, dict) else r[0] for r in rows]

        # Assign translation[i] → line[i]
        for tid, lid in zip(translation_ids, line_ids):
            yield {"translation_id": tid, "line_id": lid}

    def load(self, ctx: RunContext, records: Iterator[dict]) -> LoadStats:
        stats = LoadStats()
        with ctx.db.cursor() as cur:
            for rec in records:
                cur.execute(
                    "UPDATE translations SET line_id = %s WHERE id = %s AND line_id IS NULL",
                    (rec["line_id"], rec["translation_id"]),
                )
                if cur.rowcount:
                    stats.inserted += 1
                else:
                    stats.skipped += 1
        ctx.db.commit()
        # Mark corresponding dead letters resolved
        with ctx.db.cursor() as cur:
            cur.execute(
                """
                UPDATE import_dead_letters
                SET resolution_status='fixed',
                    resolved_by=%s,
                    resolved_at=NOW()
                WHERE connector_id='translation-line-matcher'
                  AND resolution_status='open'
                  AND (payload->>'line_id') IS NULL
                  AND payload->>'translation_id' IN (
                    SELECT id::text FROM translations WHERE line_id IS NOT NULL AND source='cdli'
                  )
                """,
                (f"cdli-translation-resolver/{ctx.run_id}",),
            )
            resolved = cur.rowcount
            ctx.db.commit()
        ctx.info("resolver.resolved_dead_letters", resolved=resolved)
        return stats
