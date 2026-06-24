"""Pipeline-status recalc connector (#260).

Recomputes the five per-artifact completeness scores in ``pipeline_status`` from
the live data, so the composites coverage badges (#158) and the agent eval
(``core/agent/eval.py``) — both of which read this table — never quietly show
stale numbers after an ingest.

Why a connector, not the SQL script
-----------------------------------
``data-model/scripts/recalc_pipeline_status.sql`` was MANUAL: it had to be run by
hand with ``psql`` after every ingest, it only set 4 of the 5 stage columns
(``graphemic_complete`` was never populated), and nothing scheduled it. By making
this a derived connector it becomes first-class in the framework:
- it runs in ``ingestion.cli run-all`` after the data connectors (``runs_after``),
- it can be scheduled from ``cron-ingest.yml`` like any other connector,
- every run is recorded in ``import_runs`` with row counts, and
- it now sets all five stages, including the previously-missing graphemic one.

The five stages
---------------
A stage score is 1.0 when the artifact has the corresponding data and 0.0 when it
does not (binary today; the column is ``real`` so a future partial score fits):

1. physical    — has at least one row in ``artifact_images``
2. graphemic   — has at least one ``sign_annotations`` row, reached via
                 ``surface_images`` -> ``surfaces`` -> ``p_number`` (#260: this
                 stage was never populated before)
3. reading     — has at least one ATF ``text_lines`` row
4. linguistic  — has at least one ``lemmatizations`` row with a citation_form
                 (the column the 2026 Fix A/C backfill actually populated)
5. semantic    — has at least one non-empty ``translations`` row

Idempotency
-----------
Each stage is a pair of UPDATEs (set 1.0 where the evidence EXISTS, 0.0 where it
does not) over the whole ``pipeline_status`` table. Re-running produces the same
values, so the connector is safe to run as often as the ingest does. It writes
``last_updated = NOW()`` at the end so freshness is observable.

Runs after the connectors that produce the evidence so the recompute always sees
the latest ingested data.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

# Each entry: (column, EXISTS-predicate that means "this stage is complete").
# The predicate is correlated to pipeline_status ps via ps.p_number.
_STAGES: list[tuple[str, str]] = [
    (
        "physical_complete",
        "SELECT 1 FROM artifact_images ai WHERE ai.p_number = ps.p_number",
    ),
    # #260: graphemic was the missing 5th column. Sign annotations attach to a
    # surface image, so we walk sign_annotations -> surface_images -> surfaces to
    # reach the artifact's p_number.
    (
        "graphemic_complete",
        """
        SELECT 1
        FROM sign_annotations sa
        JOIN surface_images si ON si.id = sa.surface_image_id
        JOIN surfaces s        ON s.id = si.surface_id
        WHERE s.p_number = ps.p_number
        """,
    ),
    (
        "reading_complete",
        "SELECT 1 FROM text_lines tl WHERE tl.p_number = ps.p_number",
    ),
    (
        "linguistic_complete",
        """
        SELECT 1
        FROM text_lines tl
        JOIN tokens t        ON t.line_id = tl.id
        JOIN lemmatizations lz ON lz.token_id = t.id
        WHERE tl.p_number = ps.p_number
          AND lz.citation_form IS NOT NULL
        """,
    ),
    (
        "semantic_complete",
        """
        SELECT 1
        FROM translations tr
        WHERE tr.p_number = ps.p_number
          AND tr.translation IS NOT NULL
          AND tr.translation != ''
        """,
    ),
]


class PipelineStatusRecalcConnector(SourceConnector):
    id = "pipeline-status-recalc"
    display_name = "Pipeline Status Recalc"
    description = (
        "Recomputes the five per-artifact completeness scores in pipeline_status "
        "(physical/graphemic/reading/linguistic/semantic) from live data so the "
        "composites coverage badges and agent eval never read stale rows (#260)."
    )
    kind = "derived"
    # Run after the connectors that produce each stage's evidence so the recompute
    # reflects the freshest ingested data.
    runs_after = [
        "cdli-catalog",
        "atf-parser",
        "oracc-lemmatizations",
        "oracc-norms",
    ]
    upstream_url = None
    license = None
    license_url = None
    citation = "Derived from Glintstone's own ingested data; no external source."

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Nothing to extract — all work is set-based SQL in load(). Yield a single
        # sentinel so the runner calls load() once.
        yield {"recalc": True}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # Drain the sentinel.
        list(rows)

        stats = LoadStats()
        updated = 0
        with ctx.db.cursor() as cur:
            for column, predicate in _STAGES:
                cur.execute(
                    f"""
                    UPDATE pipeline_status ps
                    SET {column} = 1.0
                    WHERE EXISTS ({predicate})
                      AND ({column} IS DISTINCT FROM 1.0)
                    """
                )
                updated += cur.rowcount or 0
                cur.execute(
                    f"""
                    UPDATE pipeline_status ps
                    SET {column} = 0.0
                    WHERE NOT EXISTS ({predicate})
                      AND ({column} IS DISTINCT FROM 0.0)
                    """
                )
                updated += cur.rowcount or 0
                ctx.info("pipeline_status_recalc.stage", stage=column)
                ctx.db.commit()

            cur.execute("UPDATE pipeline_status SET last_updated = NOW()")
            ctx.db.commit()

        # These are UPDATEs to an existing table, not inserts — report them as
        # updated so the run summary is honest.
        stats.updated = updated
        ctx.info("pipeline_status_recalc.done", rows_touched=updated)
        return stats

    def verify(self, ctx: RunContext) -> None:
        # Sanity floor: every artifact should have a pipeline_status row and none
        # of the five stages should be NULL after a recompute.
        row = ctx.db.execute(
            """
            SELECT COUNT(*) AS null_stages
            FROM pipeline_status
            WHERE physical_complete   IS NULL
               OR graphemic_complete  IS NULL
               OR reading_complete    IS NULL
               OR linguistic_complete IS NULL
               OR semantic_complete   IS NULL
            """
        ).fetchone()
        null_stages = row[0] if isinstance(row, tuple) else row["null_stages"]
        ctx.info("pipeline_status_recalc.verify", rows_with_null_stage=null_stages)
        if null_stages:
            raise AssertionError(
                f"{null_stages} pipeline_status rows still have a NULL stage score "
                "after recompute — a stage UPDATE did not cover them"
            )
