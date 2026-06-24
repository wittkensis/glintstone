"""Run a SourceConnector end-to-end with full progress tracking.

The runner is what wraps a connector subclass into a real ingestion:
1. Opens a DB connection
2. Inserts an `import_runs` row (status='running')
3. Calls discover() → checks against last successful run's checksum
4. If skip allowed, marks status='no_op' and exits
5. Else calls extract → transform → load with the connector's RunContext
6. Calls verify()
7. Updates the run row with final stats and status='succeeded' or 'failed'

Idempotency, retries, and dead-letter routing all flow through here so
connectors stay focused on data shape.
"""

from __future__ import annotations

import json
import subprocess
import traceback
from datetime import datetime, timezone
from typing import Optional

from core.database import connect_one_shot
from ingestion.base import (
    LoadStats,
    ModelConnector,
    RunContext,
    RunMode,
    SourceConnector,
    utc_now,
)
from ingestion.dead_letters import DeadLetterSink


def _git_sha() -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _last_successful_checksum(db, connector_id: str) -> Optional[str]:
    row = db.execute(
        """
        SELECT source_checksum
        FROM import_runs
        WHERE connector_id = %s AND status = 'succeeded'
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (connector_id,),
    ).fetchone()
    return (
        (row["source_checksum"] if isinstance(row, dict) else row[0]) if row else None
    )


def upsert_source_row(db, connector_cls: type[SourceConnector]) -> None:
    row = connector_cls.to_source_row()
    db.execute(
        """
        INSERT INTO sources (
            id, display_name, description, kind, upstream_url,
            license, license_url, citation, contact_email, runs_after, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (id) DO UPDATE SET
            display_name  = EXCLUDED.display_name,
            description   = EXCLUDED.description,
            kind          = EXCLUDED.kind,
            upstream_url  = EXCLUDED.upstream_url,
            license       = EXCLUDED.license,
            license_url   = EXCLUDED.license_url,
            citation      = EXCLUDED.citation,
            contact_email = EXCLUDED.contact_email,
            runs_after    = EXCLUDED.runs_after,
            updated_at    = NOW()
        """,
        (
            row["id"],
            row["display_name"],
            row["description"],
            row["kind"],
            row["upstream_url"],
            row["license"],
            row["license_url"],
            row["citation"],
            row["contact_email"],
            row["runs_after"],
        ),
    )
    db.commit()


def run_connector(
    connector_cls: type[SourceConnector],
    *,
    mode: RunMode = RunMode.FULL,
    app_env: str = "local",
    force: bool = False,
    config: Optional[dict] = None,
) -> dict:
    """Execute a connector end-to-end. Returns a summary dict.

    On any exception, the run is marked 'failed' with the traceback recorded
    in `error_summary` and re-raised.
    """
    connector = connector_cls()
    db = connect_one_shot()
    started = utc_now()
    started_perf = datetime.now(timezone.utc)

    upsert_source_row(db, connector_cls)

    # Bind a model row if this is a ModelConnector
    model_id = None
    if isinstance(connector, ModelConnector):
        model_id = connector.register_model_version(db)

    # Open the run record
    row = db.execute(
        """
        INSERT INTO import_runs
            (connector_id, run_mode, app_env, started_at, status,
             config_json, model_id, git_sha)
        VALUES (%s, %s, %s, %s, 'running', %s::jsonb, %s, %s)
        RETURNING id
        """,
        (
            connector_cls.id,
            mode.value,
            app_env,
            started,
            json.dumps(config or {}, default=str),
            model_id,
            _git_sha(),
        ),
    ).fetchone()
    if row is None:
        raise RuntimeError("INSERT INTO import_runs ... RETURNING id returned no row")
    run_id = row["id"] if isinstance(row, dict) else row[0]
    db.commit()

    sink = DeadLetterSink(db)
    ctx = RunContext(
        run_id=run_id,
        connector_id=connector_cls.id,
        mode=mode,
        db_conn=db,
        dead_letter_sink=sink,
        config=config or {},
    )

    summary: dict = {"run_id": run_id, "connector_id": connector_cls.id}

    try:
        ctx.info("run.start", mode=mode.value, app_env=app_env)
        manifest = connector.discover(ctx)
        last_checksum = _last_successful_checksum(db, connector_cls.id)

        if (
            not force
            and mode != RunMode.VERIFY_ONLY
            and manifest.checksum is not None
            and manifest.checksum == last_checksum
        ):
            ctx.info(
                "run.skip_unchanged",
                checksum=manifest.checksum,
                reason="source unchanged since last successful run",
            )
            _finalize_run(
                db,
                run_id,
                started_perf,
                status="no_op",
                checksum=manifest.checksum,
                fetched_at=manifest.fetched_at,
                stats=ctx.stats,
            )
            summary["status"] = "no_op"
            return summary

        if mode != RunMode.VERIFY_ONLY:
            extracted = connector.extract(ctx)
            transformed = _flatten_transform(connector, ctx, extracted)
            stats = connector.load(ctx, transformed)
            ctx.add_stats(stats)

        connector.verify(ctx)

        _finalize_run(
            db,
            run_id,
            started_perf,
            status="succeeded",
            checksum=manifest.checksum,
            fetched_at=manifest.fetched_at,
            stats=ctx.stats,
        )
        ctx.info(
            "run.complete",
            inserted=ctx.stats.inserted,
            updated=ctx.stats.updated,
            skipped=ctx.stats.skipped,
            dead_lettered=ctx.stats.dead_lettered,
        )
        summary.update(
            {
                "status": "succeeded",
                "inserted": ctx.stats.inserted,
                "updated": ctx.stats.updated,
                "skipped": ctx.stats.skipped,
                "dead_lettered": ctx.stats.dead_lettered,
            }
        )
        return summary

    except Exception as exc:
        tb = traceback.format_exc(limit=10)
        try:
            ctx.error("run.failed", error=str(exc))
        except Exception:
            pass
        # The failing connector may have left the connection in an aborted
        # transaction; roll back so _finalize_run's UPDATE can execute.
        try:
            db.rollback()
        except Exception:
            pass
        _finalize_run(
            db,
            run_id,
            started_perf,
            status="failed",
            checksum=None,
            fetched_at=None,
            stats=ctx.stats,
            error_summary=f"{exc}\n\n{tb}",
        )
        summary["status"] = "failed"
        summary["error"] = str(exc)
        raise
    finally:
        db.close()


def _flatten_transform(connector, ctx, records):
    for record in records:
        yield from connector.transform(ctx, record)


def _finalize_run(
    db,
    run_id: int,
    started_perf: datetime,
    *,
    status: str,
    checksum: Optional[str],
    fetched_at: Optional[datetime],
    stats: LoadStats,
    error_summary: Optional[str] = None,
) -> None:
    duration_ms = int(
        (datetime.now(timezone.utc) - started_perf).total_seconds() * 1000
    )
    db.execute(
        """
        UPDATE import_runs
        SET finished_at        = NOW(),
            status             = %s,
            source_checksum    = %s,
            source_fetched_at  = %s,
            rows_inserted      = %s,
            rows_updated       = %s,
            rows_skipped       = %s,
            rows_dead_lettered = %s,
            error_summary      = %s,
            duration_ms        = %s
        WHERE id = %s
        """,
        (
            status,
            checksum,
            fetched_at,
            stats.inserted,
            stats.updated,
            stats.skipped,
            stats.dead_lettered,
            error_summary,
            duration_ms,
            run_id,
        ),
    )
    db.commit()
