#!/usr/bin/env python3
"""
Download ORACC glossaries for Glintstone project.
Fetches Sumerian, Akkadian (all variants), and other language glossaries.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
ORACC_BASE = "http://oracc.museum.upenn.edu"

# Glossary sources - project and languages
GLOSSARY_SOURCES = {
    "epsd2": {
        "languages": ["sux", "akk", "qpn"],
        "description": "Electronic Pennsylvania Sumerian Dictionary"
    },
    "dcclt": {
        "languages": ["sux", "akk", "akk-x-oldbab", "akk-x-stdbab", "akk-x-mbperi", "qpn", "xhu"],
        "description": "Digital Corpus of Cuneiform Lexical Texts"
    },
    "rinap": {
        "languages": ["akk", "akk-x-stdbab", "akk-x-neoass", "sux", "qpn"],
        "description": "Royal Inscriptions of the Neo-Assyrian Period"
    },
    "ribo": {
        "languages": ["akk", "akk-x-stdbab", "akk-x-neobab", "sux", "qpn"],
        "description": "Royal Inscriptions of Babylonia Online"
    },
    "saao": {
        "languages": ["akk", "akk-x-neoass", "akk-x-neobab", "akk-x-stdbab", "sux", "qpn"],
        "description": "State Archives of Assyria Online"
    }
}

# Alternative download URLs (some projects have different URL patterns)
ALTERNATIVE_URLS = {
    "epsd2": "http://oracc.org/epsd2/json",
    "dcclt": "http://oracc.org/dcclt/json",
    "rinap": "http://oracc.org/rinap/json",
    "ribo": "http://oracc.org/ribo/json",
    "saao": "http://oracc.org/saao/json"
}

def download_glossary(project: str, language: str, output_dir: Path) -> bool:
    """Download a single glossary file."""
    filename = f"gloss-{language}.json"
    output_path = output_dir / filename

    # Try multiple URL patterns
    urls_to_try = [
        f"{ORACC_BASE}/{project}/json/{project}/{filename}",
        f"{ALTERNATIVE_URLS.get(project, ORACC_BASE)}/{filename}",
        f"http://oracc.org/{project}/json/{filename}",
        f"http://build-oracc.museum.upenn.edu/{project}/json/{filename}"
    ]

    for url in urls_to_try:
        try:
            print(f"  Trying: {url}")
            response = requests.get(url, timeout=60)

            if response.status_code == 200:
                # Validate it's actual JSON
                try:
                    data = response.json()
                    if data and (isinstance(data, dict) or isinstance(data, list)):
                        # Check if it has expected glossary structure
                        if isinstance(data, dict) and ("entries" in data or "instances" in data or len(data) > 0):
                            output_path.write_bytes(response.content)
                            size_kb = len(response.content) / 1024
                            print(f"  ✓ Downloaded {filename} ({size_kb:.1f} KB)")
                            return True
                        elif isinstance(data, list) and len(data) > 0:
                            output_path.write_bytes(response.content)
                            size_kb = len(response.content) / 1024
                            print(f"  ✓ Downloaded {filename} ({size_kb:.1f} KB)")
                            return True
                except json.JSONDecodeError:
                    continue

        except requests.RequestException as e:
            continue

    print(f"  ✗ Failed to download {filename}")
    return False

def download_project_glossaries(project: str, languages: list, description: str) -> dict:
    """Download all glossaries for a project."""
    print(f"\n{'='*60}")
    print(f"Project: {project} - {description}")
    print(f"{'='*60}")

    output_dir = BASE_DIR / "ORACC" / project / "glossaries"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {"success": [], "failed": []}

    for lang in languages:
        time.sleep(0.5)  # Rate limiting
        if download_glossary(project, lang, output_dir):
            results["success"].append(lang)
        else:
            results["failed"].append(lang)

    return results

def download_epsd2_main():
    """Download main ePSD2 dictionary data."""
    print(f"\n{'='*60}")
    print("Downloading ePSD2 Main Dictionary")
    print(f"{'='*60}")

    output_dir = BASE_DIR / "ePSD2" / "dictionary"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to get the main dictionary files
    urls = [
        ("http://oracc.org/epsd2/json/epsd2/gloss-sux.json", "gloss-sux.json"),
        ("http://oracc.org/epsd2/json/gloss-sux.json", "gloss-sux.json"),
        ("http://build-oracc.museum.upenn.edu/epsd2/signlist.json", "signlist.json"),
    ]

    for url, filename in urls:
        try:
            print(f"  Trying: {url}")
            response = requests.get(url, timeout=120)
            if response.status_code == 200 and len(response.content) > 100:
                output_path = output_dir / filename
                output_path.write_bytes(response.content)
                size_kb = len(response.content) / 1024
                print(f"  ✓ Downloaded {filename} ({size_kb:.1f} KB)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

def main():
    print("=" * 60)
    print("ORACC Glossary Downloader for Glintstone")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    all_results = {}

    # Download glossaries for each project
    for project, config in GLOSSARY_SOURCES.items():
        results = download_project_glossaries(
            project,
            config["languages"],
            config["description"]
        )
        all_results[project] = results

    # Download main ePSD2 dictionary
    download_epsd2_main()

    # Summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")

    total_success = 0
    total_failed = 0

    for project, results in all_results.items():
        success_count = len(results["success"])
        failed_count = len(results["failed"])
        total_success += success_count
        total_failed += failed_count

        status = "✓" if failed_count == 0 else "⚠"
        print(f"{status} {project}: {success_count} success, {failed_count} failed")
        if results["failed"]:
            print(f"   Failed: {', '.join(results['failed'])}")

    print(f"\nTotal: {total_success} downloaded, {total_failed} failed")
    print(f"Completed: {datetime.now().isoformat()}")

    # Save results log
    log_path = BASE_DIR / "_logs" / "glossary_download.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    print(f"\nLog saved to: {log_path}")

if __name__ == "__main__":
    main()
