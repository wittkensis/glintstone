#!/usr/bin/env python3
"""
Extract translations from CDLI ATF file and update database.
Translations are marked with #tr.en: (or #tr.XX: for other languages)
"""

import sqlite3
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DOWNLOADS_DIR = BASE_DIR / "downloads"
DB_PATH = BASE_DIR / "database" / "glintstone.db"
ATF_PATH = DOWNLOADS_DIR / "CDLI/metadata/cdliatf_unblocked.atf"


def parse_translations(atf_path: Path):
    """
    Parse ATF file and extract translations for each tablet.
    Yields (p_number, translation_text, language) tuples.
    """
    current_p = None
    translations = defaultdict(list)  # {lang: [lines]}

    with open(atf_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            # New tablet
            if line.startswith('&P'):
                # Yield previous tablet's translations
                if current_p and translations:
                    for lang, lines in translations.items():
                        yield current_p, '\n'.join(lines), lang
                    translations = defaultdict(list)

                match = re.match(r'&(P\d+)', line)
                current_p = match.group(1) if match else None

            # Translation line: #tr.en: or #tr.de: etc.
            elif line.startswith('#tr.'):
                match = re.match(r'#tr\.(\w+):\s*(.+)', line.strip())
                if match:
                    lang = match.group(1)
                    text = match.group(2).strip()
                    translations[lang].append(text)

        # Don't forget last tablet
        if current_p and translations:
            for lang, lines in translations.items():
                yield current_p, '\n'.join(lines), lang


def import_translations():
    """Import all translations from CDLI ATF file."""
    print("=" * 60)
    print("IMPORTING TRANSLATIONS FROM CDLI ATF")
    print("=" * 60)
    print(f"  Source: {ATF_PATH}")

    if not ATF_PATH.exists():
        print(f"  ERROR: ATF file not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create translations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            p_number TEXT NOT NULL,
            translation TEXT,
            language TEXT DEFAULT 'en',
            source TEXT DEFAULT 'cdli',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(p_number, language, source)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_p ON translations(p_number)')

    tablets_with_trans = set()
    total_translations = 0
    lang_counts = defaultdict(int)

    print("\n  Parsing translations...")

    batch = []
    batch_size = 1000

    for p_number, translation, lang in parse_translations(ATF_PATH):
        tablets_with_trans.add(p_number)
        lang_counts[lang] += 1
        total_translations += 1

        batch.append((p_number, translation, lang))

        if len(batch) >= batch_size:
            insert_batch(cursor, batch)
            conn.commit()
            print(f"    Processed {total_translations:,} translations...", end='\r')
            batch = []

    # Process remaining
    if batch:
        insert_batch(cursor, batch)
        conn.commit()

    print(f"\n  ✓ Found translations for {len(tablets_with_trans):,} tablets")
    print(f"  ✓ Total translation segments: {total_translations:,}")
    print(f"  ✓ Languages: {dict(lang_counts)}")

    # Update pipeline_status
    print("\n  Updating pipeline status...")
    cursor.execute('''
        UPDATE pipeline_status SET
            has_translation = 1,
            quality_score = (
                COALESCE(has_image, 0) * 0.2 +
                COALESCE(has_atf, 0) * 0.3 +
                COALESCE(has_lemmas, 0) * 0.25 +
                1 * 0.25
            ),
            last_updated = CURRENT_TIMESTAMP
        WHERE p_number IN (SELECT DISTINCT p_number FROM translations)
    ''')

    # Also insert pipeline_status for tablets not yet tracked
    cursor.execute('''
        INSERT OR IGNORE INTO pipeline_status (p_number, has_translation)
        SELECT DISTINCT p_number, 1 FROM translations
        WHERE p_number NOT IN (SELECT p_number FROM pipeline_status)
    ''')

    trans_count = cursor.execute('''
        SELECT COUNT(*) FROM pipeline_status WHERE has_translation = 1
    ''').fetchone()[0]

    conn.commit()
    print(f"  ✓ Pipeline status updated: {trans_count:,} tablets have translations")

    conn.close()
    print("\n  Done!")


def insert_batch(cursor, batch):
    """Insert a batch of translations."""
    for p_number, translation, lang in batch:
        cursor.execute('''
            INSERT INTO translations (p_number, translation, language, source)
            VALUES (?, ?, ?, 'cdli')
            ON CONFLICT(p_number, language, source) DO UPDATE SET
                translation = excluded.translation
        ''', (p_number, translation, lang))


if __name__ == '__main__':
    import_translations()
