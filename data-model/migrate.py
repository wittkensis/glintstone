#!/usr/bin/env python3
"""Generic SQL migration runner for Glintstone.

Discovers `data-model/migrations/NNN_*.sql` files, applies them in order,
records each application in a `public._migrations` tracking table. Idempotent: only
applies migrations whose filename hash hasn't been seen before.

Usage:
    python data-model/migrate.py status    # show applied/pending
    python data-model/migrate.py up        # apply all pending
    python data-model/migrate.py up --to 019   # apply pending up to 019
    python data-model/migrate.py mark-applied 008  # mark as applied without running
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg  # noqa: E402

from core.config import get_settings  # noqa: E402

MIGRATIONS_DIR = ROOT / "data-model" / "migrations"
MIGRATION_PATTERN = re.compile(r"^(\d{3}[a-z]?)_(.+)\.sql$")

TRACKING_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS public._migrations (
    id BIGSERIAL PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applied_by TEXT NOT NULL,
    duration_ms INTEGER
);
"""


def conninfo() -> str:
    s = get_settings()
    return s.database_url or s.psycopg_conninfo()


def discover() -> list[tuple[str, str, Path]]:
    """Return (version, name, path) for every migration on disk, sorted."""
    out: list[tuple[str, str, Path]] = []
    for p in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = MIGRATION_PATTERN.match(p.name)
        if not m:
            continue
        out.append((m.group(1), m.group(2), p))
    return out


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def ensure_tracking(conn: psycopg.Connection) -> None:
    conn.execute(TRACKING_TABLE_DDL)
    conn.commit()


def applied_versions(conn: psycopg.Connection) -> dict[str, dict]:
    rows = conn.execute(
        "SELECT version, name, checksum, applied_at FROM public._migrations ORDER BY version"
    ).fetchall()
    return {r["version"]: dict(r) for r in rows}


def cmd_status() -> int:
    with psycopg.connect(conninfo(), row_factory=psycopg.rows.dict_row) as conn:
        ensure_tracking(conn)
        applied = applied_versions(conn)
    all_migrations = discover()
    print(f"Found {len(all_migrations)} migrations in {MIGRATIONS_DIR}")
    print(f"Applied: {len(applied)}\n")
    for version, name, path in all_migrations:
        if version in applied:
            ts = applied[version]["applied_at"].strftime("%Y-%m-%d %H:%M")
            checksum_match = applied[version]["checksum"] == file_checksum(path)
            marker = "OK" if checksum_match else "CHANGED!"
            print(f"  [{marker}] {version}  {name}  (applied {ts})")
        else:
            print(f"  [    ] {version}  {name}  (pending)")
    return 0


def apply_migration(
    conn: psycopg.Connection,
    version: str,
    name: str,
    path: Path,
    mark_only: bool = False,
) -> None:
    started = datetime.now(timezone.utc)
    if not mark_only:
        sql = path.read_text()
        # Reset session state before each migration. pg_dump output (used as
        # migration 000) sets search_path to empty so its fully-qualified
        # `public.foo` references work; that setting persists into the next
        # migration on the same connection and breaks anything that uses
        # unqualified table names.
        conn.execute("SET search_path = public, pg_catalog")
        conn.execute(sql)
    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    conn.execute(
        """
        INSERT INTO public._migrations (version, name, checksum, applied_by, duration_ms)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (version, name, file_checksum(path), get_settings().app_env, duration_ms),
    )
    conn.commit()


def cmd_up(target: str | None = None) -> int:
    with psycopg.connect(conninfo(), row_factory=psycopg.rows.dict_row) as conn:
        ensure_tracking(conn)
        applied = applied_versions(conn)
        all_migrations = discover()
        pending = [(v, n, p) for v, n, p in all_migrations if v not in applied]
        if target:
            pending = [t for t in pending if t[0] <= target]
        if not pending:
            print("Nothing to apply.")
            return 0
        print(f"Applying {len(pending)} migration(s)...")
        for version, name, path in pending:
            print(f"  -> {version}  {name}")
            try:
                apply_migration(conn, version, name, path)
            except Exception as e:
                conn.rollback()
                print(f"     FAILED: {e}", file=sys.stderr)
                return 1
            print("     OK")
    return 0


def cmd_mark_applied(version: str) -> int:
    all_migrations = {v: (v, n, p) for v, n, p in discover()}
    if version not in all_migrations:
        print(f"Unknown migration: {version}", file=sys.stderr)
        return 1
    v, n, p = all_migrations[version]
    with psycopg.connect(conninfo(), row_factory=psycopg.rows.dict_row) as conn:
        ensure_tracking(conn)
        if version in applied_versions(conn):
            print(f"Already applied: {version}")
            return 0
        apply_migration(conn, v, n, p, mark_only=True)
        print(f"Marked as applied (without running): {version}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_up = sub.add_parser("up", help="apply pending migrations")
    p_up.add_argument(
        "--to", dest="target", help="apply up to this version (inclusive)"
    )
    p_mark = sub.add_parser("mark-applied", help="record migration without running it")
    p_mark.add_argument("version", help="e.g. 008 or 008a")
    args = parser.parse_args()

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "up":
        return cmd_up(args.target)
    if args.cmd == "mark-applied":
        return cmd_mark_applied(args.version)
    return 1


if __name__ == "__main__":
    sys.exit(main())
