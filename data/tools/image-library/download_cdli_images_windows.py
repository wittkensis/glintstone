#!/usr/bin/env python3
"""
CDLI Image Downloader for Windows
==================================
Downloads tablet images from CDLI with resume capability and data validation.

Usage:
    python download_cdli_images_windows.py                    # Start/resume download
    python download_cdli_images_windows.py --batch 1000       # Limit batch size
    python download_cdli_images_windows.py --verify           # Verify existing downloads
    python download_cdli_images_windows.py --reset            # Start fresh

Requirements:
    pip install requests tqdm

The script expects p_numbers_with_images.txt in the same directory.
"""

import argparse
import hashlib
import json
import logging
import os
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install requests tqdm")
    sys.exit(1)

# =============================================================================
# Configuration - EDIT THESE PATHS FOR YOUR WINDOWS MACHINE
# =============================================================================

# Base directory - change to your Windows path (e.g., "D:\\CUNEIFORM" or "E:\\CUNEIFORM")
BASE_DIR = Path(__file__).parent.resolve()

# Download destination
IMAGES_DIR = BASE_DIR / "downloads" / "CDLI" / "images"

# P-numbers source file
P_NUMBERS_FILE = BASE_DIR / "p_numbers_with_images.txt"

# Progress tracking files
PROGRESS_FILE = BASE_DIR / "progress.json"
CHECKSUM_FILE = BASE_DIR / "checksums.json"
ERROR_LOG = BASE_DIR / "errors.log"

# CDLI endpoints (both photo and lineart versions)
CDLI_PHOTO_URL = "https://cdli.earth/dl/photo/{}.jpg"
CDLI_LINEART_URL = "https://cdli.earth/dl/lineart/{}.jpg"

# Download settings
RATE_LIMIT = 2.0           # Requests per second
MAX_WORKERS = 10           # Parallel download threads
RETRY_ATTEMPTS = 3         # Retries per failed download
RETRY_DELAY = 2            # Base delay between retries (seconds)
DEFAULT_BATCH_SIZE = 5000  # Images per session
REQUEST_TIMEOUT = 30       # Seconds per request
MIN_IMAGE_SIZE = 1024      # Minimum valid image size (bytes)

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ERROR_LOG, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# =============================================================================
# Progress & State Management
# =============================================================================

