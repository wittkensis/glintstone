#!/usr/bin/env python3
"""
Import CDLI ATF (transliteration) data into Glintstone database.

Features:
- Parses cdliatf_unblocked.atf file (3.5M+ lines, 135K+ tablets)
- Atomic batch transactions
- Checkpoint/resume from exact position
- Creates minimal artifact entries for P-numbers not in artifacts table
- Parses composite references (>>Q###### lines)

Usage:
    python import_cdli_atf.py [--reset]
"""

import json
import re
import signal
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DOWNLOADS_DIR = BASE_DIR / "downloads"
DB_PATH = BASE_DIR / "database" / "glintstone.db"
ATF_PATH = DOWNLOADS_DIR / "CDLI" / "metadata" / "cdliatf_unblocked.atf"
PROGRESS_DIR = BASE_DIR / "_progress"
CHECKPOINT_PATH = PROGRESS_DIR / "atf_import_state.json"

BATCH_SIZE = 2000


class ATFImporter:
    def __init__(self, reset: bool = False):
        self.conn = None
        self.interrupted = False
        self.reset = reset
        self.state = self._load_state() if not reset else self._fresh_state()
        self.stats = {
            'processed': 0,
            'inscriptions_inserted': 0,
            'inscriptions_updated': 0,
            'artifacts_created': 0,
            'composites_found': 0,
            'skipped': 0,
            'errors': [],
        }

        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        print("\n\n  Interrupt received. Saving checkpoint...")
        self.interrupted = True

    def _fresh_state(self) -> dict:
        return {
            'last_p_number': None,
            'tablets_processed': 0,
            'started_at': datetime.now().isoformat(),
            'completed': False,
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
        self.state['tablets_processed'] = self.stats['processed']
        self.state['completed'] = completed
        self.state['last_updated'] = datetime.now().isoformat()
        self.state['stats'] = {k: v for k, v in self.stats.items() if k != 'errors'}
        self.state['error_count'] = len(self.stats['errors'])

        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        temp = CHECKPOINT_PATH.with_suffix('.tmp')
        with open(temp, 'w') as f:
            json.dump(self.state, f, indent=2)
        temp.rename(CHECKPOINT_PATH)

    def _parse_atf_file(self, resume_after: str = None):
        """
        Parse CDLI ATF file into individual tablet records.
        Yields (p_number, atf_content, composites) tuples.
        """
        current_p = None
        current_lines = []
        current_composites = set()
        found_resume_point = resume_after is None

        with open(ATF_PATH, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                # New tablet starts with &Pxxxxxx
                if line.startswith('&P'):
                    # Yield previous tablet if exists
                    if current_p and current_lines and found_resume_point:
                        yield current_p, '\n'.join(current_lines), list(current_composites)

                    # Extract P-number
                    match = re.match(r'&(P\d+)', line)
                    if match:
                        current_p = match.group(1)
                        current_lines = [line.rstrip()]
                        current_composites = set()

                        # Check if we've passed the resume point
                        if not found_resume_point:
                            if current_p == resume_after:
                                found_resume_point = True
                                current_p = None  # Skip the resume point itself
                                current_lines = []
                    else:
                        current_p = None
                        current_lines = []
                        current_composites = set()

                elif current_p:
                    current_lines.append(line.rstrip())

                    # Extract composite references (>>Q###### format)
                    if line.startswith('>>Q'):
                        match = re.match(r'>>(Q\d+)', line)
                        if match:
                            current_composites.add(match.group(1))

            # Don't forget last tablet
            if current_p and current_lines and found_resume_point:
                yield current_p, '\n'.join(current_lines), list(current_composites)

    def _ensure_artifact_exists(self, cursor, p_number: str):
        """Create minimal artifact entry if it doesn't exist."""
        cursor.execute("SELECT 1 FROM artifacts WHERE p_number = ?", (p_number,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO artifacts (p_number, designation)
                VALUES (?, ?)
            ''', (p_number, f"ATF-only: {p_number}"))
            self.stats['artifacts_created'] += 1

    def _process_batch(self, batch: list):
        """Atomically process a batch of ATF records."""
        cursor = self.conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")

            for p_number, atf_content, composites in batch:
                # Ensure artifact exists
                self._ensure_artifact_exists(cursor, p_number)

                # Check for existing inscription
                existing = cursor.execute(
                    "SELECT id, atf FROM inscriptions WHERE p_number = ? AND source = 'cdli'",
                    (p_number,)
                ).fetchone()

                if existing:
                    if existing[1] != atf_content:
                        cursor.execute('''
                            UPDATE inscriptions SET atf = ?, is_latest = 1
                            WHERE p_number = ? AND source = 'cdli'
                        ''', (atf_content, p_number))
                        self.stats['inscriptions_updated'] += 1
                    else:
                        self.stats['skipped'] += 1
                else:
                    cursor.execute('''
                        INSERT INTO inscriptions (p_number, atf, source, is_latest)
                        VALUES (?, ?, 'cdli', 1)
                    ''', (p_number, atf_content))
                    self.stats['inscriptions_inserted'] += 1

                # Process composites
                for q_number in composites:
                    # Ensure composite exists
                    cursor.execute('''
                        INSERT OR IGNORE INTO composites (q_number, designation)
                        VALUES (?, ?)
                    ''', (q_number, f"Composite {q_number}"))

                    # Link artifact to composite
                    cursor.execute('''
                        INSERT OR IGNORE INTO artifact_composites (p_number, q_number)
                        VALUES (?, ?)
                    ''', (p_number, q_number))
                    self.stats['composites_found'] += 1

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise e

    def run(self):
        """Execute the ATF import."""
        print("=" * 70)
        print("CDLI ATF IMPORT")
        print("=" * 70)

        # Verify source file
        if not ATF_PATH.exists():
            print(f"  ERROR: ATF file not found at {ATF_PATH}")
            sys.exit(1)

        file_size = ATF_PATH.stat().st_size / (1024 * 1024)
        print(f"  Source: {ATF_PATH.name}")
        print(f"  Size: {file_size:.1f} MB")

        # Check if resuming
        resume_after = None
        if not self.reset and self.state.get('last_p_number'):
            if self.state.get('completed'):
                print("\n  Import already completed. Use --reset to reimport.")
                return True
            resume_after = self.state['last_p_number']
            print(f"\n  RESUMING after {resume_after}")
            self.stats = self.state.get('stats', self.stats)

        # Connect to database
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")

        # Ensure source column exists
        try:
            self.conn.execute('ALTER TABLE inscriptions ADD COLUMN source TEXT DEFAULT "cdli"')
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            print(f"\n  Parsing and importing ATF data (batch size: {BATCH_SIZE:,})...")

            batch = []
            last_p = None

            for p_number, atf_content, composites in self._parse_atf_file(resume_after):
                if self.interrupted:
                    break

                batch.append((p_number, atf_content, composites))
                last_p = p_number
                self.stats['processed'] += 1

                if len(batch) >= BATCH_SIZE:
                    self._process_batch(batch)
                    batch = []
                    self.state['last_p_number'] = last_p
                    self._save_state()
                    print(f"    Processed: {self.stats['processed']:,} tablets", end='\r')

            # Final batch
            if batch and not self.interrupted:
                self._process_batch(batch)
                self.state['last_p_number'] = last_p

            print()  # Newline after progress

            if not self.interrupted:
                self._update_pipeline_status()
                self._save_state(completed=True)
                print("\n  Import completed successfully!")
            else:
                self._save_state(completed=False)
                print(f"\n  Import interrupted at {self.stats['processed']:,} tablets")
                print("  Run again to resume from checkpoint.")

        finally:
            self.conn.close()

        self._print_summary()
        return not self.interrupted

    def _update_pipeline_status(self):
        """Update pipeline status for all tablets with ATF."""
        print("\n  Updating pipeline status...")
        cursor = self.conn.cursor()

        # Update has_atf for all inscriptions
        cursor.execute('''
            INSERT INTO pipeline_status (p_number, has_atf, atf_source)
            SELECT DISTINCT p_number, 1, 'cdli'
            FROM inscriptions
            WHERE atf IS NOT NULL AND atf != ''
            ON CONFLICT(p_number) DO UPDATE SET
                has_atf = 1,
                atf_source = 'cdli',
                last_updated = CURRENT_TIMESTAMP
        ''')

        # Recalculate quality scores
        cursor.execute('''
            UPDATE pipeline_status SET
                quality_score = (
                    COALESCE(has_image, 0) * 0.2 +
                    COALESCE(has_atf, 0) * 0.3 +
                    COALESCE(has_lemmas, 0) * 0.25 +
                    COALESCE(has_translation, 0) * 0.25
                ),
                last_updated = CURRENT_TIMESTAMP
        ''')

        self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM pipeline_status WHERE has_atf = 1")
        atf_count = cursor.fetchone()[0]
        print(f"    {atf_count:,} tablets now have ATF")

    def _print_summary(self):
        """Print import summary."""
        print("\n" + "=" * 70)
        print("ATF IMPORT SUMMARY")
        print("=" * 70)
        print(f"  Tablets processed:       {self.stats['processed']:,}")
        print(f"  Inscriptions inserted:   {self.stats['inscriptions_inserted']:,}")
        print(f"  Inscriptions updated:    {self.stats['inscriptions_updated']:,}")
        print(f"  Artifacts created:       {self.stats['artifacts_created']:,}")
        print(f"  Composite refs found:    {self.stats['composites_found']:,}")
        print(f"  Skipped (unchanged):     {self.stats['skipped']:,}")

        if self.stats['errors']:
            print(f"\n  Errors ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:5]:
                print(f"    {err}")

        # Verify counts
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inscriptions WHERE source = 'cdli'")
        ins_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM composites")
        comp_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM artifact_composites")
        link_count = cursor.fetchone()[0]
        conn.close()

        print(f"\n  Database totals:")
        print(f"    Inscriptions (cdli): {ins_count:,}")
        print(f"    Composites:          {comp_count:,}")
        print(f"    Artifact-composite:  {link_count:,}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import CDLI ATF data')
    parser.add_argument('--reset', action='store_true', help='Reset and start fresh')
    args = parser.parse_args()

    importer = ATFImporter(reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
