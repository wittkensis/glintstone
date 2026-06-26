#!/usr/bin/env python3
"""Weekly data-integrity audit for Glintstone (backlog #490).

What this does, in plain English
--------------------------------
Once a week a scheduled job runs this script. It asks the database three
health questions, writes the answers to a dated JSON file, prints a short
human-readable summary, and raises an alarm (a non-zero exit code) if anything
looks worse than it did the last time it ran.

The three questions, and how they map onto the *real* Glintstone schema
-----------------------------------------------------------------------
The original ticket described these checks against table names that don't
exist in this database (``ingestion_jobs``, a ``status='dead_letter'`` column,
a ``lemmas.normalized_form`` column, an ``artifacts.pipeline_status`` enum).
The intent is clear, so each check is implemented against the table that
actually carries that concept:

1. **Dead-letter open-count by reason.**
   Failed ingestion rows live in ``import_dead_letters``. A row is still a
   problem while ``resolution_status = 'open'``. We group the open rows by
   ``category`` (the structured failure reason) and, secondarily, by the free
   text ``reason``. Alert if the total number of *open* dead-letters has gone
   up since the previous run.

2. **Wrong-lemma / mis-targeted annotation check.**
   There is no ``lemmas.normalized_form`` column; the normalized form lives in
   ``lemmatizations.norm``. We count lemmatizations whose ``norm`` is missing
   (NULL or empty) — those are lemmas that never got a normalized form, the
   real-world equivalent of the ticket's "wrong-lemma" case. Because
   ``annotation_runs`` has no ``status`` column (it never records 'failed'),
   the equivalent "mis-targeted run" signal in this schema is an annotation
   that carries no source attribution at all — ``annotation_run_id IS NULL`` —
   which CLAUDE.md calls a structural violation. We surface both counts.

3. **Pipeline-status drift.**
   ``pipeline_status`` is a per-tablet table of completeness percentages, not
   an enum. We bucket every tablet into one of four stages (complete /
   advanced / partial / empty) from its ``*_complete`` columns, then compare
   this week's distribution to last week's. Alert if any bucket's share of the
   corpus moved by more than the drift threshold.

Because the database keeps no history of past distributions, "last run" is
read from the most recent JSON report this script previously wrote. The first
ever run therefore has nothing to compare against and is treated as clean.

Database connection
-------------------
``DATABASE_URL`` is read, in order, from: the process environment, then
``~/.claude/state/glintstone.env`` if it exists, then the project's own
``core.config`` settings (which load ``.env``). All DB imports are lazy so the
module imports cleanly even with no database and no project deps installed.

Usage
-----
    python3 ops/data_integrity_audit.py            # run, write report, exit 0/1
    python3 ops/data_integrity_audit.py --dry-run  # run, do NOT write report
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Paths and thresholds
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPORTS_DIR = _REPO_ROOT / "ops" / "reports"
_GLOBAL_ENV = Path.home() / ".claude" / "state" / "glintstone.env"

# Alert thresholds.
#   - Any increase in open dead-letters vs. last run is an alert.
#   - Pipeline-bucket share moving by more than this many PERCENTAGE POINTS
#     (e.g. 22% -> 33% is +11pp) is an alert. The ticket says ">10%".
_DEADLETTER_INCREASE_TRIGGERS_ALERT = True
_PIPELINE_DRIFT_PP_THRESHOLD = 10.0


# --------------------------------------------------------------------------- #
# Environment / connection
# --------------------------------------------------------------------------- #


def _load_env_file(path: Path) -> dict[str, str]:
    """Parse a tiny KEY=VALUE env file. Ignores blanks and # comments."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.lower().startswith("export "):
            key = key[len("export "):].strip()
        val = val.strip().strip('"').strip("'")
        out[key] = val
    return out