class ProgressTracker:
    """Manages download progress state for resume capability."""

    def __init__(self, progress_file: Path, checksum_file: Path):
        self.progress_file = progress_file
        self.checksum_file = checksum_file
        self.state = self._load_state()
        self.checksums = self._load_checksums()
        self._interrupted = False
        self._dirty = False

        # Handle graceful interruption (works on Windows with CTRL+C)
        signal.signal(signal.SIGINT, self._handle_interrupt)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        logger.warning("\n\nInterrupt received. Saving progress...")
        self._interrupted = True
        self.save()
        logger.info(f"Progress saved. {len(self.state.get('completed', []))} images recorded.")
        logger.info("Run script again to resume from where you left off.")
        sys.exit(0)

    def _load_state(self) -> dict:
        if self.progress_file.exists():
            try:
                with open(self.progress_file, encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Corrupted progress file, starting fresh")
        return {
            "started_at": datetime.now().isoformat(),
            "completed": [],
            "failed": [],
            "skipped": [],
        }

    def _load_checksums(self) -> dict:
        if self.checksum_file.exists():
            try:
                with open(self.checksum_file, encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Corrupted checksum file, starting fresh")
        return {}

    def save(self):
        """Atomically save progress state."""
        if not self._dirty:
            return

        self.state["last_updated"] = datetime.now().isoformat()
        self.state["total_completed"] = len(self.state.get("completed", []))
        self.state["total_failed"] = len(self.state.get("failed", []))

        # Write to temp file, then rename (atomic operation)
        temp_file = self.progress_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

        # On Windows, need to remove target first
        if self.progress_file.exists():
            self.progress_file.unlink()
        temp_file.rename(self.progress_file)

        # Save checksums
        temp_checksum = self.checksum_file.with_suffix(".tmp")
        with open(temp_checksum, "w", encoding="utf-8") as f:
            json.dump(self.checksums, f)
        if self.checksum_file.exists():
            self.checksum_file.unlink()
        temp_checksum.rename(self.checksum_file)

        self._dirty = False

    def mark_completed(self, p_number: str, checksum: str):
        """Record successful download."""
        if p_number not in self.state["completed"]:
            self.state["completed"].append(p_number)
        self.checksums[p_number] = checksum
        self._dirty = True

    def mark_failed(self, p_number: str, error: str):
        """Record failed download."""
        if p_number not in self.state["failed"]:
            self.state["failed"].append(p_number)
        self._dirty = True

    def mark_skipped(self, p_number: str, reason: str):
        """Record skipped download."""
        if p_number not in self.state["skipped"]:
            self.state["skipped"].append(p_number)
        self._dirty = True

    def is_completed(self, p_number: str) -> bool:
        """Check if P-number was already downloaded."""
        return p_number in self.state.get("completed", [])

    def get_checksum(self, p_number: str) -> Optional[str]:
        """Get recorded checksum for P-number."""
        return self.checksums.get(p_number)

    def reset(self):
        """Reset all progress."""
        self.state = {
            "started_at": datetime.now().isoformat(),
            "completed": [],
            "failed": [],
            "skipped": [],
        }
        self.checksums = {}
        self._dirty = True
        self.save()

    @property
    def interrupted(self) -> bool:
        return self._interrupted


# =============================================================================
# Image Validation
# =============================================================================

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_image(filepath: Path) -> tuple[bool, str]:
    """
    Validate downloaded file is a real JPEG image.

    Returns:
        (is_valid, reason)
    """
    if not filepath.exists():
        return False, "File does not exist"

    file_size = filepath.stat().st_size

    # Check minimum size (error pages are typically small)
    if file_size < MIN_IMAGE_SIZE:
        return False, f"File too small ({file_size} bytes)"

    # Check JPEG magic bytes
    try:
        with open(filepath, "rb") as f:
            magic = f.read(3)

        if magic != b'\xff\xd8\xff':
            # Check if it's HTML (error page)
            with open(filepath, "rb") as f:
                header = f.read(100)
            if b'<!DOCTYPE' in header or b'<html' in header.lower():
                return False, "HTML error page received"
            return False, f"Invalid JPEG magic bytes: {magic.hex()}"

    except Exception as e:
        return False, f"Error reading file: {e}"

    return True, "Valid JPEG"


# =============================================================================
# Downloader
# =============================================================================

class CDLIDownloader:
    """HTTP download manager with retry and rate limiting."""

    def __init__(self, rate_limit: float = RATE_LIMIT):
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CDLI-Research-Downloader/1.0 (Academic Research; Windows)"
        })
        # Disable SSL warnings for cdli.earth certificate issues
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    def download_image(self, p_number: str, dest_dir: Path) -> tuple[bool, str, Optional[str]]:
        """
        Download image for a P-number.

        Returns:
            (success, message, checksum or None)
        """
        dest_file = dest_dir / f"{p_number}.jpg"

        # Try photo first, then lineart
        urls = [
            CDLI_PHOTO_URL.format(p_number),
            CDLI_LINEART_URL.format(p_number),
        ]

        for url in urls:
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    self._rate_limit()

                    response = self.session.get(
                        url,
                        timeout=REQUEST_TIMEOUT,
                        verify=False,  # CDLI has certificate issues
                        stream=True,
                    )

                    if response.status_code == 404:
                        break  # Try next URL

                    response.raise_for_status()

                    # Check Content-Type
                    content_type = response.headers.get("Content-Type", "")
                    if "image" not in content_type and "jpeg" not in content_type:
                        continue

                    # Write to file
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    with open(dest_file, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # Validate the downloaded image
                    is_valid, reason = validate_image(dest_file)
                    if not is_valid:
                        dest_file.unlink()  # Delete invalid file
                        logger.debug(f"{p_number}: {reason}")
                        continue

                    # Compute checksum
                    checksum = compute_sha256(dest_file)
                    return True, "Downloaded", checksum

                except requests.exceptions.Timeout:
                    delay = RETRY_DELAY * (attempt + 1)
                    logger.debug(f"{p_number}: Timeout, retry {attempt + 1}/{RETRY_ATTEMPTS}")
                    time.sleep(delay)

                except requests.exceptions.RequestException as e:
                    delay = RETRY_DELAY * (attempt + 1)
                    logger.debug(f"{p_number}: {e}, retry {attempt + 1}/{RETRY_ATTEMPTS}")
                    time.sleep(delay)

        return False, "No image available", None


# =============================================================================
# Main Functions
# =============================================================================

def load_p_numbers(filepath: Path) -> list[str]:
    """Load P-numbers from text file."""
    if not filepath.exists():
        logger.error(f"P-numbers file not found: {filepath}")
        logger.error("Make sure p_numbers_with_images.txt is in the same directory as this script.")
        sys.exit(1)

    with open(filepath, encoding="utf-8") as f:
        p_numbers = [line.strip() for line in f if line.strip().startswith("P")]

    return p_numbers


def verify_downloads(progress: ProgressTracker, images_dir: Path) -> dict:
    """Verify integrity of downloaded images."""
    logger.info("Verifying downloaded images...")

    results = {
        "verified": 0,
        "corrupted": [],
        "missing": [],
        "checksum_mismatch": [],
    }

    completed = progress.state.get("completed", [])

    for p_number in tqdm(completed, desc="Verifying"):
        filepath = images_dir / f"{p_number}.jpg"

        if not filepath.exists():
            results["missing"].append(p_number)
            continue

        # Validate image format
        is_valid, reason = validate_image(filepath)
        if not is_valid:
            results["corrupted"].append((p_number, reason))
            continue

        # Check checksum
        expected = progress.get_checksum(p_number)
        if expected:
            actual = compute_sha256(filepath)
            if actual != expected:
                results["checksum_mismatch"].append(p_number)
                continue

        results["verified"] += 1

    return results


def download_batch(
    p_numbers: list[str],
    progress: ProgressTracker,
    downloader: CDLIDownloader,
    images_dir: Path,
    batch_size: int,
    max_workers: int = MAX_WORKERS,
) -> dict:
    """Download a batch of images with parallel workers."""

    # Filter out already completed
    pending = [p for p in p_numbers if not progress.is_completed(p)]

    if not pending:
        logger.info("All images already downloaded!")
        return {"downloaded": 0, "failed": 0, "skipped": len(p_numbers)}

    # Limit to batch size
    to_download = pending[:batch_size]

    logger.info(f"Downloading {len(to_download)} images ({len(p_numbers) - len(pending)} already done)")
    logger.info(f"Using {max_workers} parallel workers at {RATE_LIMIT} req/s")
    logger.info("Press CTRL+C to stop gracefully and save progress.\n")

    stats = {"downloaded": 0, "failed": 0, "skipped": 0}
    save_interval = 100  # Save progress every N images

    with tqdm(total=len(to_download), desc="Downloading", unit="img") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(downloader.download_image, p, images_dir): p
                for p in to_download
            }

            for i, future in enumerate(as_completed(futures)):
                if progress.interrupted:
                    break

                p_number = futures[future]

                try:
                    success, message, checksum = future.result()

                    if success:
                        progress.mark_completed(p_number, checksum)
                        stats["downloaded"] += 1
                    else:
                        progress.mark_failed(p_number, message)
                        stats["failed"] += 1

                except Exception as e:
                    progress.mark_failed(p_number, str(e))
                    stats["failed"] += 1
                    logger.error(f"{p_number}: Unexpected error - {e}")

                pbar.update(1)
                pbar.set_postfix({
                    "OK": stats["downloaded"],
                    "Fail": stats["failed"],
                })

                # Periodic save
                if (i + 1) % save_interval == 0:
                    progress.save()

    # Final save
    progress.save()

    return stats


