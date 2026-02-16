#!/usr/bin/env python3
"""
Batch thumbnail generation for all tablets with images.
Generates 4 standard sizes (64, 100, 120, 200px) with checkpointing and resume capability.

Usage:
    python3 generate_all_thumbnails.py [OPTIONS]

Options:
    --reset              Start from scratch (ignore checkpoint)
    --force-regenerate   Regenerate all thumbnails (overwrite existing)
    --workers N          Number of parallel workers (default: 10)
    --sizes SIZE1,SIZE2  Comma-separated sizes to generate (default: 64,100,120,200)
    --verify-only        Check how many tablets need thumbnails without generating
"""

import argparse
import json
import logging
import signal
import sqlite3
import ssl
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple, List

try:
    from PIL import Image
except ImportError:
    print("ERROR: PIL (Pillow) is required. Install with: pip3 install Pillow")
    sys.exit(1)

# Configuration
BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DB_PATH = BASE_DIR / "database" / "glintstone.db"
IMAGE_DIR = BASE_DIR / "database" / "images"
THUMBNAIL_DIR = IMAGE_DIR / "thumbnails"
PROGRESS_DIR = BASE_DIR / "data-tools" / "import" / "_progress"
ERROR_DIR = BASE_DIR / "data-tools" / "import" / "_errors"
CHECKPOINT_PATH = PROGRESS_DIR / "thumbnail_generation_state.json"
ERROR_LOG_PATH = ERROR_DIR / "thumbnail_generation_errors.log"

# CDLI URLs
CDLI_PHOTO_URL = "https://cdli.earth/dl/photo/{}.jpg"
CDLI_LINEART_URL = "https://cdli.earth/dl/lineart/{}.jpg"

# SSL context for CDLI
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Processing settings
DEFAULT_WORKERS = 10
DEFAULT_SIZES = [64, 100, 120, 200]
REQUEST_TIMEOUT = 10
MAX_RETRIES = 2
CHECKPOINT_INTERVAL = 100  # Save checkpoint every N tablets
JPEG_QUALITY = 85
BACKGROUND_COLOR = (30, 30, 35)  # Dark theme background


