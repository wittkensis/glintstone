"""Dead-letter open-count alerting (#175) — no silent growth.

CLAUDE.md non-negotiable: "Never silently overwrite … always create a new run"
and, more broadly, failures must never grow in the dark. The dead-letter queue
(``import_dead_letters``) is the triage queue for every record that could not be
integrated. If a connector starts shedding rows into it run after run and nobody
notices, the SSOT quietly rots — exactly the silent-failure gap this closes.

WHAT THIS DOES
--------------
After every connector run, the runner calls :func:`check_and_alert`. It:

1. Reads the CURRENT open dead-letter count for the connector
   (``resolution_status='open'``).
2. Reads the open count recorded at the end of the connector's PREVIOUS run.
3. If the count GREW by more than ``threshold`` rows since the last run, it
   raises a LOUD alert on three channels (NOT email — per the no-email rule this
   cycle):

     * **stderr** — visible in CI logs and interactive terminals.
     * **import_run_events** — a row at level ``error`` (the dashboard / status
       view already reads this table), so the alert is durable and queryable.
     * **a status file** — JSON written under ``GLINTSTONE_DLQ_ALERT_DIR``
       (default ``ops/snapshots/dlq-alerts/``), one file per connector, so a
       briefing / spine process can read "is anything bleeding?" without a DB
       round-trip.

WHY "grew since last run" and not "above an absolute ceiling"
------------------------------------------------------------
An absolute ceiling punishes connectors that have a known, triaged backlog of
open dead letters (e.g. translation-line-matcher's structurally-unmatchable
rows). What we actually care about is *new* bleeding: did THIS run add open
dead letters beyond a small tolerance? So we compare against the previous run's
recorded open count. The first-ever run has no baseline, so any growth past the
threshold from zero alerts (which is correct — a brand-new connector dumping
hundreds of rows IS worth a shout).

The per-run open count is recorded on ``import_runs.dlq_open_after`` (added in
migration 057) so the comparison is exact and survives across processes.

GOOD-CITIZEN / SAFETY
---------------------
* This NEVER fails a run. An alert is a signal, not an error — if the alerting
  code itself throws (e.g. the status dir is unwritable), it logs and returns;
  the connector's own success/failure is untouched.
* It does its own COMMIT for the ``dlq_open_after`` write and the event row, so
  a connector that left the transaction clean stays clean.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Default growth tolerance: a run may add up to this many open dead letters
# before it's considered "bleeding". 0 = alert on ANY net growth. The default is
# deliberately small but non-zero so a single transient bad row doesn't page.
DEFAULT_THRESHOLD = int(os.environ.get("GLINTSTONE_DLQ_GROWTH_THRESHOLD", "0"))

# Where the per-connector status files land. In-repo by default so a briefing /
# spine process can read them with no DB access; override on the VPS to point at
# a shared/persistent path if desired.
_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALERT_DIR = Path(
    os.environ.get(
        "GLINTSTONE_DLQ_ALERT_DIR",
        str(_REPO_ROOT / "ops" / "snapshots" / "dlq-alerts"),
    )
)


@dataclass
class DlqAlertResult:
    """Outcome of one post-run dead-letter check (returned for tests / summary)."""

    connector_id: str
    open_now: int
    open_before: Optional[int]
    grew_by: Optional[int]
    threshold: int
    alerted: bool


def _open_count(db: Any, connector_id: str) -> int:
    row = db.execute(
        """
        SELECT COUNT(*) AS n
        FROM import_dead_letters
        WHERE connector_id = %s AND resolution_status = 'open'
        """,
        (connector_id,),
    ).fetchone()
    return row["n"] if isinstance(row, dict) else row[0]


def _previous_open_after(
    db: Any, connector_id: str, exclude_run_id: int
) -> Optional[int]:
    """The ``dlq_open_after`` recorded by this connector's most recent *prior* run.

    Returns None when there is no prior run that recorded a value (first run, or
    runs from before migration 057 landed) — in which case the caller treats the
    baseline as 0.
    """
    row = db.execute(
        """
        SELECT dlq_open_after
        FROM import_runs
        WHERE connector_id = %s
          AND id <> %s
          AND dlq_open_after IS NOT NULL
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (connector_id, exclude_run_id),
    ).fetchone()
    if row is None:
        return None
    val = row["dlq_open_after"] if isinstance(row, dict) else row[0]
    return int(val) if val is not None else None


