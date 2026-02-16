#!/usr/bin/env python3
"""
Verify CDLI import completeness and data integrity.

Checks:
1. Total artifact count matches CSV source
2. No NULL or malformed P-numbers
3. No duplicate P-numbers
4. Elamite tablet count >= expected
5. ATF inscription coverage
6. Pipeline status consistency

Usage:
    python verify_cdli_import.py [--verbose]
"""

import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DB_PATH = BASE_DIR / "database" / "glintstone.db"
CSV_PATH = BASE_DIR / "downloads" / "CDLI" / "metadata" / "cdli_cat.csv"
ATF_PATH = BASE_DIR / "downloads" / "CDLI" / "metadata" / "cdliatf_unblocked.atf"
PROGRESS_DIR = BASE_DIR / "_progress"
REPORT_PATH = PROGRESS_DIR / "import_verification.json"


def count_csv_rows() -> int:
    """Count data rows in CSV (excluding header)."""
    with open(CSV_PATH, 'r', encoding='utf-8', errors='replace') as f:
        return sum(1 for _ in f) - 1


def count_atf_tablets() -> int:
    """Count unique P-numbers in ATF file."""
    count = 0
    with open(ATF_PATH, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('&P'):
                count += 1
    return count


def count_csv_elamite() -> int:
    """Count Elamite records in CSV."""
    count = 0
    with open(CSV_PATH, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = row.get('language', '').lower()
            if 'elamite' in lang:
                count += 1
    return count


def verify_import(verbose: bool = False):
    """Run all verification checks."""
    print("=" * 70)
    print("CDLI IMPORT VERIFICATION")
    print("=" * 70)

    report = {
        'generated_at': datetime.now().isoformat(),
        'checks': [],
        'anomalies': [],
        'summary': {},
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # =========================================================================
    # Check 1: Total artifact count
    # =========================================================================
    print("\n  [1/6] Checking artifact count...")
    csv_count = count_csv_rows()
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    db_count = cursor.fetchone()[0]

    check1 = {
        'name': 'artifact_count',
        'description': 'Total artifacts match CSV source',
        'csv_count': csv_count,
        'db_count': db_count,
        'passed': db_count >= csv_count,
    }
    report['checks'].append(check1)
    status = "PASS" if check1['passed'] else "FAIL"
    print(f"        CSV: {csv_count:,} | DB: {db_count:,} [{status}]")

    # =========================================================================
    # Check 2: No NULL P-numbers
    # =========================================================================
    print("  [2/6] Checking for NULL P-numbers...")
    cursor.execute("SELECT COUNT(*) FROM artifacts WHERE p_number IS NULL OR p_number = ''")
    null_count = cursor.fetchone()[0]

    check2 = {
        'name': 'no_null_p_numbers',
        'description': 'No NULL or empty P-numbers',
        'null_count': null_count,
        'passed': null_count == 0,
    }
    report['checks'].append(check2)
    status = "PASS" if check2['passed'] else "FAIL"
    print(f"        NULL P-numbers: {null_count:,} [{status}]")

    # =========================================================================
    # Check 3: No duplicate P-numbers
    # =========================================================================
    print("  [3/6] Checking for duplicates...")
    cursor.execute('''
        SELECT p_number, COUNT(*) as cnt
        FROM artifacts
        GROUP BY p_number
        HAVING cnt > 1
        LIMIT 10
    ''')
    duplicates = cursor.fetchall()

    check3 = {
        'name': 'no_duplicates',
        'description': 'No duplicate P-numbers',
        'duplicate_count': len(duplicates),
        'passed': len(duplicates) == 0,
        'samples': [{'p_number': d[0], 'count': d[1]} for d in duplicates],
    }
    report['checks'].append(check3)
    status = "PASS" if check3['passed'] else "FAIL"
    print(f"        Duplicates: {len(duplicates):,} [{status}]")

    # =========================================================================
    # Check 4: Elamite count
    # =========================================================================
    print("  [4/6] Checking Elamite tablets...")
    csv_elamite = count_csv_elamite()
    cursor.execute("SELECT COUNT(*) FROM artifacts WHERE LOWER(language) LIKE '%elamite%'")
    db_elamite = cursor.fetchone()[0]

    check4 = {
        'name': 'elamite_count',
        'description': 'Elamite tablets imported correctly',
        'csv_count': csv_elamite,
        'db_count': db_elamite,
        'passed': db_elamite >= csv_elamite,
    }
    report['checks'].append(check4)
    status = "PASS" if check4['passed'] else "FAIL"
    print(f"        CSV: {csv_elamite:,} | DB: {db_elamite:,} [{status}]")

    # =========================================================================
    # Check 5: ATF inscriptions
    # =========================================================================
    print("  [5/6] Checking ATF inscriptions...")
    atf_count = count_atf_tablets()
    cursor.execute("SELECT COUNT(DISTINCT p_number) FROM inscriptions WHERE source = 'cdli'")
    db_inscriptions = cursor.fetchone()[0]

    check5 = {
        'name': 'atf_inscriptions',
        'description': 'ATF inscriptions imported',
        'atf_file_count': atf_count,
        'db_count': db_inscriptions,
        'coverage_pct': round((db_inscriptions / atf_count * 100) if atf_count > 0 else 0, 1),
        'passed': db_inscriptions >= atf_count * 0.99,  # Allow 1% tolerance
    }
    report['checks'].append(check5)
    status = "PASS" if check5['passed'] else "FAIL"
    print(f"        ATF file: {atf_count:,} | DB: {db_inscriptions:,} ({check5['coverage_pct']}%) [{status}]")

    # =========================================================================
    # Check 6: Pipeline status consistency
    # =========================================================================
    print("  [6/6] Checking pipeline status...")
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    total_artifacts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pipeline_status")
    pipeline_count = cursor.fetchone()[0]

    check6 = {
        'name': 'pipeline_status',
        'description': 'Pipeline status exists for all artifacts',
        'artifacts': total_artifacts,
        'pipeline_records': pipeline_count,
        'passed': pipeline_count >= total_artifacts,
    }
    report['checks'].append(check6)
    status = "PASS" if check6['passed'] else "FAIL"
    print(f"        Artifacts: {total_artifacts:,} | Pipeline: {pipeline_count:,} [{status}]")

    # =========================================================================
    # Summary statistics
    # =========================================================================
    print("\n  Gathering summary statistics...")

    # Language distribution
    cursor.execute('''
        SELECT language, COUNT(*) as cnt
        FROM artifacts
        WHERE language IS NOT NULL AND language != ''
        GROUP BY language
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    lang_dist = cursor.fetchall()
    report['summary']['language_distribution'] = [
        {'language': l[0], 'count': l[1]} for l in lang_dist
    ]

    # Period distribution
    cursor.execute('''
        SELECT period, COUNT(*) as cnt
        FROM artifacts
        WHERE period IS NOT NULL AND period != ''
        GROUP BY period
        ORDER BY cnt DESC
        LIMIT 15
    ''')
    period_dist = cursor.fetchall()
    report['summary']['period_distribution'] = [
        {'period': p[0], 'count': p[1]} for p in period_dist
    ]

    # Material distribution
    cursor.execute('''
        SELECT material, COUNT(*) as cnt
        FROM artifacts
        WHERE material IS NOT NULL AND material != ''
        GROUP BY material
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    mat_dist = cursor.fetchall()
    report['summary']['material_distribution'] = [
        {'material': m[0], 'count': m[1]} for m in mat_dist
    ]

    # Pipeline completeness
    cursor.execute('''
        SELECT
            SUM(CASE WHEN has_atf = 1 THEN 1 ELSE 0 END) as with_atf,
            SUM(CASE WHEN has_image = 1 THEN 1 ELSE 0 END) as with_image,
            SUM(CASE WHEN has_translation = 1 THEN 1 ELSE 0 END) as with_translation,
            AVG(quality_score) as avg_quality
        FROM pipeline_status
    ''')
    pipeline_stats = cursor.fetchone()
    report['summary']['pipeline'] = {
        'with_atf': pipeline_stats[0] or 0,
        'with_image': pipeline_stats[1] or 0,
        'with_translation': pipeline_stats[2] or 0,
        'avg_quality_score': round(pipeline_stats[3] or 0, 3),
    }

    conn.close()

    # =========================================================================
    # Overall result
    # =========================================================================
    all_passed = all(c.get('passed', True) for c in report['checks'])
    report['overall_status'] = 'PASSED' if all_passed else 'FAILED'
    report['checks_passed'] = sum(1 for c in report['checks'] if c.get('passed', True))
    report['checks_total'] = len(report['checks'])

    # Save report
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    # Print results
    print("\n" + "=" * 70)
    print("VERIFICATION RESULT")
    print("=" * 70)

    for check in report['checks']:
        status = "PASS" if check.get('passed') else "FAIL"
        print(f"  [{status}] {check['description']}")

    print(f"\n  Overall: {report['overall_status']}")
    print(f"  Checks: {report['checks_passed']}/{report['checks_total']} passed")
    print(f"\n  Report saved: {REPORT_PATH}")

    if verbose:
        print("\n  Top 10 Languages:")
        for item in report['summary']['language_distribution'][:10]:
            print(f"    {item['language']}: {item['count']:,}")

        print("\n  Top 10 Periods:")
        for item in report['summary']['period_distribution'][:10]:
            print(f"    {item['period']}: {item['count']:,}")

        print("\n  Pipeline Status:")
        ps = report['summary']['pipeline']
        print(f"    With ATF: {ps['with_atf']:,}")
        print(f"    With Image: {ps['with_image']:,}")
        print(f"    Avg Quality: {ps['avg_quality_score']:.1%}")

    return report['overall_status'] == 'PASSED'


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Verify CDLI import')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed statistics')
    args = parser.parse_args()

    success = verify_import(verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