class ThumbnailGenerator:
    def __init__(self, args):
        self.args = args
        self.interrupted = False
        self.state = self._load_state() if not args.reset else self._fresh_state()
        self.stats = {
            'processed': 0,
            'generated': 0,
            'skipped_existing': 0,
            'errors': 0,
            'error_tablets': []
        }

        # Create necessary directories
        THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        ERROR_DIR.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            filename=ERROR_LOG_PATH,
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Handle graceful interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        print("\n\nInterrupt received. Saving checkpoint...")
        self.interrupted = True

    def _fresh_state(self) -> dict:
        return {
            'last_processed_index': 0,
            'started_at': datetime.now().isoformat(),
            'completed': False
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
        """Save checkpoint state atomically."""
        self.state['last_processed_index'] = self.stats['processed']
        self.state['completed'] = completed
        self.state['last_updated'] = datetime.now().isoformat()
        self.state['stats'] = self.stats.copy()

        # Write atomically
        temp_path = CHECKPOINT_PATH.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(self.state, f, indent=2)
        temp_path.rename(CHECKPOINT_PATH)

    def get_tablets_with_images(self) -> List[str]:
        """Query database for all tablets with images."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT a.p_number
            FROM artifacts a
            JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE ps.has_image = 1
            ORDER BY a.p_number ASC
        ''')

        tablets = [row[0] for row in cursor.fetchall()]
        conn.close()

        return tablets

    def fetch_remote_image(self, url: str) -> Optional[bytes]:
        """Fetch image from CDLI with retries."""
        for attempt in range(MAX_RETRIES):
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Glintstone/1.0 (Cuneiform Research Platform)')

                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as response:
                    content_type = response.headers.get('Content-Type', '')

                    if 'image' not in content_type:
                        return None

                    data = response.read()

                    if len(data) < 1000:  # Too small to be a real image
                        return None

                    return data

            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
                if attempt == MAX_RETRIES - 1:
                    return None
                time.sleep(0.5)  # Brief delay before retry

        return None

    def get_source_image(self, p_number: str) -> Tuple[Optional[Image.Image], Optional[str]]:
        """
        Get source image for a tablet using fallback chain.
        Returns (PIL Image, source_type) or (None, None) if not found.
        """
        # 1. Try local storage first
        local_path = IMAGE_DIR / f"{p_number}.jpg"
        if local_path.exists():
            try:
                img = Image.open(local_path)
                return (img, 'local')
            except Exception as e:
                logging.error(f"{p_number}: Failed to open local image: {e}")

        # 2. Try CDLI photo
        photo_data = self.fetch_remote_image(CDLI_PHOTO_URL.format(p_number))
        if photo_data:
            try:
                from io import BytesIO
                img = Image.open(BytesIO(photo_data))
                return (img, 'cdli-photo')
            except Exception as e:
                logging.error(f"{p_number}: Failed to parse CDLI photo: {e}")

        # 3. Try CDLI lineart
        lineart_data = self.fetch_remote_image(CDLI_LINEART_URL.format(p_number))
        if lineart_data:
            try:
                from io import BytesIO
                img = Image.open(BytesIO(lineart_data))
                return (img, 'cdli-lineart')
            except Exception as e:
                logging.error(f"{p_number}: Failed to parse CDLI lineart: {e}")

        return (None, None)

    def generate_square_thumbnail(self, source_img: Image.Image, size: int) -> Image.Image:
        """
        Generate square center-cropped thumbnail.
        Replicates the PHP GD logic from thumbnail.php.
        """
        # Get source dimensions
        width, height = source_img.size

        # Calculate center crop dimensions
        crop_size = min(width, height)
        crop_x = (width - crop_size) // 2
        crop_y = (height - crop_size) // 2

        # Crop to square from center
        cropped = source_img.crop((
            crop_x,
            crop_y,
            crop_x + crop_size,
            crop_y + crop_size
        ))

        # Resize to target size with high-quality filter
        thumbnail = cropped.resize((size, size), Image.Resampling.LANCZOS)

        # Convert to RGB if needed (handles RGBA, P mode, etc.)
        if thumbnail.mode != 'RGB':
            # Create RGB image with dark background
            rgb_thumbnail = Image.new('RGB', (size, size), BACKGROUND_COLOR)
            if thumbnail.mode == 'RGBA':
                rgb_thumbnail.paste(thumbnail, mask=thumbnail.split()[3])  # Use alpha as mask
            else:
                rgb_thumbnail.paste(thumbnail)
            thumbnail = rgb_thumbnail

        return thumbnail

    def process_tablet(self, p_number: str) -> Tuple[str, int, int, List[str]]:
        """
        Process a single tablet and generate all thumbnail sizes.
        Returns (p_number, generated_count, skipped_count, errors).
        """
        generated = 0
        skipped = 0
        errors = []

        # Check which thumbnails already exist
        sizes_to_generate = []
        for size in self.args.sizes:
            thumbnail_path = THUMBNAIL_DIR / f"{p_number}_{size}.jpg"
            if thumbnail_path.exists() and not self.args.force_regenerate:
                skipped += 1
            else:
                sizes_to_generate.append(size)

        # If all thumbnails exist and not forcing regeneration, skip
        if not sizes_to_generate:
            return (p_number, generated, skipped, errors)

        # Get source image
        source_img, source_type = self.get_source_image(p_number)

        if source_img is None:
            error_msg = f"{p_number}: No source image available"
            errors.append(error_msg)
            logging.error(error_msg)
            return (p_number, generated, skipped, errors)

        # Generate each size
        for size in sizes_to_generate:
            try:
                thumbnail = self.generate_square_thumbnail(source_img, size)
                thumbnail_path = THUMBNAIL_DIR / f"{p_number}_{size}.jpg"
                thumbnail.save(thumbnail_path, 'JPEG', quality=JPEG_QUALITY)
                generated += 1
            except Exception as e:
                error_msg = f"{p_number}: Failed to generate {size}px thumbnail: {e}"
                errors.append(error_msg)
                logging.error(error_msg)

        # Clean up source image
        source_img.close()

        return (p_number, generated, skipped, errors)

    def verify_only(self, tablets: List[str]):
        """Check how many thumbnails need to be generated without generating them."""
        print("=" * 70)
        print("VERIFICATION MODE - No thumbnails will be generated")
        print("=" * 70)
        print()

        total_tablets = len(tablets)
        needs_generation = 0
        fully_cached = 0
        total_files_needed = 0

        for p_number in tablets:
            missing_sizes = 0
            for size in self.args.sizes:
                thumbnail_path = THUMBNAIL_DIR / f"{p_number}_{size}.jpg"
                if not thumbnail_path.exists():
                    missing_sizes += 1

            if missing_sizes > 0:
                needs_generation += 1
                total_files_needed += missing_sizes
            else:
                fully_cached += 1

        print(f"Total tablets with images: {total_tablets:,}")
        print(f"Fully cached tablets: {fully_cached:,}")
        print(f"Tablets needing thumbnails: {needs_generation:,}")
        print(f"Total thumbnail files needed: {total_files_needed:,}")
        print()
        print(f"Estimated storage: {total_files_needed * 10 / 1024:.1f} MB (approximate)")
        print()

    def run(self):
        """Main processing loop."""
        print("=" * 70)
        print("BATCH THUMBNAIL GENERATION")
        print("=" * 70)
        print()

        # Get tablets to process
        tablets = self.get_tablets_with_images()
        total_tablets = len(tablets)

        print(f"Total tablets with images: {total_tablets:,}")
        print(f"Thumbnail sizes: {', '.join(map(str, self.args.sizes))}px")
        print(f"Parallel workers: {self.args.workers}")
        print(f"Force regenerate: {self.args.force_regenerate}")
        print()

        # Verify only mode
        if self.args.verify_only:
            self.verify_only(tablets)
            return

        # Resume from checkpoint
        start_index = self.state['last_processed_index']
        if start_index > 0:
            print(f"Resuming from checkpoint at tablet {start_index + 1:,}/{total_tablets:,}")
            print()

        # Process tablets
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.args.workers) as executor:
            futures = {}

            for i in range(start_index, total_tablets):
                if self.interrupted:
                    break

                p_number = tablets[i]
                future = executor.submit(self.process_tablet, p_number)
                futures[future] = p_number

            # Collect results
            for future in as_completed(futures):
                if self.interrupted:
                    break

                p_number, generated, skipped, errors = future.result()

                self.stats['processed'] += 1
                self.stats['generated'] += generated
                self.stats['skipped_existing'] += skipped

                if errors:
                    self.stats['errors'] += len(errors)
                    self.stats['error_tablets'].append(p_number)

                # Progress report
                if self.stats['processed'] % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
                    remaining = total_tablets - start_index - self.stats['processed']
                    eta = remaining / rate if rate > 0 else 0

                    print(f"\rProgress: {self.stats['processed']:,}/{total_tablets - start_index:,} "
                          f"({self.stats['processed'] * 100 // (total_tablets - start_index)}%) - "
                          f"Generated: {self.stats['generated']:,} files - "
                          f"Skipped: {self.stats['skipped_existing']:,} - "
                          f"Errors: {self.stats['errors']} - "
                          f"Rate: {rate:.1f}/s - "
                          f"ETA: {eta/60:.1f}min", end='', flush=True)

                # Save checkpoint periodically
                if self.stats['processed'] % CHECKPOINT_INTERVAL == 0:
                    self._save_state()

        print()  # New line after progress

        # Save final state
        self._save_state(completed=not self.interrupted)

        # Final report
        elapsed = time.time() - start_time
        print()
        print("=" * 70)
        if self.interrupted:
            print("INTERRUPTED - Checkpoint saved")
        else:
            print("COMPLETE")
        print("=" * 70)
        print(f"Processed: {self.stats['processed']:,} tablets")
        print(f"Generated: {self.stats['generated']:,} thumbnails")
        print(f"Skipped existing: {self.stats['skipped_existing']:,} thumbnails")
        print(f"Errors: {self.stats['errors']} ({len(self.stats['error_tablets'])} tablets)")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        if self.stats['error_tablets']:
            print(f"Error log: {ERROR_LOG_PATH}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Batch generate thumbnails for all tablets with images'
    )
    parser.add_argument('--reset', action='store_true',
                        help='Start from scratch (ignore checkpoint)')
    parser.add_argument('--force-regenerate', action='store_true',
                        help='Regenerate all thumbnails (overwrite existing)')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS,
                        help=f'Number of parallel workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--sizes', type=str, default=','.join(map(str, DEFAULT_SIZES)),
                        help=f'Comma-separated sizes to generate (default: {",".join(map(str, DEFAULT_SIZES))})')
    parser.add_argument('--verify-only', action='store_true',
                        help='Check how many tablets need thumbnails without generating')

    args = parser.parse_args()

    # Parse sizes
    try:
        args.sizes = [int(s.strip()) for s in args.sizes.split(',')]
    except ValueError:
        print("ERROR: --sizes must be comma-separated integers (e.g., 64,100,120,200)")
        sys.exit(1)

    # Validate sizes
    for size in args.sizes:
        if size < 50 or size > 400:
            print(f"ERROR: Size {size} is out of range (50-400)")
            sys.exit(1)

    # Check database exists
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    # Run generator
    generator = ThumbnailGenerator(args)
    generator.run()


if __name__ == "__main__":
    main()