def resolve_database_url() -> str | None:
    """Find a DATABASE_URL without importing any DB driver.

    Order: process env -> ~/.claude/state/glintstone.env -> project .env via
    core.config. Returns None if nothing yields one.
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    file_env = _load_env_file(_GLOBAL_ENV)
    if file_env.get("DATABASE_URL"):
        return file_env["DATABASE_URL"]

    # Last resort: ask the project's own settings (loads .env, supports the
    # discrete DB_* fallback). Imported lazily so a missing dep never breaks
    # `--dry-run` import-time behaviour.
    try:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from core.config import get_settings  # type: ignore

        settings = get_settings()
        url = settings.database_url or settings.psycopg_conninfo()
        return url or None
    except Exception:
        return None


def _connect(conninfo: str):
    """Open a one-shot psycopg connection with dict rows. Imported lazily."""
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    return psycopg.connect(conninfo, row_factory=dict_row, connect_timeout=10)


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def check_dead_letters(conn) -> dict[str, Any]:
    """Open dead-letters, grouped by structured category and free-text reason."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM import_dead_letters
            WHERE resolution_status = 'open'
            GROUP BY category
            ORDER BY count DESC
            """
        )
        by_category = [
            {"category": r["category"], "count": int(r["count"])} for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(reason, ''), '(none)') AS reason, COUNT(*) AS count
            FROM import_dead_letters
            WHERE resolution_status = 'open'
            GROUP BY 1
            ORDER BY count DESC
            LIMIT 25
            """
        )
        by_reason = [
            {"reason": r["reason"], "count": int(r["count"])} for r in cur.fetchall()
        ]

    total = sum(item["count"] for item in by_category)
    return {
        "total_open": total,
        "by_category": by_category,
        "by_reason": by_reason,
    }


