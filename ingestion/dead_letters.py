"""DeadLetterSink — routes every record that fails to integrate.

Replaces ad-hoc disk files like `_progress/19_unmatched_translations.json`,
`_progress/unmatched_sign_values.txt`. Every dead letter carries its original
payload as JSONB plus a category and resolution status, so they become a
triage queue you can query, mark resolved, or replay after a fix.

Categories are constrained by the DB CHECK constraint:
    validation_failed, no_match, missing_reference, schema_drift, duplicate, other
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Optional


class DeadLetterCategory(str, Enum):
    VALIDATION_FAILED = "validation_failed"
    NO_MATCH = "no_match"
    MISSING_REFERENCE = "missing_reference"
    SCHEMA_DRIFT = "schema_drift"
    DUPLICATE = "duplicate"
    OTHER = "other"


class DeadLetterSink:
    """Writes to `import_dead_letters`. One instance per RunContext."""

    def __init__(self, db_conn: Any) -> None:
        self.db = db_conn

    def write(
        self,
        *,
        run_id: int,
        connector_id: str,
        category: str,
        payload: dict,
        reason: str,
        subcategory: Optional[str] = None,
        source_key: Optional[str] = None,
    ) -> int:
        """Insert one dead-letter row, returning its id."""
        if category not in {c.value for c in DeadLetterCategory}:
            raise ValueError(
                f"Invalid dead-letter category: {category!r}. "
                f"Valid: {[c.value for c in DeadLetterCategory]}"
            )
        result = self.db.execute(
            """
            INSERT INTO import_dead_letters
                (run_id, connector_id, category, subcategory, source_key, payload, reason)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
            RETURNING id
            """,
            (
                run_id,
                connector_id,
                category,
                subcategory,
                source_key,
                json.dumps(payload, default=str, ensure_ascii=False),
                reason,
            ),
        ).fetchone()
        self.db.commit()
        return result["id"] if isinstance(result, dict) else result[0]

    def count_open(self, connector_id: str) -> int:
        row = self.db.execute(
            """
            SELECT COUNT(*) AS n
            FROM import_dead_letters
            WHERE connector_id = %s AND resolution_status = 'open'
            """,
            (connector_id,),
        ).fetchone()
        return row["n"] if isinstance(row, dict) else row[0]

    def resolve(
        self,
        ids: list[int],
        *,
        status: str,
        note: Optional[str] = None,
        resolved_by: Optional[str] = None,
    ) -> int:
        """Mark a batch of dead letters as resolved. Returns rows updated."""
        if status not in {"open", "investigating", "wontfix", "fixed", "duplicate"}:
            raise ValueError(f"Invalid resolution status: {status!r}")
        if not ids:
            return 0
        result = self.db.execute(
            """
            UPDATE import_dead_letters
            SET resolution_status = %s,
                resolution_note = COALESCE(%s, resolution_note),
                resolved_by = COALESCE(%s, resolved_by),
                resolved_at = CASE WHEN %s IN ('wontfix','fixed','duplicate')
                                   THEN NOW() ELSE resolved_at END
            WHERE id = ANY(%s)
            """,
            (status, note, resolved_by, status, ids),
        )
        self.db.commit()
        return result.rowcount or 0
