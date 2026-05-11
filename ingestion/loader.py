"""Batch loaders that make safe-rerun explicit.

Connectors declare a conflict policy and unique key per call; the loader
emits an `INSERT ... ON CONFLICT` matching that policy. Returns counts
(inserted vs updated vs skipped) so the RunContext can aggregate them.
"""

from __future__ import annotations

from typing import Iterable

from ingestion.base import ConflictPolicy, LoadStats


def upsert_batch(
    db,
    *,
    table: str,
    rows: Iterable[dict],
    unique_key: list[str],
    columns: list[str] | None = None,
    policy: ConflictPolicy = ConflictPolicy.SKIP,
    batch_size: int = 1000,
) -> LoadStats:
    """Insert rows into `table`, handling conflicts on `unique_key`.

    - SKIP    → `ON CONFLICT DO NOTHING` (counts as skipped)
    - UPDATE  → `ON CONFLICT DO UPDATE SET <every non-key column>=EXCLUDED.*`
    - REPLACE → same as UPDATE for now (semantic distinction reserved for future)

    Returns LoadStats with counts. Uses RETURNING to distinguish insert from
    update via `xmax = 0` (true if the row was freshly inserted).
    """
    rows_list = list(rows)
    if not rows_list:
        return LoadStats()

    if columns is None:
        columns = list(rows_list[0].keys())

    if not _safe_ident(table) or not all(_safe_ident(c) for c in columns + unique_key):
        raise ValueError("Identifiers must be alphanumeric+underscore.")

    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    unique_list = ", ".join(unique_key)

    if policy == ConflictPolicy.SKIP:
        conflict_clause = "ON CONFLICT (" + unique_list + ") DO NOTHING"
    else:
        non_key = [c for c in columns if c not in unique_key]
        if not non_key:
            conflict_clause = "ON CONFLICT (" + unique_list + ") DO NOTHING"
        else:
            set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in non_key)
            conflict_clause = (
                "ON CONFLICT (" + unique_list + ") DO UPDATE SET " + set_clause
            )

    sql = (
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"{conflict_clause} RETURNING (xmax = 0) AS inserted"
    )

    stats = LoadStats()
    buf: list[tuple] = []
    for r in rows_list:
        buf.append(tuple(r.get(c) for c in columns))
        if len(buf) >= batch_size:
            stats = stats.merge(_flush(db, sql, buf, policy))
            buf.clear()
    if buf:
        stats = stats.merge(_flush(db, sql, buf, policy))
    return stats


def _flush(db, sql: str, buf: list[tuple], policy: ConflictPolicy) -> LoadStats:
    stats = LoadStats()
    with db.cursor() as cur:
        for tup in buf:
            cur.execute(sql, tup)
            result = cur.fetchone()
            if result is None:
                # SKIP policy → conflict, no row returned
                stats.skipped += 1
            else:
                inserted = result["inserted"] if isinstance(result, dict) else result[0]
                if inserted:
                    stats.inserted += 1
                else:
                    stats.updated += 1
    db.commit()
    return stats


def _safe_ident(s: str) -> bool:
    """Cheap allow-list check to keep f-string SQL identifiers safe."""
    return bool(s) and s.replace("_", "").isalnum()
