#!/usr/bin/env python3
"""
Run migration 008: Unified Lexical Resource Architecture

Creates tables for the three-dimensional lexical model:
  - signs (Glyphs - graphemic dimension)
  - lemmas (Lemmas - lexemic dimension)
  - senses (Glosses - semantic dimension)
  - sign_lemma_associations (M:N join table)
  - lexical_tablet_occurrences (pre-computed associations)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

MIGRATION_FILE = Path(__file__).parent / "008_unified_lexical_resources.sql"


def run_migration():
    """Execute the migration SQL file"""
    settings = get_settings()

    # Read migration file
    with open(MIGRATION_FILE, "r") as f:
        migration_sql = f.read()

    # Connect and execute
    with psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    ) as conn:
        print("Running migration 008: Unified Lexical Resources...")

        conn.execute(migration_sql)
        conn.commit()

        print("✓ Migration complete")

        # Verify tables created
        tables = conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                  'lexical_signs',
                  'lexical_lemmas',
                  'lexical_senses',
                  'lexical_sign_lemma_associations',
                  'lexical_tablet_occurrences'
              )
            ORDER BY table_name
        """).fetchall()

        print(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Count indexes
        index_count = conn.execute("""
            SELECT COUNT(*) FROM pg_indexes
            WHERE tablename IN (
                'lexical_signs',
                'lexical_lemmas',
                'lexical_senses',
                'lexical_sign_lemma_associations',
                'lexical_tablet_occurrences'
            )
        """).fetchone()[0]

        print(f"\n✓ Created {index_count} indexes")


if __name__ == "__main__":
    run_migration()