def check_lemma_integrity(conn) -> dict[str, Any]:
    """Missing normalized forms, and annotations with no source attribution."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM lemmatizations
            WHERE norm IS NULL OR norm = ''
            """
        )
        missing_norm = int(cur.fetchone()["count"])

        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM lemmatizations
            WHERE annotation_run_id IS NULL
            """
        )
        unattributed_lemmas = int(cur.fetchone()["count"])

    return {
        "lemmatizations_missing_norm": missing_norm,
        "lemmatizations_without_attribution": unattributed_lemmas,
    }


# Buckets a tablet by its average completeness across the five pipeline stages.
_PIPELINE_BUCKETS = ("complete", "advanced", "partial", "empty")


def check_pipeline_distribution(conn) -> dict[str, Any]:
    """Distribution of tablets across completeness buckets (a snapshot)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH scored AS (
                SELECT (
                    COALESCE(physical_complete, 0)
                    + COALESCE(graphemic_complete, 0)
                    + COALESCE(reading_complete, 0)
                    + COALESCE(linguistic_complete, 0)
                    + COALESCE(semantic_complete, 0)
                ) / 5.0 AS avg_complete
                FROM pipeline_status
            )
            SELECT
                CASE
                    WHEN avg_complete >= 0.95 THEN 'complete'
                    WHEN avg_complete >= 0.50 THEN 'advanced'
                    WHEN avg_complete >  0.0  THEN 'partial'
                    ELSE 'empty'
                END AS bucket,
                COUNT(*) AS count
            FROM scored
            GROUP BY 1
            """
        )
        counts = {b: 0 for b in _PIPELINE_BUCKETS}
        for r in cur.fetchall():
            counts[r["bucket"]] = int(r["count"])

    total = sum(counts.values())
    shares = {
        b: (round(100.0 * counts[b] / total, 2) if total else 0.0)
        for b in _PIPELINE_BUCKETS
    }
    return {"total": total, "counts": counts, "shares_pct": shares}


# --------------------------------------------------------------------------- #
# History (previous report) loading + alert evaluation
# --------------------------------------------------------------------------- #

_REPORT_RE = re.compile(r"^integrity-\d{4}-\d{2}-\d{2}\.json$")


def load_previous_report(exclude: Path | None = None) -> dict[str, Any] | None:
    """Most recent prior report JSON, or None if this is the first run."""
    if not _REPORTS_DIR.exists():
        return None
    candidates = sorted(
        (p for p in _REPORTS_DIR.iterdir() if _REPORT_RE.match(p.name)),
        key=lambda p: p.name,
        reverse=True,
    )
    for path in candidates:
        if exclude is not None and path.resolve() == exclude.resolve():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def evaluate_alerts(
    current: dict[str, Any], previous: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Compare current checks to the previous run; return a list of alerts."""
    alerts: list[dict[str, Any]] = []

    # 1. Dead-letter increase.
    cur_dl = current["checks"]["dead_letters"]["total_open"]
    if previous is not None:
        prev_dl = (
            previous.get("checks", {}).get("dead_letters", {}).get("total_open")
        )
        if (
            _DEADLETTER_INCREASE_TRIGGERS_ALERT
            and isinstance(prev_dl, int)
            and cur_dl > prev_dl
        ):
            alerts.append(
                {
                    "check": "dead_letters",
                    "message": (
                        f"Open dead-letters rose from {prev_dl} to {cur_dl} "
                        f"(+{cur_dl - prev_dl})."
                    ),
                    "previous": prev_dl,
                    "current": cur_dl,
                }
            )

    # 3. Pipeline distribution drift (any bucket share moved > threshold pp).
    if previous is not None:
        cur_shares = current["checks"]["pipeline_distribution"]["shares_pct"]
        prev_shares = (
            previous.get("checks", {})
            .get("pipeline_distribution", {})
            .get("shares_pct", {})
        )
        for bucket, cur_share in cur_shares.items():
            prev_share = prev_shares.get(bucket)
            if prev_share is None:
                continue
            delta = round(cur_share - prev_share, 2)
            if abs(delta) > _PIPELINE_DRIFT_PP_THRESHOLD:
                alerts.append(
                    {
                        "check": "pipeline_distribution",
                        "message": (
                            f"Pipeline bucket '{bucket}' share moved "
                            f"{prev_share}% -> {cur_share}% "
                            f"({'+' if delta >= 0 else ''}{delta}pp)."
                        ),
                        "bucket": bucket,
                        "previous_pct": prev_share,
                        "current_pct": cur_share,
                        "delta_pp": delta,
                    }
                )

    return alerts


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def build_report(conn) -> dict[str, Any]:
    """Run all checks and assemble the report body (no alerts yet)."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
        "checks": {
            "dead_letters": check_dead_letters(conn),
            "lemma_integrity": check_lemma_integrity(conn),
            "pipeline_distribution": check_pipeline_distribution(conn),
        },
    }


def print_summary(report: dict[str, Any], alerts: list[dict[str, Any]]) -> None:
    dl = report["checks"]["dead_letters"]
    li = report["checks"]["lemma_integrity"]
    pd = report["checks"]["pipeline_distribution"]

    print("=" * 64)
    print("Glintstone data-integrity audit")
    print(f"Generated: {report['generated_at']}")
    print("=" * 64)

    print("\n[1] Dead-letters (open)")
    print(f"    total open: {dl['total_open']}")
    for item in dl["by_category"]:
        print(f"      {item['category'] or '(uncategorized)':<20} {item['count']}")

    print("\n[2] Lemma integrity")
    print(f"    missing normalized form (norm): {li['lemmatizations_missing_norm']}")
    print(
        f"    no source attribution (run_id NULL): "
        f"{li['lemmatizations_without_attribution']}"
    )

    print("\n[3] Pipeline distribution")
    print(f"    tablets: {pd['total']}")
    for bucket in _PIPELINE_BUCKETS:
        print(
            f"      {bucket:<10} {pd['counts'][bucket]:>8}  "
            f"({pd['shares_pct'][bucket]}%)"
        )

    print("\n" + "-" * 64)
    if alerts:
        print(f"ALERTS: {len(alerts)} threshold(s) breached")
        for a in alerts:
            print(f"  ! [{a['check']}] {a['message']}")
    else:
        print("ALERTS: none — all checks within thresholds.")
    print("-" * 64)


def write_report(report: dict[str, Any]) -> Path:
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = _REPORTS_DIR / f"integrity-{date_str}.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return out_path


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Glintstone weekly integrity audit.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run checks and print, but do not write a report file.",
    )
    args = parser.parse_args(argv)

    conninfo = resolve_database_url()
    if not conninfo:
        print(
            "data_integrity_audit: no DATABASE_URL resolved "
            "(env / ~/.claude/state/glintstone.env / core.config). "
            "Nothing to audit.",
            file=sys.stderr,
        )
        # No DB configured is an operational non-event, not an integrity alert.
        return 0

    try:
        conn = _connect(conninfo)
    except Exception as exc:  # connection failure is operational, not an alert
        print(
            f"data_integrity_audit: could not connect to database: {exc}",
            file=sys.stderr,
        )
        return 0

    try:
        report = build_report(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    previous = load_previous_report()
    alerts = evaluate_alerts(report, previous)
    report["alerts"] = alerts
    report["compared_against"] = (
        previous.get("generated_at") if previous else None
    )

    if not args.dry_run:
        out_path = write_report(report)
        print(f"Report written: {out_path}")
    else:
        print("[dry-run] report not written.")

    print_summary(report, alerts)

    return 1 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
