#!/usr/bin/env python3
"""
Cuneiform Data Download Script
==============================
Downloads production-scale cuneiform data from multiple academic sources.

Sources:
- CDLI (Cuneiform Digital Library Initiative) - metadata + images
- ORACC (Open Richly Annotated Cuneiform Corpus) - lemmatized texts
- eBL (Electronic Babylonian Literature) - fragments database
- CAD (Chicago Assyrian Dictionary) - PDF volumes
- ePSD2 (Electronic Pennsylvania Sumerian Dictionary) - via ORACC
- ML Models (DeepScribe, Akkademia) - OCR and translation

Usage:
    python download_cuneiform_data.py [--dry-run] [--source SOURCE] [--limit N]

Options:
    --dry-run       Show what would be downloaded without downloading
    --source        Download only specific source (cdli, oracc, ebl, cad, ml)
    --limit N       Limit number of items (for testing)
    --resume        Resume from last progress state (default behavior)
    --verify        Verify checksums of existing downloads
"""

import argparse
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install requests tqdm")
    sys.exit(1)

# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
PROGRESS_FILE = BASE_DIR / "_progress" / "download_state.json"
CHECKSUM_FILE = BASE_DIR / "_progress" / "checksums.json"
ERROR_LOG = BASE_DIR / "_progress" / "errors.log"

# Rate limiting (requests per second)
RATE_LIMIT = 1.0
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds

# Default limits for production scale
DEFAULT_IMAGE_LIMIT = 10000

# URLs
CDLI_GITHUB = "https://github.com/cdli-gh/data.git"
CDLI_IMAGE_BASE = "https://cdli.earth/dl"
ORACC_PROJECTS_URL = "http://oracc.museum.upenn.edu/projects.json"
ORACC_JSON_BASE = "http://build-oracc.museum.upenn.edu/json"
EBL_API_BASE = "https://www.ebl.lmu.de/api"
ARCHIVE_ORG_BASE = "https://archive.org"
DEEPSCRIBE_REPO = "https://github.com/oi-deepscribe/deepscribe.git"
AKKADEMIA_REPO = "https://github.com/gaigutherz/Akkademia.git"

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ERROR_LOG, mode="a"),
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

        # Handle graceful interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        logger.warning("\nInterrupt received. Saving progress...")
        self._interrupted = True
        self.save()
        sys.exit(1)

    def _load_state(self) -> dict:
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Corrupted progress file, starting fresh")
        return {
            "started_at": datetime.now().isoformat(),
            "sources": {},
        }

    def reset_source(self, source: str):
        """Reset a specific source's progress."""
        if source in self.state["sources"]:
            del self.state["sources"][source]
            self.save()

    def _load_checksums(self) -> dict:
        if self.checksum_file.exists():
            with open(self.checksum_file) as f:
                return json.load(f)
        return {}

    def save(self):
        """Atomically save progress state."""
        self.state["last_updated"] = datetime.now().isoformat()

        # Write to temp file, then rename (atomic on POSIX)
        temp_file = self.progress_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(self.state, f, indent=2)
        temp_file.rename(self.progress_file)

        # Save checksums
        temp_checksum = self.checksum_file.with_suffix(".tmp")
        with open(temp_checksum, "w") as f:
            json.dump(self.checksums, f, indent=2)
        temp_checksum.rename(self.checksum_file)

    def get_source_state(self, source: str) -> dict:
        return self.state["sources"].get(source, {"status": "pending"})

    def set_source_state(self, source: str, state: dict):
        self.state["sources"][source] = state
        self.save()

    def is_file_downloaded(self, filepath: str) -> bool:
        """Check if file exists and has valid checksum."""
        path = Path(filepath)
        if not path.exists():
            return False
        if filepath in self.checksums:
            return self._verify_checksum(path, self.checksums[filepath])
        return True  # File exists but no checksum recorded

    def record_checksum(self, filepath: str, checksum: str):
        self.checksums[filepath] = checksum

    def _verify_checksum(self, filepath: Path, expected: str) -> bool:
        actual = compute_sha256(filepath)
        return actual == expected

    @property
    def interrupted(self) -> bool:
        return self._interrupted


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_download(file_path: Path, expected_type: str = None) -> bool:
    """
    Validate a downloaded file is not an HTML error page.

    Args:
        file_path: Path to the downloaded file
        expected_type: Expected file type ('image', 'json', 'zip', etc.)

    Returns:
        True if file appears valid, False if it's an HTML error page or corrupted
    """
    if not file_path.exists():
        return False

    file_size = file_path.stat().st_size

    # Empty files are invalid
    if file_size == 0:
        logger.warning(f"Empty file detected: {file_path}")
        return False

    # Check for suspiciously small files (likely error pages)
    # 643 bytes is the exact size of ORACC error pages
    if file_size < 1000:
        try:
            with open(file_path, 'rb') as f:
                header = f.read(500)

            # Check for HTML signatures
            html_signatures = [
                b'<!DOCTYPE', b'<!doctype',
                b'<html', b'<HTML',
                b'<head', b'<HEAD',
                b'Oracc Pager',  # Specific ORACC error page signature
            ]

            for sig in html_signatures:
                if sig in header:
                    logger.warning(f"HTML error page detected: {file_path} ({file_size} bytes)")
                    file_path.unlink()  # Delete invalid file
                    return False

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return False

    # Type-specific validation
    if expected_type == 'image':
        # Check for JPEG/PNG magic bytes
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(8)
            jpeg_magic = b'\xff\xd8\xff'
            png_magic = b'\x89PNG\r\n\x1a\n'
            if not (magic.startswith(jpeg_magic) or magic.startswith(png_magic)):
                logger.warning(f"Invalid image file: {file_path}")
                return False
        except Exception:
            pass

    elif expected_type == 'zip':
        # Check for ZIP magic bytes
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
            if magic != b'PK\x03\x04' and magic != b'PK\x05\x06':
                logger.warning(f"Invalid ZIP file: {file_path}")
                file_path.unlink()
                return False
        except Exception:
            pass

    return True


