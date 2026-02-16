#!/usr/bin/env python3
"""
Validate data completeness for Glintstone project.
Checks all data sources and reports status.
"""

import os
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DOWNLOADS_DIR = BASE_DIR / "downloads"

def get_file_size(path: Path) -> str:
    """Get human-readable file size."""
    if not path.exists():
        return "MISSING"
    size = path.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def count_files(path: Path, pattern: str = "*") -> int:
    """Count files matching pattern."""
    if not path.exists():
        return 0
    return len(list(path.glob(pattern)))

def check_json_valid(path: Path) -> tuple[bool, int]:
    """Check if JSON file is valid and return entry count."""
    if not path.exists():
        return False, 0
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            if 'entries' in data:
                return True, len(data['entries'])
            elif 'data' in data:
                return True, len(data['data'])
            elif 'signs' in data:
                return True, len(data['signs'])
            elif 'members' in data:
                return True, len(data['members'])
            return True, len(data)
        elif isinstance(data, list):
            return True, len(data)
        return True, 0
    except:
        return False, 0

def main():
    print("=" * 70)
    print("GLINTSTONE DATA COMPLETENESS REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    # CDLI Data
    print("\n## CDLI (Cuneiform Digital Library Initiative)")
    print("-" * 50)

    catalog_path = DOWNLOADS_DIR / "CDLI/catalogue/batch-00000.json"
    valid, count = check_json_valid(catalog_path)
    print(f"  Catalog: {get_file_size(catalog_path)} - {count} tablets" if valid else "  Catalog: INVALID")

    images_dir = DOWNLOADS_DIR / "CDLI/images/photo"
    image_count = count_files(images_dir, "*.jpg") + count_files(images_dir, "*.JPG")
    print(f"  Images: {image_count} photos")

    # ORACC Data
    print("\n## ORACC (Open Richly Annotated Cuneiform Corpus)")
    print("-" * 50)

    # DCCLT
    dcclt_gloss_dir = DOWNLOADS_DIR / "ORACC/dcclt/extracted/dcclt"
    if dcclt_gloss_dir.exists():
        sux_valid, sux_count = check_json_valid(dcclt_gloss_dir / "gloss-sux.json")
        akk_valid, akk_count = check_json_valid(dcclt_gloss_dir / "gloss-akk.json")
        corpus_valid, corpus_count = check_json_valid(dcclt_gloss_dir / "corpus.json")

        print(f"  DCCLT Sumerian Glossary: {get_file_size(dcclt_gloss_dir / 'gloss-sux.json')} - {sux_count} entries")
        print(f"  DCCLT Akkadian Glossary: {get_file_size(dcclt_gloss_dir / 'gloss-akk.json')} - {akk_count} entries")
        print(f"  DCCLT Corpus Index: {corpus_count} texts")

        corpusjson_dir = dcclt_gloss_dir / "corpusjson"
        if corpusjson_dir.exists():
            corpus_files = count_files(corpusjson_dir, "*.json")
            print(f"  DCCLT Corpus JSON Files: {corpus_files} tablets")
    else:
        print("  DCCLT: Not extracted - check glossaries folder")

    # OGSL Sign List
    ogsl_path = DOWNLOADS_DIR / "ORACC/ogsl/json/ogsl/ogsl-sl.json"
    ogsl_valid, ogsl_count = check_json_valid(ogsl_path)
    print(f"  OGSL Sign List: {get_file_size(ogsl_path)} - {ogsl_count} signs" if ogsl_valid else "  OGSL: INVALID")

    # ML Models
    print("\n## Machine Learning Models")
    print("-" * 50)

    # Akkademia
    akk_model = BASE_DIR / "ML_MODELS/akkademia/akkadian/output/bilstm_model_linux.pkl"
    print(f"  Akkademia BiLSTM: {get_file_size(akk_model)}")

    akk_hmm = BASE_DIR / "ML_MODELS/akkademia/akkadian/output/hmm_model.pkl"
    print(f"  Akkademia HMM: {get_file_size(akk_hmm)}")

    akk_memm = BASE_DIR / "ML_MODELS/akkademia/akkadian/output/memm_model.pkl"
    print(f"  Akkademia MEMM: {get_file_size(akk_memm)}")

    # DeepScribe
    ds_classifier = BASE_DIR / "ML_MODELS/deepscribe/artifacts/trained_classifier_public.ckpt"
    print(f"  DeepScribe Classifier: {get_file_size(ds_classifier)}")

    ds_detector = BASE_DIR / "ML_MODELS/deepscribe/artifacts/trained_detector_public.ckpt"
    print(f"  DeepScribe Detector: {get_file_size(ds_detector)}")

    # eBL
    ebl_detr = BASE_DIR / "ML_MODELS/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth"
    print(f"  eBL DETR (173 classes): {get_file_size(ebl_detr)}")

    # ePSD2
    print("\n## ePSD2 (Pennsylvania Sumerian Dictionary)")
    print("-" * 50)

    epsd_unicode = DOWNLOADS_DIR / "ePSD2/unicode"
    if epsd_unicode.exists():
        unicode_files = count_files(epsd_unicode, "*")
        print(f"  Unicode data files: {unicode_files}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    status_items = [
        ("CDLI Catalog", catalog_path.exists() and catalog_path.stat().st_size > 1000),
        ("CDLI Images", image_count > 0),
        ("DCCLT Glossaries", dcclt_gloss_dir.exists()),
        ("OGSL Sign List", ogsl_path.exists() and ogsl_path.stat().st_size > 1000),
        ("Akkademia Models", akk_model.exists()),
        ("DeepScribe Models", ds_classifier.exists()),
        ("eBL DETR Model", ebl_detr.exists()),
    ]

    for name, status in status_items:
        icon = "✓" if status else "✗"
        print(f"  {icon} {name}")

    complete = sum(1 for _, s in status_items if s)
    total = len(status_items)
    print(f"\nData Completeness: {complete}/{total} ({100*complete/total:.0f}%)")

if __name__ == "__main__":
    main()
