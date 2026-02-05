#!/usr/bin/env python3
"""
Full data import for Glintstone - imports all available ORACC and CDLI data.
Includes checkpoints for verification.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib
import sys

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DB_PATH = BASE_DIR / "app" / "glintstone.db"
SCHEMA_PATH = BASE_DIR / "app" / "sql" / "schema.sql"

# Track statistics
STATS = {
    'glossary_entries': 0,
    'glossary_forms': 0,
    'corpus_texts': 0,
    'lemmas': 0,
    'artifacts': 0,
    'inscriptions': 0,
}

CHECKPOINTS = []

def checkpoint(name, expected=None, actual=None):
    """Record a verification checkpoint."""
    status = "✓" if expected is None or expected == actual else "⚠"
    msg = f"{status} {name}"
    if expected is not None:
        msg += f": {actual}/{expected}"
    elif actual is not None:
        msg += f": {actual}"
    CHECKPOINTS.append(msg)
    print(msg)

def create_database():
    """Create database with extended schema."""
    print("=" * 60)
    print("CREATING DATABASE")
    print("=" * 60)

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"  Removed existing database")

    conn = sqlite3.connect(DB_PATH)

    # Apply base schema
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
    conn.executescript(schema)

    # Add extended tables for corpus data
    conn.executescript('''
        -- Lemmatization data from corpus
        CREATE TABLE IF NOT EXISTS lemmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            p_number TEXT NOT NULL,
            line_no INTEGER,
            word_no INTEGER,
            form TEXT,
            cf TEXT,
            gw TEXT,
            pos TEXT,
            epos TEXT,
            lang TEXT,
            FOREIGN KEY (p_number) REFERENCES artifacts(p_number)
        );

        CREATE INDEX IF NOT EXISTS idx_lemmas_p_number ON lemmas(p_number);
        CREATE INDEX IF NOT EXISTS idx_lemmas_cf ON lemmas(cf);
        CREATE INDEX IF NOT EXISTS idx_lemmas_form ON lemmas(form);

        -- Track import sources
        CREATE TABLE IF NOT EXISTS import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            file_path TEXT,
            records_imported INTEGER,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    conn.commit()
    print(f"  ✓ Database created at {DB_PATH}")
    return conn

def import_all_glossaries(conn):
    """Import all glossary files from all ORACC projects."""
    print("\n" + "=" * 60)
    print("IMPORTING GLOSSARIES")
    print("=" * 60)

    # Find all glossary files
    glossary_files = []
    for gloss_file in BASE_DIR.glob("ORACC/**/gloss-*.json"):
        # Skip duplicates (prefer extracted over json folder)
        if "/json/" in str(gloss_file) and "/extracted/" in str(gloss_file).replace("/json/", "/extracted/"):
            continue
        size = gloss_file.stat().st_size
        if size > 1000:  # Skip empty files
            glossary_files.append((gloss_file, size))

    # Sort by size descending
    glossary_files.sort(key=lambda x: x[1], reverse=True)

    print(f"  Found {len(glossary_files)} glossary files")

    cursor = conn.cursor()
    total_entries = 0
    total_forms = 0

    # Track unique entries to avoid duplicates across projects
    seen_entries = set()

    for gloss_path, size in glossary_files:
        project = gloss_path.parts[-4] if "json" in gloss_path.parts else gloss_path.parts[-3]
        filename = gloss_path.name
        lang = filename.replace("gloss-", "").replace(".json", "")

        try:
            with open(gloss_path, 'r') as f:
                data = json.load(f)

            entries = data.get('entries', [])
            file_entries = 0
            file_forms = 0

            for entry in entries:
                entry_id = entry.get('id') or entry.get('oid')
                if not entry_id or entry_id in seen_entries:
                    continue
                seen_entries.add(entry_id)

                cursor.execute('''
                    INSERT OR IGNORE INTO glossary_entries
                    (entry_id, headword, citation_form, guide_word, language, pos, icount, project)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry_id,
                    entry.get('headword'),
                    entry.get('cf'),
                    entry.get('gw'),
                    lang,
                    entry.get('pos'),
                    int(entry.get('icount', 0)) if entry.get('icount') else 0,
                    project
                ))

                if cursor.rowcount > 0:
                    file_entries += 1
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
                            file_forms += 1
                            total_forms += 1

            if file_entries > 0:
                print(f"    {project}/{filename}: {file_entries:,} entries, {file_forms:,} forms")
                cursor.execute('''
                    INSERT INTO import_log (source, file_path, records_imported)
                    VALUES (?, ?, ?)
                ''', ('glossary', str(gloss_path), file_entries))

        except Exception as e:
            print(f"    ⚠ Error processing {gloss_path}: {e}")

    conn.commit()
    STATS['glossary_entries'] = total_entries
    STATS['glossary_forms'] = total_forms
    checkpoint("Glossary entries imported", None, total_entries)
    checkpoint("Glossary forms imported", None, total_forms)
    print(f"\n  ✓ Total: {total_entries:,} entries, {total_forms:,} forms")

def import_dcclt_catalogue(conn):
    """Import DCCLT catalogue with artifact metadata."""
    print("\n" + "=" * 60)
    print("IMPORTING DCCLT CATALOGUE")
    print("=" * 60)

    catalogue_path = BASE_DIR / "ORACC/dcclt/extracted/dcclt/catalogue.json"

    with open(catalogue_path, 'r') as f:
        data = json.load(f)

    members = data.get('members', {})
    print(f"  Found {len(members):,} catalogue entries")

    cursor = conn.cursor()
    imported = 0

    for text_id, meta in members.items():
        # Extract P-number
        p_number = meta.get('id_text') or text_id
        if not p_number.startswith('P'):
            p_number = f"P{p_number}" if p_number.isdigit() else text_id

        cursor.execute('''
            INSERT OR REPLACE INTO artifacts
            (p_number, designation, museum_no, excavation_no, period, provenience, genre, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p_number,
            meta.get('designation') or meta.get('title'),
            meta.get('museum_no'),
            meta.get('excavation_no'),
            meta.get('period'),
            meta.get('provenience'),
            meta.get('genre'),
            meta.get('language')
        ))
        imported += 1

    conn.commit()
    STATS['artifacts'] += imported
    checkpoint("DCCLT catalogue entries", len(members), imported)
    print(f"  ✓ Imported {imported:,} artifacts")

def import_cdli_catalogue(conn):
    """Import CDLI catalogue batch."""
    print("\n" + "=" * 60)
    print("IMPORTING CDLI CATALOGUE")
    print("=" * 60)

    catalog_path = BASE_DIR / "CDLI/catalogue/batch-00000.json"

    with open(catalog_path, 'r') as f:
        data = json.load(f)

    tablets = data.get('data', [])
    print(f"  Found {len(tablets)} CDLI tablets")

    cursor = conn.cursor()
    imported = 0
    inscriptions = 0

    for tablet in tablets:
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

        # Insert artifact (update if exists from DCCLT)
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
        imported += 1

        # Insert inscription if exists
        inscription = tablet.get('inscription', {})
        if inscription and inscription.get('atf'):
            cursor.execute('''
                INSERT OR REPLACE INTO inscriptions (p_number, atf, is_latest)
                VALUES (?, ?, 1)
            ''', (p_number, inscription.get('atf')))
            inscriptions += 1

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

    conn.commit()
    STATS['artifacts'] += imported
    STATS['inscriptions'] += inscriptions
    checkpoint("CDLI tablets", len(tablets), imported)
    checkpoint("CDLI inscriptions", None, inscriptions)
    print(f"  ✓ Imported {imported} tablets, {inscriptions} inscriptions")

def import_corpus_texts(conn):
    """Import DCCLT corpus texts with lemmatization."""
    print("\n" + "=" * 60)
    print("IMPORTING CORPUS TEXTS (with lemmatization)")
    print("=" * 60)

    corpus_dir = BASE_DIR / "ORACC/dcclt/extracted/dcclt/corpusjson"
    corpus_files = list(corpus_dir.glob("P*.json"))

    print(f"  Found {len(corpus_files):,} corpus files")

    cursor = conn.cursor()
    texts_imported = 0
    lemmas_imported = 0

    # Process in batches for progress reporting
    batch_size = 500

    for i, corpus_file in enumerate(corpus_files):
        if i > 0 and i % batch_size == 0:
            conn.commit()
            print(f"    Progress: {i:,}/{len(corpus_files):,} ({i*100//len(corpus_files)}%)")

        try:
            with open(corpus_file, 'r') as f:
                data = json.load(f)

            text_id = data.get('textid', corpus_file.stem)
            p_number = text_id if text_id.startswith('P') else f"P{text_id}"

            # Extract lemmas from CDL structure
            lemmas = extract_lemmas(data.get('cdl', []), p_number)

            for lemma in lemmas:
                cursor.execute('''
                    INSERT INTO lemmas (p_number, line_no, word_no, form, cf, gw, pos, epos, lang)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', lemma)
                lemmas_imported += 1

            texts_imported += 1

            # Update pipeline status
            if lemmas:
                cursor.execute('''
                    INSERT OR REPLACE INTO pipeline_status
                    (p_number, has_lemmas, lemma_coverage)
                    VALUES (?, 1, 1.0)
                ''', (p_number,))

        except Exception as e:
            if i < 5:  # Only print first few errors
                print(f"    ⚠ Error processing {corpus_file.name}: {e}")

    conn.commit()
    STATS['corpus_texts'] = texts_imported
    STATS['lemmas'] = lemmas_imported
    checkpoint("Corpus texts processed", len(corpus_files), texts_imported)
    checkpoint("Lemmas extracted", None, lemmas_imported)
    print(f"\n  ✓ Processed {texts_imported:,} texts, {lemmas_imported:,} lemmas")

def extract_lemmas(cdl_list, p_number, line_no=0, word_no=0):
    """Recursively extract lemmas from CDL structure."""
    lemmas = []

    for item in cdl_list:
        if isinstance(item, dict):
            node_type = item.get('node')

            if node_type == 'l':  # Lemma node
                f_data = item.get('f', {})
                lemmas.append((
                    p_number,
                    line_no,
                    word_no,
                    f_data.get('form'),
                    f_data.get('cf'),
                    f_data.get('gw'),
                    f_data.get('pos'),
                    f_data.get('epos'),
                    f_data.get('lang')
                ))
                word_no += 1

            elif node_type == 'c':  # Line/chunk
                label = item.get('label', '')
                if label:
                    try:
                        line_no = int(label.split('.')[0].replace("'", ""))
                    except:
                        pass

            # Recurse into nested cdl
            if 'cdl' in item:
                nested = extract_lemmas(item['cdl'], p_number, line_no, word_no)
                lemmas.extend(nested)
                word_no += len(nested)

    return lemmas

def import_ogsl_signs(conn):
    """Import OGSL sign list."""
    print("\n" + "=" * 60)
    print("IMPORTING OGSL SIGN LIST")
    print("=" * 60)

    ogsl_path = BASE_DIR / "ORACC/ogsl/json/ogsl/ogsl-sl.json"

    with open(ogsl_path, 'r') as f:
        data = json.load(f)

    signs = data.get('signs', {})
    print(f"  Found {len(signs):,} signs")

    cursor = conn.cursor()
    sign_count = 0
    value_count = 0

    for sign_id, sign_data in signs.items():
        utf8 = sign_data.get('utf8')
        hex_code = sign_data.get('hex')
        uphase = sign_data.get('uphase')
        uname = sign_data.get('uname')

        unicode_decimal = None
        if hex_code and '.' not in hex_code:
            try:
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
    checkpoint("Signs imported", len(signs), sign_count)
    checkpoint("Sign values imported", None, value_count)
    print(f"  ✓ Imported {sign_count:,} signs, {value_count:,} values")

def update_pipeline_status(conn):
    """Calculate pipeline status for all artifacts."""
    print("\n" + "=" * 60)
    print("UPDATING PIPELINE STATUS")
    print("=" * 60)

    cursor = conn.cursor()

    # Get all artifacts
    cursor.execute("SELECT p_number FROM artifacts")
    artifacts = [row[0] for row in cursor.fetchall()]

    print(f"  Updating status for {len(artifacts):,} artifacts")

    updated = 0
    for p_number in artifacts:
        # Check image
        image_path = BASE_DIR / f"CDLI/images/photo/{p_number}.jpg"
        has_image = 1 if image_path.exists() else 0

        # Check ATF
        cursor.execute("SELECT COUNT(*) FROM inscriptions WHERE p_number = ?", (p_number,))
        has_atf = 1 if cursor.fetchone()[0] > 0 else 0

        # Check lemmas
        cursor.execute("SELECT COUNT(*) FROM lemmas WHERE p_number = ?", (p_number,))
        lemma_count = cursor.fetchone()[0]
        has_lemmas = 1 if lemma_count > 0 else 0

        # Calculate quality score
        quality_score = (has_image * 20 + has_atf * 30 + has_lemmas * 30) / 100.0

        cursor.execute('''
            INSERT OR REPLACE INTO pipeline_status
            (p_number, has_image, has_atf, has_lemmas, quality_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (p_number, has_image, has_atf, has_lemmas, quality_score))
        updated += 1

    conn.commit()
    checkpoint("Pipeline status updated", len(artifacts), updated)
    print(f"  ✓ Updated {updated:,} artifacts")

def verify_and_report(conn):
    """Verify import and generate report."""
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)

    cursor = conn.cursor()

    # Count tables
    tables = [
        ('artifacts', 'Artifacts/Tablets'),
        ('inscriptions', 'Inscriptions (ATF)'),
        ('signs', 'OGSL Signs'),
        ('sign_values', 'Sign Values'),
        ('glossary_entries', 'Glossary Entries'),
        ('glossary_forms', 'Glossary Forms'),
        ('lemmas', 'Lemmas'),
        ('composites', 'Composite Texts'),
        ('pipeline_status', 'Pipeline Status'),
    ]

    print("\n  TABLE COUNTS:")
    for table, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"    {label}: {count:,}")

    # Database size
    db_size = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\n  DATABASE SIZE: {db_size:.1f} MB")

    # Checksum for verification
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    artifact_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM glossary_entries")
    glossary_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM lemmas")
    lemma_count = cursor.fetchone()[0]

    verification_string = f"{artifact_count}|{glossary_count}|{lemma_count}"
    checksum = hashlib.md5(verification_string.encode()).hexdigest()[:8]

    print(f"\n  VERIFICATION CHECKSUM: {checksum}")
    print(f"    (artifacts: {artifact_count:,} | glossary: {glossary_count:,} | lemmas: {lemma_count:,})")

    print("\n  CHECKPOINTS:")
    for cp in CHECKPOINTS:
        print(f"    {cp}")

    # Write verification report
    report_path = BASE_DIR / "app" / "import_report.json"
    report = {
        'imported_at': datetime.now().isoformat(),
        'database_size_mb': round(db_size, 2),
        'checksum': checksum,
        'counts': {table: cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table, _ in tables},
        'checkpoints': CHECKPOINTS,
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n  ✓ Report saved to {report_path}")

def main():
    print("=" * 60)
    print("GLINTSTONE FULL DATA IMPORT")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    conn = create_database()

    try:
        # Phase 1: Glossaries
        import_all_glossaries(conn)

        # Phase 2: Catalogues
        import_dcclt_catalogue(conn)
        import_cdli_catalogue(conn)

        # Phase 3: Signs
        import_ogsl_signs(conn)

        # Phase 4: Corpus texts with lemmas
        import_corpus_texts(conn)

        # Phase 5: Update pipeline status
        update_pipeline_status(conn)

        # Final verification
        verify_and_report(conn)

    finally:
        conn.close()

    print("\n" + "=" * 60)
    print(f"IMPORT COMPLETE: {datetime.now().isoformat()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
