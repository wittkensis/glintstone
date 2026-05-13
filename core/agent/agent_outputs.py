"""Lazy persist + supersession invalidation for agent_outputs.

The rule: a generated summary or interpretation is persisted on first
request and reused until any of the annotation_runs it cites gets a newer
sibling. We don't run a sweep; we check at read time.

Reuse window:
  - superseded_at IS NULL
  - generated_at > now() - INTERVAL '30 days'  (safety net)
  - prompt_version matches current

If reuse fails, the caller regenerates and inserts a new row. The old row
stays in place with superseded_at set.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime

import psycopg

from core.schemas.citation import Citation

logger = logging.getLogger(__name__)

_REUSE_TTL_DAYS = 30


@dataclass
class PersistedOutput:
    id: int
    interaction_id: int | None
    output_type: str
    target_type: str
    target_id: str
    focus: str | None
    model: str
    prompt_version: str
    output_text: str
    citations: list[Citation]
    source_run_ids: list[int]
    best_guess_flag: bool
    generated_at: datetime


def find_fresh(
    conn: psycopg.Connection,
    *,
    output_type: str,
    target_type: str,
    target_id: str,
    focus: str | None,
    prompt_version: str,
) -> PersistedOutput | None:
    """Return the current non-superseded row if it's still fresh, else None."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, interaction_id, output_type, target_type, target_id,
                   focus, model, prompt_version, output_text, citations,
                   source_run_ids, best_guess_flag, generated_at
            FROM agent_outputs
            WHERE output_type = %s
              AND target_type = %s
              AND target_id = %s
              AND COALESCE(focus, '') = COALESCE(%s, '')
              AND prompt_version = %s
              AND superseded_at IS NULL
              AND generated_at > now() - INTERVAL '%s days'
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (
                output_type,
                target_type,
                target_id,
                focus,
                prompt_version,
                _REUSE_TTL_DAYS,
            ),
        )
        row = cur.fetchone()
    if not row:
        return None

    # Check supersession by annotation_runs
    if _has_newer_annotation_run(conn, row["source_run_ids"]):
        _mark_superseded(conn, row["id"])
        return None

    citations = [Citation(**c) for c in (row["citations"] or [])]
    return PersistedOutput(
        id=row["id"],
        interaction_id=row.get("interaction_id"),
        output_type=row["output_type"],
        target_type=row["target_type"],
        target_id=row["target_id"],
        focus=row.get("focus"),
        model=row["model"],
        prompt_version=row["prompt_version"],
        output_text=row["output_text"],
        citations=citations,
        source_run_ids=list(row.get("source_run_ids") or []),
        best_guess_flag=row.get("best_guess_flag") or False,
        generated_at=row["generated_at"],
    )


def insert(
    conn: psycopg.Connection,
    *,
    interaction_id: int | None,
    output_type: str,
    target_type: str,
    target_id: str,
    focus: str | None,
    model: str,
    prompt_version: str,
    output_text: str,
    citations: list[Citation],
    source_run_ids: list[int],
    best_guess_flag: bool,
) -> int:
    """Insert a new agent_outputs row. Supersedes any existing fresh row first."""
    # If there's a fresh row for the same key, mark it superseded so the
    # partial unique index doesn't reject our insert.
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE agent_outputs
            SET superseded_at = now()
            WHERE output_type = %s
              AND target_type = %s
              AND target_id = %s
              AND COALESCE(focus, '') = COALESCE(%s, '')
              AND prompt_version = %s
              AND superseded_at IS NULL
            """,
            (output_type, target_type, target_id, focus, prompt_version),
        )

        cur.execute(
            """
            INSERT INTO agent_outputs (
                interaction_id, output_type, target_type, target_id, focus,
                model, prompt_version, output_text, citations,
                source_run_ids, best_guess_flag
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            RETURNING id
            """,
            (
                interaction_id,
                output_type,
                target_type,
                target_id,
                focus,
                model,
                prompt_version,
                output_text,
                json.dumps([c.model_dump(mode="json") for c in citations]),
                source_run_ids,
                best_guess_flag,
            ),
        )
        new_id = cur.fetchone()["id"]
    conn.commit()
    return new_id


def _has_newer_annotation_run(
    conn: psycopg.Connection, source_run_ids: list[int]
) -> bool:
    if not source_run_ids:
        return False
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM annotation_runs ar_old
            JOIN annotation_runs ar_new
              ON ar_new.source_name = ar_old.source_name
             AND ar_new.created_at > ar_old.created_at
             AND ar_new.id <> ALL(%s)
            WHERE ar_old.id = ANY(%s)
            LIMIT 1
            """,
            (source_run_ids, source_run_ids),
        )
        return cur.fetchone() is not None


def _mark_superseded(conn: psycopg.Connection, row_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE agent_outputs SET superseded_at = now() WHERE id = %s",
            (row_id,),
        )
    conn.commit()
