#!/usr/bin/env python3
"""
Download ORACC subproject ZIPs that contain corpus data.

Portal projects (saao, riao, rinap, ribo) distribute their corpus texts
across subproject ZIPs. This script downloads and extracts them to the
expected directory structure for import by 11_import_lemmatizations.py.

URL patterns:
  Top-level:  http://oracc.museum.upenn.edu/json/{project}.zip
  Subproject: http://oracc.museum.upenn.edu/json/{parent}-{sub}.zip

Usage:
    python 00_download_oracc_subprojects.py [--dry-run]
"""

import argparse
import os
import subprocess
import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources" / "ORACC"
ORACC_JSON_URL = "http://oracc.museum.upenn.edu/json"

# Subprojects to download: (parent, subproject_name)
# These are portal projects whose corpus data lives in subproject ZIPs.
SUBPROJECTS = {
    "saao": [
        "saa01",
        "saa02",
        "saa03",
        "saa04",
        "saa05",
        "saa06",
        "saa07",
        "saa08",
        "saa09",
        "saa10",
        "saa11",
        "saa12",
        "saa13",
        "saa14",
        "saa15",
        "saa16",
        "saa17",
        "saa18",
        "saa19",
        "saa20",
        "saa21",
    ],
    "riao": ["ria1", "ria2", "ria3", "ria4", "ria5"],
    "rinap": ["rinap2", "rinap3", "rinap4", "rinap5"],
    "ribo": [
        "babylon2",
        "babylon3",
        "babylon4",
        "babylon5",
        "babylon6",
        "babylon7",
        "babylon8",
        "babylon10",
    ],
}

# Top-level projects to retry (previous downloads failed)
TOPLEVEL_RETRY = ["cams", "etcsl", "rime", "ctij"]

REQUEST_DELAY = 1.0  # seconds between requests


def download_zip(url: str, timeout: int = 120) -> bytes | None:
    """Download a ZIP file via curl (handles SSL redirects), return bytes or None."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

        result = subprocess.run(
            ["curl", "-sL", "-o", tmp_path, "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        http_code = result.stdout.strip()
        if http_code != "200":
            print(f"    HTTP {http_code}")
            os.unlink(tmp_path)
            return None

        data = Path(tmp_path).read_bytes()
        os.unlink(tmp_path)

        if len(data) < 1000 or data[:2] != b"PK":
            print(f"    SKIP: Not a valid ZIP ({len(data)} bytes)")
            return None
        return data
    except subprocess.TimeoutExpired:
        print(f"    Timeout after {timeout}s")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def extract_zip(zip_data: bytes, dest_dir: Path) -> int:
    """Extract ZIP to destination, return count of corpus JSON files."""
    with zipfile.ZipFile(BytesIO(zip_data)) as zf:
        corpus_files = [
            f for f in zf.namelist() if "corpusjson/" in f and f.endswith(".json")
        ]
        zf.extractall(dest_dir)
        return len(corpus_files)


def download_subproject(parent: str, sub: str, dry_run: bool = False) -> bool:
    """Download and extract a single subproject ZIP."""
    # Expected extraction target
    target_dir = ORACC_BASE / parent / "json" / parent / sub / "corpusjson"
    if target_dir.exists() and list(target_dir.glob("*.json")):
        count = len(list(target_dir.glob("*.json")))
        print(f"  {parent}/{sub}: already extracted ({count} files)")
        return True

    url = f"{ORACC_JSON_URL}/{parent}-{sub}.zip"
    print(f"  {parent}/{sub}: downloading {url}")

    if dry_run:
        print(f"    [DRY RUN] would download to {target_dir}")
        return True

    zip_data = download_zip(url)
    if not zip_data:
        # Try alternate URL pattern
        alt_url = f"{ORACC_JSON_URL}/{parent}/{sub}.zip"
        print(f"    Trying alternate: {alt_url}")
        zip_data = download_zip(alt_url)

    if not zip_data:
        return False

    # Extract to project directory
    extract_dir = ORACC_BASE / parent / "json" / parent
    extract_dir.mkdir(parents=True, exist_ok=True)
    corpus_count = extract_zip(zip_data, extract_dir)
    print(f"    Extracted: {corpus_count} corpus files")

    time.sleep(REQUEST_DELAY)
    return corpus_count > 0


def download_toplevel(project: str, dry_run: bool = False) -> bool:
    """Download and extract a top-level project ZIP."""
    target_dir = ORACC_BASE / project / "json" / project / "corpusjson"
    if target_dir.exists() and list(target_dir.glob("*.json")):
        count = len(list(target_dir.glob("*.json")))
        print(f"  {project}: already extracted ({count} files)")
        return True

    url = f"{ORACC_JSON_URL}/{project}.zip"
    print(f"  {project}: downloading {url}")

    if dry_run:
        print(f"    [DRY RUN] would download to {target_dir}")
        return True

    zip_data = download_zip(url)
    if not zip_data:
        return False

    # Save ZIP and extract
    zip_path = ORACC_BASE / project / f"{project}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path.write_bytes(zip_data)

    extract_dir = ORACC_BASE / project / "json"
    extract_dir.mkdir(parents=True, exist_ok=True)
    corpus_count = extract_zip(zip_data, extract_dir)
    print(
        f"    Extracted: {corpus_count} corpus files (ZIP saved: {len(zip_data) / 1024 / 1024:.1f}MB)"
    )

    time.sleep(REQUEST_DELAY)
    return corpus_count > 0


def main():
    parser = argparse.ArgumentParser(description="Download ORACC subproject ZIPs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--project", help="Only download this parent project")
    args = parser.parse_args()

    print("=" * 60)
    print("ORACC SUBPROJECT DOWNLOAD")
    print(f"  Base: {ORACC_BASE}")
    print("=" * 60)

    results = {"success": 0, "failed": 0, "skipped": 0}

    # Subproject downloads
    for parent, subs in SUBPROJECTS.items():
        if args.project and parent != args.project:
            continue

        print(f"\n--- {parent.upper()} ({len(subs)} subprojects) ---")
        for sub in subs:
            ok = download_subproject(parent, sub, args.dry_run)
            if ok:
                results["success"] += 1
            else:
                results["failed"] += 1

    # Top-level retries
    if not args.project:
        print("\n--- TOP-LEVEL RETRIES ---")
        for project in TOPLEVEL_RETRY:
            ok = download_toplevel(project, args.dry_run)
            if ok:
                results["success"] += 1
            else:
                results["failed"] += 1

    print(f"\n{'=' * 60}")
    print(f"  Success: {results['success']}")
    print(f"  Failed:  {results['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
