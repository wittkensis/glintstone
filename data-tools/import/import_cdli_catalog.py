#!/usr/bin/env python3
"""
Import complete CDLI catalog from CSV into Glintstone database.

Features:
- Atomic batch transactions (no partial commits on crash)
- Checkpoint/resume from exact row on interruption
- UPSERT logic to preserve existing data
- Elamite tablet tracking
- Comprehensive progress reporting

Usage:
    python import_cdli_catalog.py [--reset] [--verify-only]
"""

import csv
import hashlib
import json
import signal
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DB_PATH = BASE_DIR / "database" / "glintstone.db"
CSV_PATH = BASE_DIR / "downloads" / "CDLI" / "metadata" / "cdli_cat.csv"
PROGRESS_DIR = BASE_DIR / "_progress"
CHECKPOINT_PATH = PROGRESS_DIR / "csv_import_state.json"

BATCH_SIZE = 5000

# CSV to database field mapping
FIELD_MAP = {
    'id': 'p_number',
    'designation': 'designation',
    'museum_no': 'museum_no',
    'excavation_no': 'excavation_no',
    'findspot_square': 'findspot_square',
    'material': 'material',
    'object_type': 'object_type',
    'period': 'period',
    'provenience': 'provenience',
    'genre': 'genre',
    'language': 'language',
    'width': 'width',
    'height': 'height',
    'thickness': 'thickness',
}