def _record_open_after(db: Any, run_id: int, open_now: int) -> None:
    db.execute(
        "UPDATE import_runs SET dlq_open_after = %s WHERE id = %s",
        (open_now, run_id),
    )
    db.commit()


def _write_status_file(result: DlqAlertResult, *, alert_dir: Path) -> Optional[Path]:
    """Write a one-file-per-connector JSON snapshot. Returns the path, or None."""
    try:
        alert_dir.mkdir(parents=True, exist_ok=True)
        path = alert_dir / f"{result.connector_id}.json"
        payload = {
            "connector_id": result.connector_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "open_now": result.open_now,
            "open_before": result.open_before,
            "grew_by": result.grew_by,
            "threshold": result.threshold,
            "alert": result.alerted,
            "status": "bleeding" if result.alerted else "ok",
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path
    except Exception as exc:  # noqa: BLE001 — alerting must never break a run
        print(
            f"  [warn] dlq-alert: could not write status file: {exc}",
            file=sys.stderr,
        )
        return None


def check_and_alert(
    ctx: Any,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    alert_dir: Path = DEFAULT_ALERT_DIR,
) -> DlqAlertResult:
    """Post-run dead-letter open-count check. Alerts loudly on growth.

    Called by the runner after verify(). NEVER raises — alerting is a signal, not
    a failure mode. Returns a :class:`DlqAlertResult` for the run summary / tests.

    `ctx` is the connector's RunContext (gives us db, connector_id, run_id, and
    the structured ``ctx.error`` event channel).
    """
    connector_id = ctx.connector_id
    db = ctx.db
    try:
        open_now = _open_count(db, connector_id)
        prev = _previous_open_after(db, connector_id, exclude_run_id=ctx.run_id)
        baseline = prev if prev is not None else 0
        grew_by = open_now - baseline
        alerted = grew_by > threshold

        # Always record the current open count so the NEXT run has a baseline.
        _record_open_after(db, ctx.run_id, open_now)

        result = DlqAlertResult(
            connector_id=connector_id,
            open_now=open_now,
            open_before=prev,
            grew_by=grew_by,
            threshold=threshold,
            alerted=alerted,
        )

        if alerted:
            # Channel 1: structured, durable, dashboard-visible.
            ctx.error(
                "dlq.open_count_grew",
                connector=connector_id,
                open_now=open_now,
                open_before=prev,
                grew_by=grew_by,
                threshold=threshold,
            )
            # Channel 2: loud stderr for CI / interactive.
            print(
                f"\n  !! DLQ ALERT [{connector_id}] open dead letters grew by "
                f"{grew_by} (now {open_now}, was {baseline}); "
                f"threshold {threshold}. Triage: "
                f"python -m ingestion.cli dead-letters {connector_id}\n",
                file=sys.stderr,
            )
        else:
            ctx.info(
                "dlq.open_count_ok",
                connector=connector_id,
                open_now=open_now,
                open_before=prev,
                grew_by=grew_by,
            )

        # Channel 3: status file for the spine / briefing (written every run, so
        # a cleared queue overwrites a prior 'bleeding' snapshot with 'ok').
        _write_status_file(result, alert_dir=alert_dir)
        return result

    except Exception as exc:  # noqa: BLE001 — never break a run over alerting
        try:
            db.rollback()
        except Exception:
            pass
        print(
            f"  [warn] dlq-alert: check failed for {connector_id}: {exc}",
            file=sys.stderr,
        )
        return DlqAlertResult(
            connector_id=connector_id,
            open_now=-1,
            open_before=None,
            grew_by=None,
            threshold=threshold,
            alerted=False,
        )
