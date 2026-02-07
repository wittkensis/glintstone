#!/usr/bin/env python3
"""
Batch update image availability status by checking CDLI.
Uses HEAD requests for efficiency - doesn't download actual images.
"""

import sqlite3
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

# Create SSL context that doesn't verify certificates (needed for cdli.earth)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DB_PATH = BASE_DIR / "database" / "glintstone.db"

# CDLI redirects to cdli.earth - use the final URL directly
CDLI_PHOTO_URL = "https://cdli.earth/dl/photo/{}.jpg"
CDLI_LINEART_URL = "https://cdli.earth/dl/lineart/{}.jpg"

# Rate limiting
MAX_WORKERS = 20
BATCH_SIZE = 1000
REQUEST_TIMEOUT = 10


def check_image_exists(p_number: str) -> tuple[str, bool]:
    """Check if CDLI has an image for this P-number using HEAD request."""
    urls_to_try = [
        CDLI_PHOTO_URL.format(p_number),
        CDLI_LINEART_URL.format(p_number),
    ]

    for url in urls_to_try:
        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'Glintstone/1.0 (Cuneiform Research Platform)')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as response:
                # Check if we got a real image (not a 404 page)
                content_type = response.headers.get('Content-Type', '')
                content_length = int(response.headers.get('Content-Length', 0))

                if 'image' in content_type and content_length > 1000:
                    return (p_number, True)

        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception):
            continue

    return (p_number, False)


def update_database(conn, updates: list[tuple[str, bool]]):
    """Batch update pipeline_status with image availability."""
    cursor = conn.cursor()

    for p_number, has_image in updates:
        cursor.execute('''
            UPDATE pipeline_status
            SET has_image = ?,
                quality_score = (
                    ? * 0.2 +
                    COALESCE(has_atf, 0) * 0.3 +
                    COALESCE(has_lemmas, 0) * 0.25 +
                    COALESCE(has_translation, 0) * 0.25
                ),
                last_updated = CURRENT_TIMESTAMP
            WHERE p_number = ?
        ''', (1 if has_image else 0, 1 if has_image else 0, p_number))

    conn.commit()


def main():
    print("=" * 60)
    print("UPDATING IMAGE AVAILABILITY STATUS")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all P-numbers that haven't been confirmed to have images
    cursor.execute('''
        SELECT p_number FROM pipeline_status
        WHERE has_image = 0 OR has_image IS NULL
        ORDER BY p_number
    ''')
    p_numbers = [row[0] for row in cursor.fetchall()]

    total = len(p_numbers)
    print(f"Checking {total:,} tablets for image availability...")
    print(f"Using {MAX_WORKERS} parallel workers\n")

    checked = 0
    found = 0
    start_time = time.time()

    # Process in batches
    for batch_start in range(0, total, BATCH_SIZE):
        batch = p_numbers[batch_start:batch_start + BATCH_SIZE]
        updates = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(check_image_exists, p): p for p in batch}

            for future in as_completed(futures):
                p_number, has_image = future.result()
                updates.append((p_number, has_image))

                if has_image:
                    found += 1
                checked += 1

        # Update database with batch results
        update_database(conn, updates)

        # Progress report
        elapsed = time.time() - start_time
        rate = checked / elapsed if elapsed > 0 else 0
        eta = (total - checked) / rate if rate > 0 else 0

        print(f"  Progress: {checked:,}/{total:,} ({checked*100//total}%) - "
              f"Found: {found:,} images - "
              f"Rate: {rate:.1f}/s - "
              f"ETA: {eta/60:.1f}min", flush=True)

    conn.close()

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"COMPLETE")
    print(f"  Checked: {checked:,} tablets")
    print(f"  Found images: {found:,} ({found*100//checked if checked else 0}%)")
    print(f"  Time: {elapsed/60:.1f} minutes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
