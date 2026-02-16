#!/usr/bin/env python3
"""
Verify image availability for tablets with sign annotations.

This script:
1. Finds all tablets with sign_annotations
2. Checks if CDLI has images (photo or lineart)
3. Updates pipeline_status.has_image accordingly
4. Reports orphan annotations (tablets not in artifacts table)
5. Optionally removes orphan annotations
"""

import sqlite3
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "glintstone.db"

# CDLI URLs
CDLI_PHOTO_URL = "https://cdli.ucla.edu/dl/photo/{}.jpg"
CDLI_LINEART_URL = "https://cdli.ucla.edu/dl/lineart/{}.jpg"

# Request timeout
TIMEOUT = 10


def check_cdli_image(p_number: str) -> dict:
    """Check if CDLI has photo or lineart for a tablet."""
    result = {
        'p_number': p_number,
        'has_photo': False,
        'has_lineart': False,
        'error': None
    }

    try:
        # Check photo
        photo_url = CDLI_PHOTO_URL.format(p_number)
        resp = requests.head(photo_url, timeout=TIMEOUT, allow_redirects=True)
        # CDLI returns 200 for existing images, redirects for missing
        if resp.status_code == 200 and 'image' in resp.headers.get('content-type', ''):
            result['has_photo'] = True

        # Check lineart
        lineart_url = CDLI_LINEART_URL.format(p_number)
        resp = requests.head(lineart_url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 200 and 'image' in resp.headers.get('content-type', ''):
            result['has_lineart'] = True

    except requests.RequestException as e:
        result['error'] = str(e)

    return result


def verify_annotation_images(clean_orphans: bool = False, update_db: bool = False):
    """Main verification function."""
    print("=" * 60)
    print("Sign Annotation Image Verification")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Find orphan annotations (tablets not in artifacts)
    print("\n1. Checking for orphan annotations...")
    cursor.execute("""
        SELECT sa.p_number, COUNT(*) as count
        FROM sign_annotations sa
        LEFT JOIN artifacts a ON sa.p_number = a.p_number
        WHERE a.p_number IS NULL
        GROUP BY sa.p_number
    """)
    orphans = cursor.fetchall()

    if orphans:
        print(f"   Found {len(orphans)} orphan P-numbers:")
        total_orphan_annotations = 0
        for p_number, count in orphans:
            print(f"   - {p_number}: {count} annotations")
            total_orphan_annotations += count
        print(f"   Total orphan annotations: {total_orphan_annotations}")

        if clean_orphans:
            print("\n   Removing orphan annotations...")
            for p_number, _ in orphans:
                cursor.execute("DELETE FROM sign_annotations WHERE p_number = ?", (p_number,))
            conn.commit()
            print(f"   Removed {total_orphan_annotations} orphan annotations")
    else:
        print("   No orphan annotations found")

    # Step 2: Get tablets with annotations that need image verification
    print("\n2. Finding tablets with annotations but no verified image...")
    cursor.execute("""
        SELECT DISTINCT sa.p_number
        FROM sign_annotations sa
        JOIN artifacts a ON sa.p_number = a.p_number
        LEFT JOIN pipeline_status ps ON sa.p_number = ps.p_number
        WHERE ps.has_image = 0 OR ps.has_image IS NULL
    """)
    tablets_to_check = [row[0] for row in cursor.fetchall()]
    print(f"   Found {len(tablets_to_check)} tablets to verify")

    if not tablets_to_check:
        print("   All annotated tablets have verified images")
        conn.close()
        return

    # Step 3: Check CDLI for images
    print("\n3. Checking CDLI for images...")
    results = []

    # Use thread pool for parallel requests
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_p = {executor.submit(check_cdli_image, p): p for p in tablets_to_check}

        for i, future in enumerate(as_completed(future_to_p)):
            result = future.result()
            results.append(result)
            has_any = result['has_photo'] or result['has_lineart']
            status = "✓" if has_any else "✗"
            print(f"   [{i+1}/{len(tablets_to_check)}] {result['p_number']}: {status}")

            # Rate limiting
            time.sleep(0.2)

    # Step 4: Summarize results
    print("\n4. Results Summary:")
    has_image = [r for r in results if r['has_photo'] or r['has_lineart']]
    no_image = [r for r in results if not r['has_photo'] and not r['has_lineart'] and not r['error']]
    errors = [r for r in results if r['error']]

    print(f"   Image found: {len(has_image)}")
    print(f"   No image: {len(no_image)}")
    print(f"   Errors: {len(errors)}")

    if no_image:
        print("\n   Tablets with annotations but NO image on CDLI:")
        for r in no_image:
            cursor.execute("""
                SELECT COUNT(*) FROM sign_annotations WHERE p_number = ?
            """, (r['p_number'],))
            count = cursor.fetchone()[0]
            print(f"   - {r['p_number']}: {count} annotations")

    # Step 5: Update database
    if update_db and has_image:
        print("\n5. Updating pipeline_status.has_image...")
        for r in has_image:
            # First ensure row exists
            cursor.execute("""
                INSERT OR IGNORE INTO pipeline_status (p_number) VALUES (?)
            """, (r['p_number'],))
            # Then update
            cursor.execute("""
                UPDATE pipeline_status
                SET has_image = 1
                WHERE p_number = ?
            """, (r['p_number'],))
        conn.commit()
        print(f"   Updated {len(has_image)} tablets")

        # Update has_sign_annotations
        print("\n6. Refreshing has_sign_annotations...")
        cursor.execute("""
            UPDATE pipeline_status
            SET has_sign_annotations = CASE
                WHEN p_number IN (SELECT DISTINCT p_number FROM sign_annotations) THEN 1
                ELSE 0
            END
        """)
        conn.commit()
    else:
        print("\n   (Dry run - use --update to apply changes)")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify images for annotated tablets")
    parser.add_argument("--clean-orphans", action="store_true",
                       help="Remove annotations for tablets not in artifacts table")
    parser.add_argument("--update", action="store_true",
                       help="Update pipeline_status.has_image in database")

    args = parser.parse_args()
    verify_annotation_images(clean_orphans=args.clean_orphans, update_db=args.update)