class CDLICatalogImporter:
    def __init__(self, reset: bool = False):
        self.conn = None
        self.interrupted = False
        self.reset = reset
        self.state = self._load_state() if not reset else self._fresh_state()
        self.stats = {
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'skipped_no_id': 0,
            'elamite_count': 0,
            'errors': [],
        }

        # Handle graceful interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        print("\n\n  Interrupt received. Saving checkpoint...")
        self.interrupted = True

    def _fresh_state(self) -> dict:
        return {
            'last_row': 0,
            'csv_checksum': None,
            'started_at': datetime.now().isoformat(),
            'completed': False,
            'total_rows': 0,
        }

    def _load_state(self) -> dict:
        if CHECKPOINT_PATH.exists():
            try:
                with open(CHECKPOINT_PATH) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._fresh_state()

    def _save_state(self, completed: bool = False):
        """Atomically save checkpoint state."""
        self.state['last_row'] = self.stats['processed']
        self.state['completed'] = completed
        self.state['last_updated'] = datetime.now().isoformat()
        self.state['stats'] = self.stats.copy()
        self.state['stats']['errors'] = self.stats['errors'][-10:]  # Keep last 10 errors

        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        temp = CHECKPOINT_PATH.with_suffix('.tmp')
        with open(temp, 'w') as f:
            json.dump(self.state, f, indent=2)
        temp.rename(CHECKPOINT_PATH)

    def _compute_csv_checksum(self) -> str:
        """Quick checksum of first 10KB for file identity."""
        with open(CSV_PATH, 'rb') as f:
            return hashlib.sha256(f.read(10240)).hexdigest()[:16]

    def _count_csv_rows(self) -> int:
        """Count total rows in CSV (for progress reporting)."""
        with open(CSV_PATH, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for _ in f) - 1  # Minus header

    def _normalize_p_number(self, row_id: str) -> str:
        """Convert numeric ID to P-number format (P######)."""
        if not row_id or not row_id.strip():
            return None
        row_id = row_id.strip()
        try:
            return f"P{int(row_id):06d}"
        except ValueError:
            # Already formatted or invalid
            if row_id.startswith('P'):
                return row_id
            return None

    def _parse_numeric(self, value: str):
        """Safely parse numeric field."""
        if not value or not value.strip():
            return None
        try:
            return float(value.strip())
        except ValueError:
            return None

    def _is_elamite(self, language: str) -> bool:
        """Check if language contains Elamite."""
        if not language:
            return False
        return 'elamite' in language.lower()

    def _transform_row(self, row: dict) -> dict:
        """Transform CSV row to database record."""
        p_number = self._normalize_p_number(row.get('id', ''))
        if not p_number:
            return None

        return {
            'p_number': p_number,
            'designation': row.get('designation', '').strip() or None,
            'museum_no': row.get('museum_no', '').strip() or None,
            'excavation_no': row.get('excavation_no', '').strip() or None,
            'findspot_square': row.get('findspot_square', '').strip() or None,
            'material': row.get('material', '').strip() or None,
            'object_type': row.get('object_type', '').strip() or None,
            'period': row.get('period', '').strip() or None,
            'provenience': row.get('provenience', '').strip() or None,
            'genre': row.get('genre', '').strip() or None,
            'language': row.get('language', '').strip() or None,
            'width': self._parse_numeric(row.get('width', '')),
            'height': self._parse_numeric(row.get('height', '')),
            'thickness': self._parse_numeric(row.get('thickness', '')),
        }

    def _commit_batch(self, batch: list):
        """Atomically commit a batch of records using UPSERT."""
        cursor = self.conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")

            for record in batch:
                cursor.execute('''
                    INSERT INTO artifacts
                    (p_number, designation, museum_no, excavation_no, findspot_square,
                     material, object_type, period, provenience, genre, language,
                     width, height, thickness)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(p_number) DO UPDATE SET
                        designation = COALESCE(excluded.designation, designation),
                        museum_no = COALESCE(excluded.museum_no, museum_no),
                        excavation_no = COALESCE(excluded.excavation_no, excavation_no),
                        findspot_square = COALESCE(excluded.findspot_square, findspot_square),
                        material = COALESCE(excluded.material, material),
                        object_type = COALESCE(excluded.object_type, object_type),
                        period = COALESCE(excluded.period, period),
                        provenience = COALESCE(excluded.provenience, provenience),
                        genre = COALESCE(excluded.genre, genre),
                        language = COALESCE(excluded.language, language),
                        width = COALESCE(excluded.width, width),
                        height = COALESCE(excluded.height, height),
                        thickness = COALESCE(excluded.thickness, thickness)
                ''', (
                    record['p_number'], record['designation'], record['museum_no'],
                    record['excavation_no'], record['findspot_square'], record['material'],
                    record['object_type'], record['period'], record['provenience'],
                    record['genre'], record['language'], record['width'],
                    record['height'], record['thickness']
                ))

                # Track insert vs update
                if cursor.rowcount > 0:
                    self.stats['inserted'] += 1
                else:
                    self.stats['updated'] += 1

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def _run_migration(self):
        """Run schema migration if needed."""
        migration_path = BASE_DIR / "app" / "sql" / "migrations" / "add_elamite_tracking.sql"
        if migration_path.exists():
            print("  Running schema migration...")
            cursor = self.conn.cursor()
            with open(migration_path) as f:
                sql = f.read()
            # Execute each statement separately
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except sqlite3.OperationalError as e:
                        if 'already exists' not in str(e).lower():
                            print(f"    Warning: {e}")
            self.conn.commit()
            print("  Migration complete.")

    def _init_pipeline_status(self):
        """Initialize pipeline_status for all new artifacts."""
        print("\n  Initializing pipeline status...")
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO pipeline_status (p_number, has_image, has_atf, quality_score)
            SELECT p_number, 0, 0, 0.0
            FROM artifacts
            WHERE p_number NOT IN (SELECT p_number FROM pipeline_status)
        ''')
        self.conn.commit()
        print(f"    Added {cursor.rowcount:,} new pipeline status records")

    def run(self):
        """Execute the full import."""
        print("=" * 70)
        print("CDLI CATALOG IMPORT")
        print("=" * 70)

        # Verify source file
        if not CSV_PATH.exists():
            print(f"  ERROR: CSV file not found at {CSV_PATH}")
            sys.exit(1)

        # File info
        csv_checksum = self._compute_csv_checksum()
        file_size = CSV_PATH.stat().st_size / (1024 * 1024)
        print(f"  Source: {CSV_PATH.name}")
        print(f"  Size: {file_size:.1f} MB")
        print(f"  Checksum: {csv_checksum}")

        # Check if resuming
        resume_from = 0
        if not self.reset and self.state.get('csv_checksum') == csv_checksum:
            if self.state.get('completed'):
                print("\n  Import already completed. Use --reset to reimport.")
                return True
            resume_from = self.state.get('last_row', 0)
            if resume_from > 0:
                print(f"\n  RESUMING from row {resume_from:,}")
                self.stats = self.state.get('stats', self.stats)

        # Update state with file info
        self.state['csv_checksum'] = csv_checksum
        if not self.state.get('started_at'):
            self.state['started_at'] = datetime.now().isoformat()

        # Count total rows for progress
        if not self.state.get('total_rows'):
            print("  Counting rows...")
            self.state['total_rows'] = self._count_csv_rows()
        total_rows = self.state['total_rows']
        print(f"  Total records: {total_rows:,}")

        # Connect to database
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")  # 64MB cache

        try:
            # Run migration
            self._run_migration()

            # Import CSV
            print(f"\n  Importing artifacts (batch size: {BATCH_SIZE:,})...")
            self._import_csv(resume_from, total_rows)

            if not self.interrupted:
                # Initialize pipeline status
                self._init_pipeline_status()

                # Mark complete
                self._save_state(completed=True)
                print("\n  Import completed successfully!")
            else:
                self._save_state(completed=False)
                print(f"\n  Import interrupted at row {self.stats['processed']:,}")
                print("  Run again to resume from checkpoint.")

        finally:
            self.conn.close()

        self._print_summary()
        return not self.interrupted

    def _import_csv(self, resume_from: int, total_rows: int):
        """Import CSV with atomic batch transactions."""
        batch = []

        with open(CSV_PATH, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=1):
                if self.interrupted:
                    break

                if row_num <= resume_from:
                    continue

                try:
                    record = self._transform_row(row)
                    if record:
                        batch.append(record)
                        if self._is_elamite(record.get('language')):
                            self.stats['elamite_count'] += 1
                    else:
                        self.stats['skipped_no_id'] += 1

                except Exception as e:
                    self.stats['errors'].append({
                        'row': row_num,
                        'error': str(e),
                        'p_number': row.get('id', 'unknown'),
                    })

                # Commit batch atomically
                if len(batch) >= BATCH_SIZE:
                    self._commit_batch(batch)
                    batch = []
                    self.stats['processed'] = row_num
                    self._save_state()

                    # Progress update
                    pct = (row_num / total_rows) * 100
                    print(f"    Progress: {row_num:,} / {total_rows:,} ({pct:.1f}%)", end='\r')

            # Final batch
            if batch and not self.interrupted:
                self._commit_batch(batch)
                self.stats['processed'] = row_num

        print()  # Newline after progress

    def _print_summary(self):
        """Print import summary."""
        print("\n" + "=" * 70)
        print("IMPORT SUMMARY")
        print("=" * 70)
        print(f"  Total processed:  {self.stats['processed']:,}")
        print(f"  Inserted:         {self.stats['inserted']:,}")
        print(f"  Updated:          {self.stats['updated']:,}")
        print(f"  Skipped (no ID):  {self.stats['skipped_no_id']:,}")
        print(f"  Elamite tablets:  {self.stats['elamite_count']:,}")

        if self.stats['errors']:
            print(f"\n  Errors ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:5]:
                print(f"    Row {err['row']}: {err['error']}")
            if len(self.stats['errors']) > 5:
                print(f"    ... and {len(self.stats['errors']) - 5} more")

        # Verify counts
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM artifacts")
        db_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE LOWER(language) LIKE '%elamite%'")
        elamite_db = cursor.fetchone()[0]
        conn.close()

        print(f"\n  Database totals:")
        print(f"    Artifacts: {db_count:,}")
        print(f"    Elamite:   {elamite_db:,}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import CDLI catalog from CSV')
    parser.add_argument('--reset', action='store_true', help='Reset and start fresh')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing import')
    args = parser.parse_args()

    if args.verify_only:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM artifacts")
        print(f"Artifacts in database: {cursor.fetchone()[0]:,}")
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE LOWER(language) LIKE '%elamite%'")
        print(f"Elamite tablets: {cursor.fetchone()[0]:,}")
        conn.close()
        return

    importer = CDLICatalogImporter(reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