# =============================================================================
# Download Utilities
# =============================================================================

class Downloader:
    """HTTP download manager with retry and rate limiting."""

    def __init__(self, rate_limit: float = RATE_LIMIT, dry_run: bool = False,
                 verify_ssl: bool = True):
        self.rate_limit = rate_limit
        self.dry_run = dry_run
        self.verify_ssl = verify_ssl
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CuneiformDataDownloader/1.0 (Academic Research)"
        })

        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL verification disabled - use with caution")

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < (1.0 / self.rate_limit):
            time.sleep((1.0 / self.rate_limit) - elapsed)
        self.last_request_time = time.time()

    def download_file(
        self,
        url: str,
        dest: Path,
        desc: str = None,
        verify_checksum: str = None,
    ) -> bool:
        """Download a file with retry logic."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would download: {url} -> {dest}")
            return True

        if dest.exists() and verify_checksum:
            if compute_sha256(dest) == verify_checksum:
                logger.debug(f"Skipping (valid): {dest.name}")
                return True

        self._rate_limit()

        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = self.session.get(url, stream=True, timeout=60,
                                            verify=self.verify_ssl)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                dest.parent.mkdir(parents=True, exist_ok=True)

                with open(dest, "wb") as f:
                    with tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        desc=desc or dest.name,
                        leave=False,
                    ) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))

                return True

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

        logger.error(f"Failed to download: {url}")
        return False

    def get_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would fetch JSON: {url}")
            return None

        self._rate_limit()

        try:
            response = self.session.get(url, timeout=30, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JSON from {url}: {e}")
            return None


# =============================================================================
# CDLI Downloads
# =============================================================================

def download_cdli_metadata(
    progress: ProgressTracker,
    downloader: Downloader,
) -> bool:
    """Clone CDLI data repository with Git LFS."""
    logger.info("=" * 60)
    logger.info("CDLI Metadata (Git Repository)")
    logger.info("=" * 60)

    dest_dir = BASE_DIR / "CDLI" / "metadata"
    state = progress.get_source_state("cdli_metadata")

    if state.get("status") == "complete":
        logger.info("CDLI metadata already downloaded. Skipping.")
        return True

    if downloader.dry_run:
        logger.info(f"[DRY-RUN] Would clone: {CDLI_GITHUB} -> {dest_dir}")
        return True

    # Check if git-lfs is installed
    try:
        subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("git-lfs not installed. Install with: brew install git-lfs")
        return False

    try:
        if (dest_dir / ".git").exists():
            logger.info("Repository exists. Pulling updates...")
            subprocess.run(
                ["git", "-C", str(dest_dir), "pull"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(dest_dir), "lfs", "pull"],
                check=True,
            )
        else:
            logger.info("Cloning CDLI data repository (this may take a while)...")
            subprocess.run(
                ["git", "clone", CDLI_GITHUB, str(dest_dir)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(dest_dir), "lfs", "pull"],
                check=True,
            )

        progress.set_source_state("cdli_metadata", {
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
        })
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        return False


# CDLI API endpoint for catalogue
CDLI_API_BASE = "https://cdli.earth"


def download_cdli_catalogue(
    progress: ProgressTracker,
    downloader: Downloader,
    limit: int = DEFAULT_IMAGE_LIMIT,
) -> bool:
    """Download CDLI catalogue via API with pagination."""
    logger.info("=" * 60)
    logger.info(f"CDLI Catalogue (limit: {limit} records)")
    logger.info("=" * 60)

    catalogue_dir = BASE_DIR / "CDLI" / "catalogue"
    catalogue_dir.mkdir(parents=True, exist_ok=True)

    state = progress.get_source_state("cdli_catalogue")

    if downloader.dry_run:
        logger.info(f"[DRY-RUN] Would download CDLI catalogue ({limit} records)")
        return True

    # Get existing progress
    downloaded_count = state.get("record_count", 0)
    batch_size = 1000  # Records per API request

    if downloaded_count >= limit:
        logger.info(f"CDLI catalogue already has {downloaded_count} records. Skipping.")
        return True

    logger.info(f"Downloading CDLI catalogue (starting from offset {downloaded_count})...")

    total_downloaded = downloaded_count
    batch_num = downloaded_count // batch_size

    while total_downloaded < limit:
        if progress.interrupted:
            break

        offset = batch_num * batch_size
        url = f"{CDLI_API_BASE}/artifacts?limit={batch_size}&offset={offset}"

        try:
            response = downloader.session.get(url, timeout=120, verify=downloader.verify_ssl)
            response.raise_for_status()
            data = response.json()

            # Handle different response formats
            records = data.get("data", data) if isinstance(data, dict) else data

            if not records:
                logger.info(f"No more records at offset {offset}")
                break

            # Save batch to file
            batch_file = catalogue_dir / f"batch-{batch_num:05d}.json"
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            record_count = len(records) if isinstance(records, list) else 0
            total_downloaded += record_count
            batch_num += 1

            logger.info(f"Downloaded batch {batch_num}: {record_count} records (total: {total_downloaded})")

            # Save progress
            progress.set_source_state("cdli_catalogue", {
                "status": "partial",
                "record_count": total_downloaded,
                "batches": batch_num,
                "timestamp": datetime.now().isoformat(),
            })

            # If we got fewer records than requested, we've reached the end
            if record_count < batch_size:
                break

            # Rate limiting
            time.sleep(1.0 / downloader.rate_limit)

        except Exception as e:
            logger.error(f"Failed to download catalogue batch at offset {offset}: {e}")
            break

    status = "complete" if total_downloaded >= limit or total_downloaded > 0 else "failed"
    progress.set_source_state("cdli_catalogue", {
        "status": status,
        "record_count": total_downloaded,
        "batches": batch_num,
        "timestamp": datetime.now().isoformat(),
    })

    logger.info(f"CDLI catalogue: {total_downloaded} records downloaded")
    return total_downloaded > 0


def download_cdli_images(
    progress: ProgressTracker,
    downloader: Downloader,
    limit: int = DEFAULT_IMAGE_LIMIT,
) -> bool:
    """Download tablet images from CDLI."""
    logger.info("=" * 60)
    logger.info(f"CDLI Images (limit: {limit})")
    logger.info("=" * 60)

    images_dir = BASE_DIR / "CDLI" / "images"
    state = progress.get_source_state("cdli_images")

    # Get list of P-numbers from metadata
    p_numbers = []

    # Try ATF file first (most reliable source with 135K+ P-numbers)
    atf_file = BASE_DIR / "CDLI" / "metadata" / "cdliatf_unblocked.atf"
    if atf_file.exists():
        logger.info("Extracting P-numbers from ATF file...")
        p_numbers = extract_p_numbers_from_atf(atf_file, limit)
    else:
        # Try JSON catalogue as fallback
        json_catalogue_dir = BASE_DIR / "CDLI" / "catalogue"
        if json_catalogue_dir.exists() and list(json_catalogue_dir.glob("batch-*.json")):
            logger.info("Using JSON catalogue for P-numbers...")
            p_numbers = extract_p_numbers_from_json(json_catalogue_dir, limit)

    # Final fallback to sample P-numbers
    if not p_numbers:
        logger.warning("CDLI catalogue not found. Using sample P-numbers...")
        p_numbers = get_sample_p_numbers()

    if not p_numbers:
        logger.error("No P-numbers found to download")
        return False

    # Track what we've already downloaded
    completed = set(state.get("completed_ids", []))
    failed = []

    logger.info(f"Found {len(p_numbers)} P-numbers, {len(completed)} already done")

    # Download images
    pending = [p for p in p_numbers if p not in completed][:limit]

    with tqdm(total=len(pending), desc="Downloading images") as pbar:
        for p_number in pending:
            if progress.interrupted:
                break

            success = False
            for img_type in ["photo", "lineart"]:
                url = f"{CDLI_IMAGE_BASE}/{img_type}/{p_number}.jpg"
                dest = images_dir / img_type / f"{p_number}.jpg"

                if downloader.download_file(url, dest, desc=f"{p_number} ({img_type})"):
                    # Validate the downloaded file is actually an image
                    if dest.exists() and validate_download(dest, expected_type='image'):
                        success = True
                        checksum = compute_sha256(dest)
                        progress.record_checksum(str(dest), checksum)

            if success:
                completed.add(p_number)
            else:
                failed.append(p_number)

            pbar.update(1)

            # Save progress periodically
            if len(completed) % 100 == 0:
                progress.set_source_state("cdli_images", {
                    "status": "partial",
                    "completed_ids": list(completed),
                    "failed_ids": failed,
                    "total": len(p_numbers),
                })

    # Final save
    status = "complete" if len(completed) >= limit else "partial"
    progress.set_source_state("cdli_images", {
        "status": status,
        "completed_ids": list(completed),
        "failed_ids": failed,
        "total": len(p_numbers),
        "timestamp": datetime.now().isoformat(),
    })

    logger.info(f"CDLI images: {len(completed)} downloaded, {len(failed)} failed")
    return len(failed) == 0


def extract_p_numbers_from_catalogue(catalogue_file: Path, limit: int) -> list:
    """Extract P-numbers from CDLI catalogue CSV."""
    p_numbers = []
    try:
        with open(catalogue_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0:  # Skip header
                    continue
                # P-number is typically first column
                parts = line.split(",")
                if parts and parts[0].startswith("P"):
                    p_numbers.append(parts[0].strip().strip('"'))
                if len(p_numbers) >= limit * 2:  # Get extra for filtering
                    break
    except Exception as e:
        logger.error(f"Error reading catalogue: {e}")
    return p_numbers[:limit]


def extract_p_numbers_from_json(json_dir: Path, limit: int) -> list:
    """Extract P-numbers from CDLI catalogue JSON files."""
    import re
    p_numbers = []
    p_number_pattern = re.compile(r'P\d{6}')

    # Find all batch JSON files
    json_files = sorted(json_dir.glob("batch-*.json"))
    if not json_files:
        logger.warning(f"No batch JSON files found in {json_dir}")
        return []

    for json_file in json_files:
        if len(p_numbers) >= limit:
            break

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle both direct array and {data: [...]} structure
            records = data.get("data", data) if isinstance(data, dict) else data

            for record in records:
                if len(p_numbers) >= limit:
                    break

                # Try to extract P-number from inscription ATF
                inscription = record.get("inscription", {})
                atf = inscription.get("atf", "") if isinstance(inscription, dict) else ""

                # P-number appears at start of ATF: "&P000001 = ..."
                match = p_number_pattern.search(atf)
                if match:
                    p_num = match.group()
                    if p_num not in p_numbers:
                        p_numbers.append(p_num)

        except Exception as e:
            logger.error(f"Error reading JSON catalogue {json_file}: {e}")

    logger.info(f"Extracted {len(p_numbers)} P-numbers from JSON catalogue")
    return p_numbers[:limit]


def extract_p_numbers_from_atf(atf_file: Path, limit: int) -> list:
    """Extract P-numbers from CDLI ATF file (most comprehensive source)."""
    import re
    p_numbers = []
    p_number_pattern = re.compile(r'&(P\d{6})')

    try:
        with open(atf_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if len(p_numbers) >= limit:
                    break
                match = p_number_pattern.search(line)
                if match:
                    p_num = match.group(1)
                    if p_num not in p_numbers:
                        p_numbers.append(p_num)
    except Exception as e:
        logger.error(f"Error reading ATF file: {e}")

    logger.info(f"Extracted {len(p_numbers)} P-numbers from ATF file")
    return p_numbers[:limit]


def get_sample_p_numbers() -> list:
    """Return sample P-numbers for well-known tablets with verified images."""
    # These P-numbers have been verified to have images on CDLI
    return [
        "P273202",  # Gilgamesh Tablet V (Sulaymaniyah)
        "P252163",  # Gilgamesh Penn
        "P273201",  # Flood Tablet XI
        "P217403",  # Cylinder seal
        "P100178",  # Administrative text
        "P100179",  # Administrative text
        "P100180",  # Administrative text
        "P100181",  # Administrative text
        "P100182",  # Administrative text
        "P100183",  # Administrative text
        "P100184",  # Administrative text
        "P100185",  # Administrative text
        "P100186",  # Administrative text
        "P100187",  # Administrative text
        "P100188",  # Administrative text
        "P100189",  # Administrative text
    ]


# =============================================================================
# ORACC Downloads
# =============================================================================

def download_oracc_projects(
    progress: ProgressTracker,
    downloader: Downloader,
) -> bool:
    """Download all ORACC projects as JSON archives."""
    logger.info("=" * 60)
    logger.info("ORACC Projects")
    logger.info("=" * 60)

    projects_dir = BASE_DIR / "ORACC" / "projects"
    state = progress.get_source_state("oracc_projects")

    # Fetch project list
    logger.info("Fetching ORACC project list...")
    projects_data = downloader.get_json(ORACC_PROJECTS_URL)

    if downloader.dry_run:
        logger.info("[DRY-RUN] Would download all ORACC projects")
        return True

    projects = []
    if projects_data:
        projects = extract_project_names(projects_data)

    if not projects:
        # Use known project list as fallback
        logger.warning("Could not parse project list. Using known projects.")
        projects = get_known_oracc_projects()

    completed = set(state.get("completed", []))
    failed = []

    logger.info(f"Found {len(projects)} projects, {len(completed)} already done")

    pending = [p for p in projects if p not in completed]

    for project in tqdm(pending, desc="Downloading ORACC projects"):
        if progress.interrupted:
            break

        url = f"{ORACC_JSON_BASE}/{project}.zip"
        dest = projects_dir / f"{project}.zip"

        if downloader.download_file(url, dest, desc=project):
            # Validate the downloaded file is actually a ZIP, not an HTML error
            if dest.exists() and validate_download(dest, expected_type='zip'):
                completed.add(project)
                progress.record_checksum(str(dest), compute_sha256(dest))
            else:
                logger.warning(f"Invalid or corrupted download for {project}")
                failed.append(project)
        else:
            failed.append(project)

        # Save progress
        progress.set_source_state("oracc_projects", {
            "status": "partial",
            "completed": list(completed),
            "failed": failed,
        })

    status = "complete" if not failed else "partial"
    progress.set_source_state("oracc_projects", {
        "status": status,
        "completed": list(completed),
        "failed": failed,
        "timestamp": datetime.now().isoformat(),
    })

    logger.info(f"ORACC: {len(completed)} downloaded, {len(failed)} failed")
    return len(failed) == 0


def extract_project_names(projects_data) -> list:
    """Extract project names from ORACC projects.json."""
    projects = []
    if isinstance(projects_data, list):
        for item in projects_data:
            if isinstance(item, dict) and "abbrev" in item:
                projects.append(item["abbrev"])
            elif isinstance(item, str):
                projects.append(item)
    elif isinstance(projects_data, dict):
        # Handle nested structure with 'public' key containing actual projects
        if "public" in projects_data and isinstance(projects_data["public"], list):
            for item in projects_data["public"]:
                if isinstance(item, dict) and "abbrev" in item:
                    projects.append(item["abbrev"])
        else:
            # Skip metadata keys like 'type', 'public'
            for key in projects_data:
                if key not in ("type", "public", "format"):
                    projects.append(key)

    # If we didn't get useful projects, return empty to trigger fallback
    if not projects or all(p in ("type", "public", "format") for p in projects):
        return []
    return projects


def get_known_oracc_projects() -> list:
    """Return list of known ORACC projects."""
    return [
        "epsd2",      # Pennsylvania Sumerian Dictionary
        "dcclt",      # Digital Corpus of Cuneiform Lexical Texts
        "saao",       # State Archives of Assyria Online
        "rinap",      # Royal Inscriptions of Neo-Assyrian Period
        "riao",       # Royal Inscriptions of Assur
        "etcsri",     # Electronic Text Corpus of Sumerian Royal Inscriptions
        "cams",       # Corpus of Ancient Mesopotamian Scholarship
        "amgg",       # Ancient Mesopotamian Gods and Goddesses
        "aemw",       # Archaic Cuneiform from Mesopotamia
        "blms",       # Babylonian-Assyrian Lexical and Magical Texts
    ]


# =============================================================================
# eBL Downloads
# =============================================================================

def download_ebl_dataset(
    progress: ProgressTracker,
    downloader: Downloader,
) -> bool:
    """Download eBL fragments dataset."""
    logger.info("=" * 60)
    logger.info("eBL (Electronic Babylonian Literature)")
    logger.info("=" * 60)

    ebl_dir = BASE_DIR / "eBL"
    state = progress.get_source_state("ebl")

    if state.get("status") == "complete":
        logger.info("eBL dataset already downloaded. Skipping.")
        return True

    if downloader.dry_run:
        logger.info("[DRY-RUN] Would download eBL fragments dataset")
        return True

    # eBL provides data through their API
    # Try to get the fragments list
    logger.info("Fetching eBL fragments list...")

    # The eBL API may require authentication for full dataset
    # Try public endpoint first
    fragments_url = f"{EBL_API_BASE}/fragments"

    try:
        response = downloader.session.get(
            fragments_url,
            params={"limit": 1000},
            timeout=60,
            verify=downloader.verify_ssl,
        )
        if response.status_code == 200:
            fragments = response.json()
            dest = ebl_dir / "fragments" / "fragments_sample.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w") as f:
                json.dump(fragments, f, indent=2)
            logger.info(f"Downloaded {len(fragments)} eBL fragments")
        else:
            logger.warning(f"eBL API returned {response.status_code}")
            # Clone the repository instead
            logger.info("Cloning eBL API repository for database access...")
            ebl_repo_dir = ebl_dir / "metadata" / "ebl-api"
            if not (ebl_repo_dir / ".git").exists():
                subprocess.run(
                    ["git", "clone", "--depth", "1",
                     "https://github.com/ElectronicBabylonianLiterature/ebl-api.git",
                     str(ebl_repo_dir)],
                    check=True,
                )
            logger.info("eBL repository cloned for reference")

        progress.set_source_state("ebl", {
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
        })
        return True

    except Exception as e:
        logger.error(f"Failed to download eBL data: {e}")
        progress.set_source_state("ebl", {"status": "failed", "error": str(e)})
        return False


# =============================================================================
# CAD Downloads
# =============================================================================

def download_cad_pdfs(
    progress: ProgressTracker,
    downloader: Downloader,
) -> bool:
    """Download Chicago Assyrian Dictionary PDFs from Internet Archive."""
    logger.info("=" * 60)
    logger.info("CAD (Chicago Assyrian Dictionary)")
    logger.info("=" * 60)

    cad_dir = BASE_DIR / "CAD" / "pdfs"
    state = progress.get_source_state("cad")

    if state.get("status") == "complete":
        logger.info("CAD PDFs already downloaded. Skipping.")
        return True

    if downloader.dry_run:
        logger.info("[DRY-RUN] Would download CAD PDFs from Internet Archive")
        return True

    # Get metadata for the CAD collection
    logger.info("Fetching CAD collection from Internet Archive...")

    # Known CAD volume identifiers on archive.org
    cad_volumes = get_cad_volume_identifiers()

    completed = set(state.get("completed", []))
    failed = []

    for volume_id in tqdm(cad_volumes, desc="Downloading CAD volumes"):
        if progress.interrupted:
            break

        if volume_id in completed:
            continue

        # Get download URL from archive.org metadata
        metadata_url = f"{ARCHIVE_ORG_BASE}/metadata/{volume_id}"
        metadata = downloader.get_json(metadata_url)

        if not metadata:
            failed.append(volume_id)
            continue

        # Find PDF file
        pdf_file = None
        for file_info in metadata.get("files", []):
            if file_info.get("name", "").endswith(".pdf"):
                pdf_file = file_info["name"]
                break

        if pdf_file:
            url = f"{ARCHIVE_ORG_BASE}/download/{volume_id}/{pdf_file}"
            dest = cad_dir / f"{volume_id}.pdf"

            if downloader.download_file(url, dest, desc=volume_id):
                completed.add(volume_id)
                if dest.exists():
                    progress.record_checksum(str(dest), compute_sha256(dest))
            else:
                failed.append(volume_id)
        else:
            logger.warning(f"No PDF found for {volume_id}")
            failed.append(volume_id)

        progress.set_source_state("cad", {
            "status": "partial",
            "completed": list(completed),
            "failed": failed,
        })

    status = "complete" if not failed else "partial"
    progress.set_source_state("cad", {
        "status": status,
        "completed": list(completed),
        "failed": failed,
        "timestamp": datetime.now().isoformat(),
    })

    logger.info(f"CAD: {len(completed)} volumes downloaded, {len(failed)} failed")
    return len(failed) == 0


def get_cad_volume_identifiers() -> list:
    """Return Internet Archive identifiers for CAD volumes."""
    # These are the known archive.org identifiers for CAD volumes
    return [
        "assyriandictiona0000unse_a1",
        "assyriandictiona0000unse_a2",
        "assyriandictiona0000unse_b",
        "assyriandictiona0000unse_d",
        "assyriandictiona0000unse_e",
        "assyriandictiona0000unse_g",
        "assyriandictiona0000unse_h",
        "assyriandictiona0000unse_i_j",
        "assyriandictiona0000unse_k",
        "assyriandictiona0000unse_l",
        "assyriandictiona0000unse_m1",
        "assyriandictiona0000unse_m2",
        "assyriandictiona0000unse_n1",
        "assyriandictiona0000unse_n2",
        "assyriandictiona0000unse_p",
        "assyriandictiona0000unse_q",
        "assyriandictiona0000unse_r",
        "assyriandictiona0000unse_s",
        "assyriandictiona0000unse_s_",  # shin
        "assyriandictiona0000unse_t",
        "assyriandictiona0000unse_t_",  # tet
        "assyriandictiona0000unse_u_w",
        "assyriandictiona0000unse_z",
    ]


# =============================================================================
# ML Model Downloads
# =============================================================================

def download_ml_models(
    progress: ProgressTracker,
    downloader: Downloader,
) -> bool:
    """Clone ML model repositories."""
    logger.info("=" * 60)
    logger.info("ML Models (DeepScribe, Akkademia)")
    logger.info("=" * 60)

    models_dir = BASE_DIR / "ML_MODELS"
    state = progress.get_source_state("ml_models")

    if state.get("status") == "complete":
        logger.info("ML models already downloaded. Skipping.")
        return True

    if downloader.dry_run:
        logger.info("[DRY-RUN] Would clone ML model repositories")
        return True

    models = [
        ("deepscribe", DEEPSCRIBE_REPO),
        ("akkademia", AKKADEMIA_REPO),
    ]

    completed = []
    failed = []

    for name, repo_url in models:
        dest_dir = models_dir / name

        try:
            if (dest_dir / ".git").exists():
                logger.info(f"Updating {name}...")
                subprocess.run(
                    ["git", "-C", str(dest_dir), "pull"],
                    check=True,
                )
            else:
                logger.info(f"Cloning {name}...")
                subprocess.run(
                    ["git", "clone", repo_url, str(dest_dir)],
                    check=True,
                )
            completed.append(name)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {name}: {e}")
            failed.append(name)

    status = "complete" if not failed else "partial"
    progress.set_source_state("ml_models", {
        "status": status,
        "completed": completed,
        "failed": failed,
        "timestamp": datetime.now().isoformat(),
    })

    logger.info(f"ML Models: {len(completed)} downloaded, {len(failed)} failed")
    return len(failed) == 0


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download cuneiform data from academic sources"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without downloading",
    )
    parser.add_argument(
        "--source",
        choices=["cdli", "oracc", "ebl", "cad", "ml", "all"],
        default="all",
        help="Download only specific source",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_IMAGE_LIMIT,
        help=f"Limit number of items (default: {DEFAULT_IMAGE_LIMIT})",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify checksums of existing downloads",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset progress and start fresh",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL verification (for servers with certificate issues)",
    )
    args = parser.parse_args()

    # Check if base directory exists
    if not BASE_DIR.exists():
        logger.error(f"Base directory not found: {BASE_DIR}")
        logger.error("Make sure the external drive is mounted.")
        sys.exit(1)

    # Create progress directory
    (BASE_DIR / "_progress").mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info("Cuneiform Data Download Script")
    logger.info("=" * 60)
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Mode: {'DRY-RUN' if args.dry_run else 'DOWNLOAD'}")
    logger.info(f"Source: {args.source}")
    logger.info(f"Image limit: {args.limit}")

    # Initialize progress tracker and downloader
    progress = ProgressTracker(PROGRESS_FILE, CHECKSUM_FILE)
    downloader = Downloader(
        dry_run=args.dry_run,
        verify_ssl=not args.no_verify_ssl
    )

    # Reset progress if requested
    if args.reset:
        logger.info("Resetting progress...")
        progress.state = {
            "started_at": datetime.now().isoformat(),
            "sources": {},
        }
        progress.checksums = {}
        progress.save()

    results = {}

    # Download sources based on selection
    sources_to_download = {
        "cdli": [
            ("cdli_metadata", lambda: download_cdli_metadata(progress, downloader)),
            ("cdli_catalogue", lambda: download_cdli_catalogue(progress, downloader, args.limit)),
            ("cdli_images", lambda: download_cdli_images(progress, downloader, args.limit)),
        ],
        "oracc": [
            ("oracc", lambda: download_oracc_projects(progress, downloader)),
        ],
        "ebl": [
            ("ebl", lambda: download_ebl_dataset(progress, downloader)),
        ],
        "cad": [
            ("cad", lambda: download_cad_pdfs(progress, downloader)),
        ],
        "ml": [
            ("ml_models", lambda: download_ml_models(progress, downloader)),
        ],
    }

    if args.source == "all":
        sources = ["cdli", "oracc", "ebl", "cad", "ml"]
    else:
        sources = [args.source]

    for source in sources:
        if progress.interrupted:
            break
        for name, func in sources_to_download[source]:
            if progress.interrupted:
                break
            results[name] = func()

    # Summary
    logger.info("=" * 60)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 60)
    for name, success in results.items():
        status = "SUCCESS" if success else "FAILED/PARTIAL"
        logger.info(f"  {name}: {status}")

    # Save final state
    progress.save()

    logger.info("")
    logger.info(f"Progress saved to: {PROGRESS_FILE}")
    logger.info(f"Error log: {ERROR_LOG}")

    # Exit with error if any downloads failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
