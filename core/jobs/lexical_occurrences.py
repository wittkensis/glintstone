"""Lexical tablet occurrences — background job.

Counts distinct tablets (p_numbers) containing each lemma and upserts rows
into ``lexical_tablet_occurrences`` (one row per lemma + p_number pair).

The table already exists (migration 000_baseline_v1). Because there is no
unique constraint on (lemma_id, p_number) we DELETE existing lemma rows then
INSERT fresh ones in a single transaction — this is safe because the job is
the only writer to this table and the PRD explicitly requires idempotency.

Join path for lemma resolution:
    lemmatizations.token_id  → tokens.id
    tokens.line_id           → text_lines.id  (text_lines carries p_number)
    lemmatizations.norm_id   → lexical_norms.id
    lexical_norms.lemma_id   → lexical_lemmas.id

Run after ingestion:
    python -m core.jobs.lexical_occurrences
"""

import logging
from datetime import datetime, timezone

from core.database import connect_one_shot

logger = logging.getLogger(__name__)

# Process lemmas in batches to limit peak memory pressure.
BATCH_SIZE = 10_000


def _aggregate(conn) -> list[dict]:
    """Return one row per (lemma_id, p_number) with occurrence_count."""
    sql = """
        SELECT
            ln.lemma_id,
            tl.p_number,
            COUNT(*) AS occurrence_count
        FROM lemmatizations lz
        JOIN tokens         t  ON t.id  = lz.token_id
        JOIN text_lines     tl ON tl.id = t.line_id
        JOIN lexical_norms  ln ON ln.id = lz.norm_id
        WHERE lz.norm_id IS NOT NULL
          AND ln.lemma_id IS NOT NULL
          AND tl.p_number IS NOT NULL
        GROUP BY ln.lemma_id, tl.p_number
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def compute_occurrences() -> int:
    """Populate ``lexical_tablet_occurrences`` for all lemmas.

    Strategy:
    1. Aggregate (lemma_id, p_number, occurrence_count) in one pass.
    2. DELETE all existing rows where lemma_id IS NOT NULL (keeps sign/sense rows
       that we don't own intact).
    3. INSERT the fresh rows.

    Returns the number of rows inserted.
    """
    conn = connect_one_shot()
    try:
        logger.info("Aggregating lemma tablet occurrences…")
        rows = _aggregate(conn)
        logger.info("Aggregation complete — %d (lemma, p_number) pairs", len(rows))

        if not rows:
            logger.warning(
                "No rows to insert — check that lemmatizations.norm_id is populated"
            )
            return 0

        computed_at = datetime.now(timezone.utc)

        with conn.cursor() as cur:
            # Clear prior lemma-based occurrence rows only — leave sign/sense rows alone.
            cur.execute(
                "DELETE FROM lexical_tablet_occurrences WHERE lemma_id IS NOT NULL"
            )
            deleted = cur.rowcount
            logger.info("Deleted %d stale lemma occurrence rows", deleted)

        # Batch-insert to avoid a single enormous transaction.
        inserted = 0
        insert_sql = """
            INSERT INTO lexical_tablet_occurrences
                        (lemma_id, p_number, occurrence_count, computed_at)
            VALUES      (%(lemma_id)s, %(p_number)s, %(occurrence_count)s, %(computed_at)s)
        """
        for batch_start in range(0, len(rows), BATCH_SIZE):
            batch = rows[batch_start : batch_start + BATCH_SIZE]
            with conn.cursor() as cur:
                cur.executemany(
                    insert_sql,
                    [
                        {
                            "lemma_id": r["lemma_id"],
                            "p_number": r["p_number"],
                            "occurrence_count": r["occurrence_count"],
                            "computed_at": computed_at,
                        }
                        for r in batch
                    ],
                )
            conn.commit()
            inserted += len(batch)
            logger.info(
                "Inserted %d / %d rows (%.0f%%)",
                inserted,
                len(rows),
                100 * inserted / len(rows),
            )

        logger.info("Done — %d rows inserted", inserted)
        return inserted

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    count = compute_occurrences()
    print(f"Inserted {count} lemma tablet occurrence rows")
