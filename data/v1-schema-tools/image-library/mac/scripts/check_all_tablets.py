#!/usr/bin/env python3
"""
Check ALL 389,715 tablets for image availability at CDLI.
Updates database with accurate status.
"""

import sqlite3
import urllib.request
import urllib.error
import ssl
import json
import time
import signal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_DIR = Path(__file__).parent.parent
DB_PATH = Path("/Volumes/Portable Storage/CUNEIFORM/database/glintstone.db")
CHECKPOINT_PATH = BASE_DIR / "progress" / "check_progress.json"
LOG_PATH = BASE_DIR / "logs" / "check_status.log"

CDLI_PHOTO_URL = "https://cdli.earth/dl/photo/{}.jpg"
CDLI_LINEART_URL = "https://cdli.earth/dl/lineart/{}.jpg"

MAX_WORKERS = 20
REQUEST_TIMEOUT = 10

# SSL context for CDLI
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

interrupted = False

def handle_interrupt(signum, frame):
    global interrupted
    print("\n\nInterrupt received. Saving checkpoint...")
    interrupted = True

signal.signal(signal.SIGINT, handle_interrupt)
signal.signal(signal.SIGTERM, handle_interrupt)

def check_image_exists(p_number):
    """Check if CDLI has an image for this P-number."""
    for url in [CDLI_PHOTO_URL.format(p_number), CDLI_LINEART_URL.format(p_number)]:
        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'Glintstone/1.0')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as response:
                content_type = response.headers.get('Content-Type', '')
                content_length = int(response.headers.get('Content-Length', 0))

                if 'image' in content_type and content_length > 1000:
                    return (p_number, True)
        except:
            continue

    return (p_number, False)

def main():
    print("=" * 60)
    print("CUNEIFORM IMAGE STATUS CHECKER")
    print("=" * 60)
    print()

    # Load checkpoint
    checkpoint = {}
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            checkpoint = json.load(f)

    start_index = checkpoint.get('last_checked_index', 0)

    # Get all tablets
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT p_number FROM artifacts ORDER BY p_number ASC')
    tablets = [row[0] for row in cursor.fetchall()]
    total = len(tablets)

    print(f"Total tablets: {total:,}")
    if start_index > 0:
        print(f"Resuming from tablet {start_index + 1:,}")
    print(f"Using {MAX_WORKERS} parallel workers")
    print()

    found = checkpoint.get('found_images', 0)
    checked = start_index
    start_time = time.time()

    # Process in batches
    batch_size = 1000
    for batch_start in range(start_index, total, batch_size):
        if interrupted:
            break

        batch = tablets[batch_start:batch_start + batch_size]
        updates = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(check_image_exists, p): p for p in batch}

            for future in as_completed(futures):
                if interrupted:
                    break

                p_number, has_image = future.result()
                updates.append((p_number, has_image))

                if has_image:
                    found += 1
                checked += 1

                # Progress
                if checked % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = checked / elapsed if elapsed > 0 else 0
                    eta = (total - checked) / rate if rate > 0 else 0

                    print(f"\rProgress: {checked:,}/{total:,} ({checked*100//total}%) - "
                          f"Found: {found:,} - Rate: {rate:.1f}/s - ETA: {eta/60:.1f}min",
                          end='', flush=True)

        # Update database
        for p_number, has_image in updates:
            cursor.execute('''
                UPDATE pipeline_status
                SET has_image = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE p_number = ?
            ''', (1 if has_image else 0, p_number))
        conn.commit()

        # Save checkpoint
        checkpoint = {
            'last_checked_index': checked,
            'found_images': found,
            'started_at': checkpoint.get('started_at', time.time()),
            'last_updated': time.time()
        }
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    conn.close()

    # Final report
    elapsed = time.time() - start_time
    print()
    print()
    print("=" * 60)
    if interrupted:
        print("INTERRUPTED - Checkpoint saved")
    else:
        print("COMPLETE")
    print("=" * 60)
    print(f"Checked: {checked:,} tablets")
    print(f"Found images: {found:,} ({found*100//checked if checked else 0}%)")
    print(f"Time: {elapsed/60:.1f} minutes")
    print("=" * 60)

    # Write log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("Image Status Check " + ("INTERRUPTED" if interrupted else "COMPLETE") + "\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total tablets checked: {checked:,}\n")
        f.write(f"Tablets with images found: {found:,} ({found*100//checked if checked else 0}%)\n")
        f.write(f"Time taken: {elapsed/60:.1f} minutes\n")
        f.write(f"Database updated: Yes\n")

if __name__ == "__main__":
    main()
