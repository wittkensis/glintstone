#!/usr/bin/env python3
"""
Download CAD PDF files from ISAC website.

Usage:
    python download_cad_pdfs.py [--volume VOLUME] [--force]

Options:
    --volume    Download specific volume only (e.g., 'a1', 'g', 'k')
    --force     Re-download even if file exists
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# CAD volume metadata
CAD_VOLUMES = [
    {"id": "a1", "file": "cad_a1.pdf", "pages": 392, "letter": "A (Part 1)"},
    {"id": "a2", "file": "cad_a2.pdf", "pages": 531, "letter": "A (Part 2)"},
    {"id": "b", "file": "cad_b.pdf", "pages": 366, "letter": "B"},
    {"id": "d", "file": "cad_d.pdf", "pages": 203, "letter": "D"},
    {"id": "e", "file": "cad_e.pdf", "pages": 435, "letter": "E"},
    {"id": "g", "file": "cad_g.pdf", "pages": 158, "letter": "G"},
    {"id": "h", "file": "cad_h.pdf", "pages": 266, "letter": "H"},
    {"id": "i-j", "file": "cad_i-j.pdf", "pages": 331, "letter": "I/J"},
    {"id": "k", "file": "cad_k.pdf", "pages": 617, "letter": "K"},
    {"id": "l", "file": "cad_l.pdf", "pages": 259, "letter": "L"},
    {"id": "m1", "file": "cad_m1.pdf", "pages": 400, "letter": "M (Part 1)"},
    {"id": "m2", "file": "cad_m2.pdf", "pages": 365, "letter": "M (Part 2)"},
    {"id": "n1", "file": "cad_n1.pdf", "pages": 400, "letter": "N (Part 1)"},
    {"id": "n2", "file": "cad_n2.pdf", "pages": 339, "letter": "N (Part 2)"},
    {"id": "p", "file": "cad_p.pdf", "pages": 559, "letter": "P"},
    {"id": "q", "file": "cad_q.pdf", "pages": 332, "letter": "Q"},
    {"id": "r", "file": "cad_r.pdf", "pages": 441, "letter": "R"},
    {"id": "s", "file": "cad_s.pdf", "pages": 428, "letter": "S"},
    {"id": "s_tsade", "file": "cad_s_tsade.pdf", "pages": 262, "letter": "Ṣ (Tsade)"},
    {"id": "s_shin_1", "file": "cad_s_shin_1.pdf", "pages": 500, "letter": "Š (Part 1)"},
    {"id": "s_shin_2", "file": "cad_s_shin_2.pdf", "pages": 450, "letter": "Š (Part 2)"},
    {"id": "s_shin_3", "file": "cad_s_shin_3.pdf", "pages": 415, "letter": "Š (Part 3)"},
    {"id": "t", "file": "cad_t.pdf", "pages": 500, "letter": "T"},
    {"id": "tet", "file": "cad_tet.pdf", "pages": 167, "letter": "Ṭ (Tet)"},
    {"id": "u_w", "file": "cad_u_w.pdf", "pages": 411, "letter": "U/W"},
    {"id": "z", "file": "cad_z.pdf", "pages": 170, "letter": "Z"},
]

BASE_URL = "https://isac.uchicago.edu/sites/default/files/uploads/shared/docs/"


def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_progress(count, block_size, total_size):
    """Show download progress."""
    percent = min(100, int(count * block_size * 100 / total_size))
    sys.stdout.write(f"\r  Progress: {percent}%")
    sys.stdout.flush()


def download_volume(volume: dict, output_dir: Path, force: bool = False) -> bool:
    """
    Download a single CAD volume.

    Returns True if downloaded, False if skipped.
    """
    output_path = output_dir / volume["file"]
    url = BASE_URL + volume["file"]

    # Check if already downloaded
    if output_path.exists() and not force:
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Already exists: {volume['file']} ({size_mb:.1f} MB)")
        return False

    print(f"  Downloading: {volume['file']}...")

    try:
        urlretrieve(url, output_path, reporthook=download_progress)
        print()  # newline after progress

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Downloaded: {size_mb:.1f} MB")
        return True

    except HTTPError as e:
        print(f"\n  ERROR: HTTP {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"\n  ERROR: {e.reason}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download CAD PDF files")
    parser.add_argument("--volume", "-v", help="Download specific volume only")
    parser.add_argument("--force", "-f", action="store_true", help="Re-download existing files")
    parser.add_argument("--list", "-l", action="store_true", help="List available volumes")
    args = parser.parse_args()

    # List mode
    if args.list:
        print("\nAvailable CAD volumes:")
        print("-" * 50)
        total_pages = 0
        for vol in CAD_VOLUMES:
            print(f"  {vol['id']:12} {vol['letter']:15} {vol['pages']:4} pages")
            total_pages += vol['pages']
        print("-" * 50)
        print(f"  {'TOTAL':12} {'':15} {total_pages:4} pages")
        print(f"\n  26 PDF files")
        return

    # Determine output directory
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / "pdfs"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("CAD PDF DOWNLOAD")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print()

    # Filter volumes if specific one requested
    volumes = CAD_VOLUMES
    if args.volume:
        vol_id = args.volume.lower()
        volumes = [v for v in CAD_VOLUMES if v["id"] == vol_id]
        if not volumes:
            print(f"ERROR: Unknown volume '{args.volume}'")
            print("Use --list to see available volumes")
            return 1

    # Download
    downloaded = 0
    skipped = 0
    errors = 0

    for i, volume in enumerate(volumes, 1):
        print(f"\n[{i}/{len(volumes)}] {volume['letter']}")

        try:
            if download_volume(volume, output_dir, args.force):
                downloaded += 1
            else:
                skipped += 1
            time.sleep(0.5)  # Be polite to the server
        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped:    {skipped}")
    print(f"  Errors:     {errors}")

    # Save manifest
    manifest_path = output_dir / "manifest.json"
    manifest = {
        "volumes": CAD_VOLUMES,
        "base_url": BASE_URL,
        "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest saved to: {manifest_path}")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
