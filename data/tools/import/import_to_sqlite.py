#!/usr/bin/env python3
"""
Import cuneiform data into SQLite database for Glintstone local POC.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DOWNLOADS_DIR = BASE_DIR / "downloads"
DB_PATH = BASE_DIR / "database" / "glintstone.db"
SCHEMA_PATH = BASE_DIR / "app" / "sql" / "schema.sql"

def create_database():
    """Create database and apply schema."""
    print("Creating database...")
    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()

    conn.executescript(schema)
    conn.commit()
    print(f"  ✓ Database created at {DB_PATH}")
    return conn

def import_cdli_catalog(conn):
    """Import CDLI catalog data."""
    print("\nImporting CDLI catalog...")

    catalog_path = DOWNLOADS_DIR / "CDLI/catalogue/batch-00000.json"
    with open(catalog_path, 'r') as f:
        data = json.load(f)

    tablets = data.get('data', [])
    cursor = conn.cursor()

    for tablet in tablets:
        # Extract basic metadata
        p_number = f"P{tablet.get('id', ''):06d}"

        # Get first material if exists
        materials = tablet.get('materials', [])
        material = materials[0]['material']['material'] if materials else None

        # Get first language if exists
        languages = tablet.get('languages', [])
        language = languages[0]['language']['language'] if languages else None

        # Get first genre if exists
        genres = tablet.get('genres', [])
        genre = genres[0]['genre']['genre'] if genres else None

        # Insert artifact
        cursor.execute('''
            INSERT OR REPLACE INTO artifacts
            (p_number, designation, museum_no, excavation_no, findspot_square,
             material, width, height, thickness, language, genre)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p_number,
            tablet.get('designation'),
            tablet.get('museum_no'),
            tablet.get('excavation_no'),
            tablet.get('findspot_square'),
            material,
            float(tablet.get('width') or 0) if tablet.get('width') else None,
            float(tablet.get('height') or 0) if tablet.get('height') else None,
            float(tablet.get('thickness') or 0) if tablet.get('thickness') else None,
            language,
            genre
        ))

        # Insert inscription if exists
        inscription = tablet.get('inscription', {})
        if inscription and inscription.get('atf'):
            cursor.execute('''
                INSERT OR REPLACE INTO inscriptions (p_number, atf, is_latest)
                VALUES (?, ?, ?)
            ''', (
                p_number,
                inscription.get('atf'),
                1 if inscription.get('is_latest') else 0
            ))

        # Insert composites
        for comp in tablet.get('composites', []):
            q_number = comp.get('composite_no')
            composite_data = comp.get('composite', {})

            cursor.execute('''
                INSERT OR IGNORE INTO composites (q_number, designation)
                VALUES (?, ?)
            ''', (q_number, composite_data.get('designation')))

            cursor.execute('''
                INSERT OR IGNORE INTO artifact_composites (p_number, q_number)
                VALUES (?, ?)
            ''', (p_number, q_number))

        # Insert external resources
        for ext in tablet.get('external_resources', []):
            ext_res = ext.get('external_resource', {})
            cursor.execute('''
                INSERT INTO external_resources (p_number, resource_name, resource_key, base_url)
                VALUES (?, ?, ?, ?)
            ''', (
                p_number,
                ext_res.get('external_resource'),
                ext.get('external_resource_key'),
                ext_res.get('base_url')
            ))

        # Initialize pipeline status
        has_image = 1 if (BASE_DIR / f"CDLI/images/photo/{p_number}.jpg").exists() else 0
        has_atf = 1 if inscription and inscription.get('atf') else 0

        cursor.execute('''
            INSERT OR REPLACE INTO pipeline_status
            (p_number, has_image, has_atf, atf_source, quality_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            p_number,
            has_image,
            has_atf,
            'canonical' if has_atf else None,
            (has_image * 20 + has_atf * 30) / 100.0  # Basic quality score
        ))

    conn.commit()
    print(f"  ✓ Imported {len(tablets)} tablets")

def import_ogsl_signs(conn):
    """Import OGSL sign list."""
    print("\nImporting OGSL sign list...")

    ogsl_path = DOWNLOADS_DIR / "ORACC/ogsl/json/ogsl/ogsl-sl.json"
    with open(ogsl_path, 'r') as f:
        data = json.load(f)

    signs = data.get('signs', {})
    cursor = conn.cursor()

    sign_count = 0
    value_count = 0

    for sign_id, sign_data in signs.items():
        # Get Unicode info
        utf8 = sign_data.get('utf8')
        hex_code = sign_data.get('hex')
        uphase = sign_data.get('uphase')
        uname = sign_data.get('uname')

        # Convert hex to decimal
        unicode_decimal = None
        if hex_code:
            try:
                # Handle compound signs like "x12000.x12000"
                if '.' not in hex_code:
                    unicode_decimal = int(hex_code.replace('x', ''), 16)
            except:
                pass

        cursor.execute('''
            INSERT OR REPLACE INTO signs
            (sign_id, utf8, unicode_hex, unicode_decimal, uphase, uname)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sign_id, utf8, hex_code, unicode_decimal, uphase, uname))
        sign_count += 1

        # Insert values
        values = sign_data.get('values', [])
        for value in values:
            cursor.execute('''
                INSERT INTO sign_values (sign_id, value)
                VALUES (?, ?)
            ''', (sign_id, value))
            value_count += 1

    conn.commit()
    print(f"  ✓ Imported {sign_count} signs with {value_count} values")

def import_glossaries(conn):
    """Import DCCLT glossaries."""
    print("\nImporting glossaries...")

    gloss_dir = DOWNLOADS_DIR / "ORACC/dcclt/extracted/dcclt"
    cursor = conn.cursor()

    glossary_files = [
        ("gloss-sux.json", "sux"),
        ("gloss-akk.json", "akk"),
        ("gloss-akk-x-oldbab.json", "akk-x-oldbab"),
        ("gloss-akk-x-stdbab.json", "akk-x-stdbab"),
        ("gloss-qpn.json", "qpn"),
    ]

    total_entries = 0
    total_forms = 0

    for filename, language in glossary_files:
        gloss_path = gloss_dir / filename
        if not gloss_path.exists():
            print(f"  ⚠ Skipping {filename} (not found)")
            continue

        print(f"  Processing {filename}...")

        with open(gloss_path, 'r') as f:
            data = json.load(f)

        entries = data.get('entries', [])

        for entry in entries:
            entry_id = entry.get('id') or entry.get('oid')
            if not entry_id:
                continue

            cursor.execute('''
                INSERT OR REPLACE INTO glossary_entries
                (entry_id, headword, citation_form, guide_word, language, pos, icount, project)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                entry.get('headword'),
                entry.get('cf'),
                entry.get('gw'),
                language,
                entry.get('pos'),
                int(entry.get('icount', 0)) if entry.get('icount') else 0,
                'dcclt'
            ))
            total_entries += 1

            # Import forms
            forms = entry.get('forms', [])
            for form in forms:
                form_text = form.get('n')
                if form_text:
                    cursor.execute('''
                        INSERT INTO glossary_forms (entry_id, form, count)
                        VALUES (?, ?, ?)
                    ''', (
                        entry_id,
                        form_text,
                        int(form.get('icount', 0)) if form.get('icount') else 0
                    ))
                    total_forms += 1

    conn.commit()
    print(f"  ✓ Imported {total_entries} entries with {total_forms} forms")

def main():
    print("=" * 60)
    print("GLINTSTONE DATA IMPORT")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Create/connect to database
    conn = create_database()

    try:
        # Import data
        import_cdli_catalog(conn)
        import_ogsl_signs(conn)
        import_glossaries(conn)

        # Final stats
        print("\n" + "=" * 60)
        print("IMPORT COMPLETE")
        print("=" * 60)

        cursor = conn.cursor()

        stats = [
            ("Artifacts", "SELECT COUNT(*) FROM artifacts"),
            ("Inscriptions", "SELECT COUNT(*) FROM inscriptions"),
            ("Composites", "SELECT COUNT(*) FROM composites"),
            ("Signs", "SELECT COUNT(*) FROM signs"),
            ("Sign Values", "SELECT COUNT(*) FROM sign_values"),
            ("Glossary Entries", "SELECT COUNT(*) FROM glossary_entries"),
            ("Glossary Forms", "SELECT COUNT(*) FROM glossary_forms"),
        ]

        for name, query in stats:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"  {name}: {count:,}")

        # Database size
        db_size = DB_PATH.stat().st_size / (1024 * 1024)
        print(f"\n  Database size: {db_size:.1f} MB")

    finally:
        conn.close()

    print(f"\nCompleted: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
