"""DLQ replay (#174) — re-run stored dead-letter payloads through current logic.

`python -m ingestion.cli dlq-replay <connector> [--category X] [--subcategory Y]
[--limit N] [--dry-run]`

Pulls OPEN rows from `import_dead_letters` for a connector, re-runs each stored
JSONB payload through the connector's *current* match logic, and on success
marks the row `resolution_status='fixed'` (+ `resolved_at`, `resolved_by`). Rows
that still don't match are left `open`.

Design properties:
- **Idempotent / safe to re-run.** Inserts use ON CONFLICT DO NOTHING; only rows
  that newly resolve are marked fixed. Re-running picks up whatever is still open
  and does no harm to already-fixed rows (they're no longer selected).
- **Batched.** Reads and commits in batches so a 73K replay never holds one giant
  transaction. Each batch builds the line/token caches for just that batch's
  p_numbers.
- **Dry-run.** Reports how many *would* resolve without writing lemmatizations or
  touching resolution_status.

Adding replay for another connector = register a handler in REPLAY_HANDLERS.
A handler is a callable(db, rows, *, dry_run) -> (fixed_ids, still_open) that
owns its connector's match semantics.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from ingestion.connectors.oracc_lemmatizations import OraccLemmatizationsConnector

BATCH_SIZE = 2000

# A handler returns the list of dead-letter ids it resolved in this batch.
ReplayHandler = Callable[[Any, list[dict], bool], list[int]]


def _oracc_lemmatizations_handler(
    db: Any, rows: list[dict], dry_run: bool
) -> list[int]:
    """Replay a batch of oracc-lemmatizations dead letters.

    Each `rows` element is a dict with at least `id` and `payload` (the stored
    JSONB, already deserialized by psycopg). Resolution reuses the connector's
    shared match helpers so behaviour is identical to a fresh ingestion run.
    """
    # Resolve annotation_run_id per project once (source_name = "oracc/{project}").
    projects: set[str] = set()
    p_number_set: set[str] = set()
    for r in rows:
        payload = r["payload"] or {}
        proj = payload.get("project")
        if proj:
            projects.add(proj)
        pnum = payload.get("p_number")
        if pnum:
            p_number_set.add(pnum)

    ann_run_ids: dict[str, int] = {}
    for proj in projects:
        arow = db.execute(
            "SELECT id FROM annotation_runs WHERE source_name = %s",
            (f"oracc/{proj}",),
        ).fetchone()
        if arow:
            ann_run_ids[proj] = arow["id"] if isinstance(arow, dict) else arow[0]

    p_numbers = sorted(p_number_set)
    line_cache, token_cache = OraccLemmatizationsConnector.build_caches_for_payloads(
        db, p_numbers
    )

    fixed_ids: list[int] = []
    for r in rows:
        payload = r["payload"] or {}
        project = payload.get("project")
        # Default to run id 1 to mirror load()'s fallback when a project's
        # annotation_run row is missing; that fallback is the established
        # connector behaviour, not a replay-specific invention.
        ann_run_id = ann_run_ids.get(project, 1) if project else 1
        if OraccLemmatizationsConnector.resolve_payload(
            db, payload, ann_run_id, line_cache, token_cache
        ):
            fixed_ids.append(r["id"])
    if dry_run:
        # Undo any lemmatization inserts the probe made; resolution_status is
        # never touched in dry-run, so nothing else needs rolling back.
        db.rollback()
    return fixed_ids


REPLAY_HANDLERS: dict[str, ReplayHandler] = {
    "oracc-lemmatizations": _oracc_lemmatizations_handler,
}


def _fetch_batch(
    db: Any,
    connector_id: str,
    category: Optional[str],
    subcategory: Optional[str],
    after_id: int,
    batch_size: int,
) -> list[dict]:
    """Fetch the next batch of OPEN dead letters by ascending id.

    Keyset pagination on id (> after_id) is stable even as rows get marked
    fixed, because fixed rows simply drop out of the `resolution_status='open'`
    predicate and ids only move forward.
    """
    clauses = ["connector_id = %s", "resolution_status = 'open'", "id > %s"]
    params: list[Any] = [connector_id, after_id]
    if category:
        clauses.append("category = %s")
        params.append(category)
    if subcategory:
        clauses.append("subcategory = %s")
        params.append(subcategory)
    params.append(batch_size)
    rows = db.execute(
        f"SELECT id, payload FROM import_dead_letters "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY id ASC LIMIT %s",
        tuple(params),
    ).fetchall()
    return [dict(r) for r in rows]


def _mark_fixed(db: Any, ids: list[int]) -> int:
    if not ids:
        return 0
    result = db.execute(
        """
        UPDATE import_dead_letters
        SET resolution_status = 'fixed',
            resolved_at = NOW(),
            resolved_by = 'dlq-replay'
        WHERE id = ANY(%s) AND resolution_status = 'open'
        """,
        (ids,),
    )
    db.commit()
    return result.rowcount or 0


def replay(
    db: Any,
    connector_id: str,
    *,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    batch_size: int = BATCH_SIZE,
    progress: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Replay open dead letters for one connector. Returns a summary dict.

    `limit` caps the total number of dead letters *examined* (not just fixed),
    so a `--limit 1000 --dry-run` gives a fast representative projection.
    """
    handler = REPLAY_HANDLERS.get(connector_id)
    if handler is None:
        raise ValueError(
            f"No DLQ replay handler registered for connector {connector_id!r}. "
            f"Known: {sorted(REPLAY_HANDLERS)}"
        )

    examined = 0
    fixed = 0
    after_id = 0
    while True:
        remaining = None if limit is None else max(0, limit - examined)
        if remaining == 0:
            break
        this_batch = batch_size if remaining is None else min(batch_size, remaining)
        rows = _fetch_batch(
            db, connector_id, category, subcategory, after_id, this_batch
        )
        if not rows:
            break
        after_id = rows[-1]["id"]
        examined += len(rows)

        fixed_ids = handler(db, rows, dry_run)
        if dry_run:
            # handler already rolled back its probe inserts; count only.
            fixed += len(fixed_ids)
        else:
            db.commit()  # persist the lemmatization inserts from this batch
            marked = _mark_fixed(db, fixed_ids)
            fixed += marked
        if progress:
            progress({"examined": examined, "fixed": fixed})

    return {
        "connector_id": connector_id,
        "dry_run": dry_run,
        "examined": examined,
        "fixed": fixed,
        "still_open": examined - fixed,
    }
