#!/usr/bin/env python3
"""
Build sign mapping JSON from checkpoint metadata and ebl.txt.
Maps class_id -> { name, unicode, abz_code }
"""

import json
import torch
from pathlib import Path


def load_ebl_mapping(ebl_path: Path) -> dict:
    """Load ebl.txt and create sign_name -> {abz, unicode} mapping."""
    mapping = {}
    with open(ebl_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                sign_name = parts[0]
                abz_code = parts[1]
                unicode_char = parts[2] if parts[2] != 'None' else None
                mapping[sign_name] = {
                    'abz': abz_code,
                    'unicode': unicode_char
                }
    return mapping


def build_class_mapping(checkpoint_path: Path, ebl_mapping: dict) -> list:
    """Build class mapping from checkpoint metadata."""
    print(f"Loading checkpoint: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)

    # Extract class names from meta
    meta = checkpoint.get('meta', {})
    dataset_meta = meta.get('dataset_meta', {})
    class_names = dataset_meta.get('classes', [])

    print(f"Found {len(class_names)} classes")

    # Build mapping
    class_mapping = []
    for i, name in enumerate(class_names):
        entry = {
            'id': i,
            'name': name,
            'unicode': None,
            'abz': None
        }

        # Try to find in ebl mapping
        if name in ebl_mapping:
            entry['unicode'] = ebl_mapping[name]['unicode']
            entry['abz'] = ebl_mapping[name]['abz']
        else:
            # Handle compound signs like |U.GUD|
            print(f"  Class '{name}' not found in ebl mapping")

        class_mapping.append(entry)

    return class_mapping


def main():
    checkpoint_path = Path("/Volumes/Portable Storage/CUNEIFORM/models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth")
    ebl_path = Path("/Volumes/Portable Storage/CUNEIFORM/downloads/ebl-annotations/cuneiform_ocr_data/sign_mappings/ebl.txt")
    output_path = Path(__file__).parent / "sign_mapping.json"

    # Load ebl mapping
    print(f"Loading EBL mapping from: {ebl_path}")
    ebl_mapping = load_ebl_mapping(ebl_path)
    print(f"Loaded {len(ebl_mapping)} sign mappings from ebl.txt")

    # Build class mapping
    class_mapping = build_class_mapping(checkpoint_path, ebl_mapping)

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(class_mapping, f, ensure_ascii=False, indent=2)

    print(f"\nSaved mapping to: {output_path}")

    # Print summary
    matched = sum(1 for c in class_mapping if c['unicode'] is not None)
    print(f"Matched {matched}/{len(class_mapping)} classes to Unicode")


if __name__ == "__main__":
    main()