def print_summary(progress: ProgressTracker, stats: dict, total_available: int):
    """Print download session summary."""
    completed = len(progress.state.get("completed", []))
    failed = len(progress.state.get("failed", []))

    logger.info("\n" + "=" * 60)
    logger.info("DOWNLOAD SESSION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  This session: {stats['downloaded']} downloaded, {stats['failed']} failed")
    logger.info(f"  Total progress: {completed:,} / {total_available:,} ({completed * 100 // total_available}%)")
    logger.info(f"  Remaining: {total_available - completed:,}")
    logger.info("")
    logger.info(f"  Progress file: {PROGRESS_FILE}")
    logger.info(f"  Images folder: {IMAGES_DIR}")
    logger.info("")

    if completed < total_available:
        logger.info("  Run this script again to continue downloading.")
    else:
        logger.info("  ALL IMAGES DOWNLOADED!")

    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Download CDLI tablet images with resume capability"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Max images to download per session (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify integrity of existing downloads",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset progress and start fresh",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Parallel download threads (default: {MAX_WORKERS})",
    )
    args = parser.parse_args()

    # Banner
    logger.info("=" * 60)
    logger.info("CDLI IMAGE DOWNLOADER")
    logger.info("=" * 60)
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Images folder: {IMAGES_DIR}")
    logger.info("")

    # Create directories
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize progress tracker
    progress = ProgressTracker(PROGRESS_FILE, CHECKSUM_FILE)

    # Reset if requested
    if args.reset:
        logger.warning("Resetting all progress...")
        progress.reset()

    # Load P-numbers
    p_numbers = load_p_numbers(P_NUMBERS_FILE)
    logger.info(f"Loaded {len(p_numbers):,} P-numbers from {P_NUMBERS_FILE.name}")

    # Show current progress
    completed_count = len(progress.state.get("completed", []))
    logger.info(f"Already downloaded: {completed_count:,}")
    logger.info(f"Remaining: {len(p_numbers) - completed_count:,}")
    logger.info("")

    # Verify mode
    if args.verify:
        results = verify_downloads(progress, IMAGES_DIR)
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"  Verified OK: {results['verified']}")
        logger.info(f"  Missing files: {len(results['missing'])}")
        logger.info(f"  Corrupted: {len(results['corrupted'])}")
        logger.info(f"  Checksum mismatch: {len(results['checksum_mismatch'])}")

        if results['corrupted']:
            logger.info("\nCorrupted files:")
            for p, reason in results['corrupted'][:10]:
                logger.info(f"  {p}: {reason}")
            if len(results['corrupted']) > 10:
                logger.info(f"  ... and {len(results['corrupted']) - 10} more")

        return

    # Download
    workers = args.workers

    downloader = CDLIDownloader(rate_limit=RATE_LIMIT)

    stats = download_batch(
        p_numbers=p_numbers,
        progress=progress,
        downloader=downloader,
        images_dir=IMAGES_DIR,
        batch_size=args.batch,
        max_workers=workers,
    )

    print_summary(progress, stats, len(p_numbers))


if __name__ == "__main__":
    main()
