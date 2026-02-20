"""CLI migration runner.

Applies numbered SQL files from migrations/ in order.
Tracks applied migrations in a _migrations table.

Usage: python data-model/migrate.py
"""

import glob
import os
import sys
from pathlib import Path

# Add project root to path so core package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg
from psycopg.rows import dict_row

from core.config import get_settings


def run_migrations() -> None:
    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user} "
        f"password={settings.db_password}"
    )

    conn = psycopg.connect(conninfo, row_factory=dict_row)

    # Create tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()

    # Get already-applied migrations
    rows = conn.execute("SELECT filename FROM _migrations ORDER BY id").fetchall()
    applied = {row["filename"] for row in rows}

    # Find pending migrations
    migrations_dir = Path(__file__).parent / "migrations"
    files = sorted(glob.glob(str(migrations_dir / "*.sql")))
    pending = [f for f in files if os.path.basename(f) not in applied]

    if not pending:
        print("No pending migrations.")
        conn.close()
        return

    for filepath in pending:
        name = os.path.basename(filepath)
        print(f"Applying: {name}... ", end="", flush=True)

        sql = Path(filepath).read_text()

        try:
            conn.execute(sql)
            conn.execute(
                "INSERT INTO _migrations (filename) VALUES (%s)", (name,)
            )
            conn.commit()
            print("OK")
        except Exception as e:
            conn.rollback()
            print(f"FAILED: {e}")
            conn.close()
            sys.exit(1)

    print("Done.")
    conn.close()


if __name__ == "__main__":
    run_migrations()
