#!/usr/bin/env python3
"""
Step 20: Import collections from v0.1 SQLite database.

Reads collections and collection_members from app-v0.1/database/glintstone.db
and populates the collections and collection_members tables in PostgreSQL.

PREREQUISITE: Copy collection cover images to the web app static directory:
    mkdir -p app/static/images/collections
    cp app-v0.1/public_html/assets/images/collections/*.jpg app/static/images/collections/

Idempotent: uses ON CONFLICT DO NOTHING for collections (by name),
and ON CONFLICT DO NOTHING for collection_members (by PK).
Safe to re-run.

Usage:
    python 20_import_collections.py [--dry-run]
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from psycopg.rows import dict_row

from core.config import get_settings

OLD_DB_PATH = Path(__file__).resolve().parents[2] / "app-v0.1/database/glintstone.db"


def main():
    parser = argparse.ArgumentParser(description="Import collections from v0.1 SQLite DB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without inserting")
    args = parser.parse_args()

    if not OLD_DB_PATH.exists():
        print(f"❌ Old database not found: {OLD_DB_PATH}")
        sys.exit(1)

    settings = get_settings()
    pg_dsn = f"host={settings.db_host} port={settings.db_port} dbname={settings.db_name} user={settings.db_user} password={settings.db_password}"

    # Connect to old SQLite DB
    sqlite_conn = sqlite3.connect(OLD_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Connect to new PostgreSQL DB
    pg_conn = psycopg.connect(pg_dsn, row_factory=dict_row)
    pg_cur = pg_conn.cursor()

    # Fetch collections from old DB
    sqlite_cur.execute("""
        SELECT collection_id, name, description, image_path, created_at, updated_at
        FROM collections
        ORDER BY collection_id
    """)
    collections = sqlite_cur.fetchall()

    print(f"📦 Found {len(collections)} collections in old database")

    # Fetch collection members from old DB
    sqlite_cur.execute("""
        SELECT collection_id, p_number, added_at
        FROM collection_members
        ORDER BY collection_id, p_number
    """)
    members = sqlite_cur.fetchall()

    print(f"📎 Found {len(members)} collection member associations")

    if args.dry_run:
        print("\n🔍 DRY RUN - Collections to import:")
        for coll in collections:
            member_count = sum(1 for m in members if m['collection_id'] == coll['collection_id'])
            print(f"  • [{coll['collection_id']}] {coll['name']} ({member_count} tablets)")
            if coll['image_path']:
                print(f"    Image: {coll['image_path']}")
        print("\n✅ Dry run complete - no changes made")
        return

    # Import collections
    print("\n📥 Importing collections...")
    inserted_collections = 0
    skipped_collections = 0

    # Create a mapping from old collection_id to new collection_id
    collection_id_map = {}

    for coll in collections:
        try:
            # First check if collection already exists
            pg_cur.execute("""
                SELECT collection_id FROM collections WHERE name = %s
            """, (coll['name'],))
            existing = pg_cur.fetchone()

            # Convert image path from /assets to /static
            image_path = coll['image_path']
            if image_path and image_path.startswith('/assets/'):
                image_path = image_path.replace('/assets/', '/static/')

            if existing:
                collection_id_map[coll['collection_id']] = existing['collection_id']
                skipped_collections += 1
                print(f"  ⊗ Skipped (exists): {coll['name']} (old_id={coll['collection_id']}, new_id={existing['collection_id']})")
            else:
                # Insert new collection
                pg_cur.execute("""
                    INSERT INTO collections (name, description, image_path, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING collection_id
                """, (
                    coll['name'],
                    coll['description'],
                    image_path,
                    coll['created_at'],
                    coll['updated_at']
                ))
                result = pg_cur.fetchone()
                new_id = result['collection_id']
                collection_id_map[coll['collection_id']] = new_id
                inserted_collections += 1
                print(f"  ✓ Inserted: {coll['name']} (old_id={coll['collection_id']}, new_id={new_id})")

        except Exception as e:
            print(f"  ❌ Error inserting collection '{coll['name']}': {e}")
            continue

    pg_conn.commit()
    print(f"\n✅ Collections: {inserted_collections} inserted, {skipped_collections} skipped")

    # Import collection members
    print("\n📥 Importing collection members...")
    inserted_members = 0
    skipped_members = 0
    error_members = 0
    missing_artifacts = []

    for member in members:
        old_coll_id = member['collection_id']

        # Skip if we don't have a mapping for this collection
        if old_coll_id not in collection_id_map:
            error_members += 1
            continue

        new_coll_id = collection_id_map[old_coll_id]
        p_number = member['p_number']

        try:
            # First check if the artifact exists
            pg_cur.execute("SELECT 1 FROM artifacts WHERE p_number = %s", (p_number,))
            if not pg_cur.fetchone():
                missing_artifacts.append(p_number)
                error_members += 1
                continue

            pg_cur.execute("""
                INSERT INTO collection_members (collection_id, p_number)
                VALUES (%s, %s)
                ON CONFLICT (collection_id, p_number) DO NOTHING
            """, (new_coll_id, p_number))

            if pg_cur.rowcount > 0:
                inserted_members += 1
            else:
                skipped_members += 1

        except Exception as e:
            print(f"  ❌ Error inserting member {p_number} to collection {new_coll_id}: {e}")
            error_members += 1
            continue

    pg_conn.commit()

    if missing_artifacts:
        print(f"\n⚠️  Skipped {len(missing_artifacts)} artifacts not found in database:")
        for p_num in missing_artifacts:
            print(f"  • {p_num}")
    print(f"✅ Members: {inserted_members} inserted, {skipped_members} skipped, {error_members} errors")

    # Summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Collections imported: {inserted_collections}/{len(collections)}")
    print(f"Members imported: {inserted_members}/{len(members)}")
    print("="*60)

    # Verify by counting
    pg_cur.execute("SELECT COUNT(*) as count FROM collections")
    total_collections = pg_cur.fetchone()['count']

    pg_cur.execute("SELECT COUNT(*) as count FROM collection_members")
    total_members = pg_cur.fetchone()['count']

    print(f"\nDatabase now contains:")
    print(f"  • {total_collections} collections")
    print(f"  • {total_members} collection member associations")

    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    main()
