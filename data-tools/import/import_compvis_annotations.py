#!/usr/bin/env python3
"""
Import sign annotations from CompVis cuneiform-sign-detection-dataset.

Dataset: https://github.com/CompVis/cuneiform-sign-detection-dataset
Paper: Deep Learning of Cuneiform Sign Detection with Weak Supervision (PLOS ONE, 2020)

The dataset provides bounding box annotations for 81 tablets with 8,109 annotated signs.
Coordinates are provided as both composite-absolute (bbox) and segment-relative (relative_bbox).
We use composite-absolute coordinates since CDLI displays full composite images.
"""

import csv
import json
import sqlite3
import os
import re
from pathlib import Path
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COMPVIS_DIR = PROJECT_ROOT / "downloads" / "compvis-annotations"
DB_PATH = PROJECT_ROOT / "database" / "glintstone.db"

# Annotation files to process
ANNOTATION_FILES = [
    "bbox_annotations_test_full.csv",
    "bbox_annotations_train_full.csv",
    "bbox_annotations_saa05.csv",
    "bbox_annotations_saa06.csv",
    "bbox_annotations_saa09.csv",
]

# Segment metadata files for getting surface info and segment dimensions
SEGMENT_FILES = [
    "tablet_segments_test.csv",
    "tablet_segments_train.csv",
    "tablet_segments_saa05.csv",
    "tablet_segments_saa06.csv",
    "tablet_segments_saa09.csv",
]


def load_segments(compvis_dir: Path) -> tuple:
    """Load segment metadata and compute composite dimensions for each tablet.

    Returns:
        segments: {(tablet_id, segm_idx): {view_desc, ...}}
        composite_dims: {tablet_id: (width, height)} - dimensions of full composite image
    """
    segments = {}  # {(tablet_id, segm_idx): {view_desc, ...}}
    composite_dims = {}  # {tablet_id: (max_x, max_y)}

    for filename in SEGMENT_FILES:
        filepath = compvis_dir / "segments" / filename
        if not filepath.exists():
            print(f"  Warning: {filename} not found")
            continue

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tablet_id = row['tablet_CDLI']
                segm_idx = int(row['segm_idx'])

                # Parse bbox [x1, y1, x2, y2] - segment bounds within composite
                bbox_str = row.get('bbox', '').strip()
                if bbox_str:
                    try:
                        bbox = json.loads(bbox_str.replace("'", '"'))
                        x2, y2 = bbox[2], bbox[3]

                        # Track max bounds to determine composite dimensions
                        if tablet_id in composite_dims:
                            curr_x, curr_y = composite_dims[tablet_id]
                            composite_dims[tablet_id] = (max(curr_x, x2), max(curr_y, y2))
                        else:
                            composite_dims[tablet_id] = (x2, y2)
                    except:
                        pass

                segments[(tablet_id, segm_idx)] = {
                    'view_desc': row.get('view_desc', ''),
                }

    return segments, composite_dims


def map_museum_to_pnumber(conn: sqlite3.Connection) -> dict:
    """Create mapping from museum numbers to P-numbers."""
    cursor = conn.cursor()
    cursor.execute("SELECT p_number, museum_no FROM artifacts WHERE museum_no IS NOT NULL")

    mapping = {}
    for p_number, museum_no in cursor.fetchall():
        if museum_no:
            # Normalize: remove spaces, convert to uppercase
            normalized = museum_no.replace(' ', '').upper()
            mapping[normalized] = p_number

    return mapping


def normalize_tablet_id(tablet_id: str) -> tuple:
    """
    Normalize tablet ID and determine if it's a P-number or museum number.
    Returns (normalized_id, is_pnumber)
    """
    tablet_id = tablet_id.strip()

    # Already a P-number
    if re.match(r'^P\d+', tablet_id):
        # Extract just the P-number part (handle cases like P336663b)
        match = re.match(r'^(P\d+)', tablet_id)
        return match.group(1), True

    # Museum number - normalize (remove suffixes like Vs, Rs)
    normalized = re.sub(r'(Vs|Rs|Obv|Rev)$', '', tablet_id)
    normalized = normalized.replace(' ', '').upper()
    return normalized, False


def parse_bbox(bbox_str: str) -> tuple:
    """Parse bbox string like '[910, 738, 978, 787]' to (x1, y1, x2, y2)."""
    try:
        bbox = json.loads(bbox_str.replace("'", '"'))
        return tuple(bbox)
    except:
        return None


def import_compvis_annotations():
    """Import CompVis annotations into the database."""
    print("=" * 60)
    print("CompVis Sign Annotation Importer")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load segment metadata and compute composite dimensions
    print("\n1. Loading segment metadata...")
    segments, composite_dims = load_segments(COMPVIS_DIR)
    print(f"   Loaded {len(segments)} segment records")
    print(f"   Computed composite dimensions for {len(composite_dims)} tablets")

    # Create museum number mapping
    print("\n2. Creating museum number mapping...")
    museum_mapping = map_museum_to_pnumber(conn)
    print(f"   Found {len(museum_mapping)} museum number mappings")

    # Load valid P-numbers from artifacts table
    print("\n2b. Loading valid P-numbers from artifacts...")
    cursor.execute("SELECT p_number FROM artifacts")
    valid_pnumbers = {row[0] for row in cursor.fetchall()}
    print(f"   Found {len(valid_pnumbers)} valid P-numbers")

    # Clear existing CompVis annotations
    print("\n3. Clearing existing CompVis annotations...")
    cursor.execute("DELETE FROM sign_annotations WHERE source = 'compvis'")
    print(f"   Deleted {cursor.rowcount} existing records")

    # Process annotation files
    print("\n4. Processing annotation files...")

    total_imported = 0
    total_skipped = 0
    tablets_imported = set()
    tablets_skipped = set()

    for filename in ANNOTATION_FILES:
        filepath = COMPVIS_DIR / "annotations" / filename
        if not filepath.exists():
            print(f"   Skipping {filename} (not found)")
            continue

        print(f"\n   Processing {filename}...")
        file_imported = 0
        file_skipped = 0

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                tablet_id = row.get('tablet_CDLI', '').strip()
                if not tablet_id:
                    continue

                # Normalize and resolve tablet ID
                normalized_id, is_pnumber = normalize_tablet_id(tablet_id)

                if is_pnumber:
                    p_number = normalized_id
                else:
                    # Look up museum number
                    p_number = museum_mapping.get(normalized_id)
                    if not p_number:
                        # Try variations
                        for variant in [normalized_id, normalized_id.replace('0', '')]:
                            if variant in museum_mapping:
                                p_number = museum_mapping[variant]
                                break

                if not p_number:
                    tablets_skipped.add(tablet_id)
                    file_skipped += 1
                    continue

                # Validate P-number exists in our artifacts table
                if p_number not in valid_pnumbers:
                    tablets_skipped.add(f"{tablet_id} ({p_number} not in artifacts)")
                    file_skipped += 1
                    continue

                # Get segment info for surface detection
                segm_idx = int(row.get('segm_idx', 0))
                segment_info = segments.get((tablet_id, segm_idx), {})

                # Parse composite-absolute bbox (not segment-relative)
                bbox_str = row.get('bbox', '')
                bbox = parse_bbox(bbox_str)

                if not bbox:
                    file_skipped += 1
                    continue

                x1, y1, x2, y2 = bbox

                # Get composite dimensions for this tablet
                composite_w, composite_h = composite_dims.get(tablet_id, (None, None))

                if composite_w and composite_h and composite_w > 0 and composite_h > 0:
                    # Convert to percentage of full composite image
                    bbox_x = (x1 / composite_w) * 100
                    bbox_y = (y1 / composite_h) * 100
                    bbox_width = ((x2 - x1) / composite_w) * 100
                    bbox_height = ((y2 - y1) / composite_h) * 100
                else:
                    # No composite dimensions - skip this annotation
                    file_skipped += 1
                    continue

                # Clamp to valid range
                bbox_x = max(0, min(100, bbox_x))
                bbox_y = max(0, min(100, bbox_y))
                bbox_width = max(0, min(100 - bbox_x, bbox_width))
                bbox_height = max(0, min(100 - bbox_y, bbox_height))

                # Get sign label (MZL number)
                sign_label = row.get('mzl_label', row.get('train_label', ''))

                # Get surface from segment info
                surface = segment_info.get('view_desc', '').lower()
                if surface in ['obv', 'obverse']:
                    surface = 'obverse'
                elif surface in ['rev', 'reverse']:
                    surface = 'reverse'
                elif not surface:
                    surface = None

                batch.append((
                    p_number,
                    str(sign_label) if sign_label else None,
                    bbox_x,
                    bbox_y,
                    bbox_width,
                    bbox_height,
                    None,  # confidence (not provided in CompVis)
                    surface,
                    None,  # atf_line
                    'compvis',
                    'photo',
                    int(composite_w),  # ref_image_width
                    int(composite_h),  # ref_image_height
                ))

                tablets_imported.add(p_number)
                file_imported += 1

                # Batch insert
                if len(batch) >= 1000:
                    cursor.executemany("""
                        INSERT INTO sign_annotations
                        (p_number, sign_label, bbox_x, bbox_y, bbox_width, bbox_height,
                         confidence, surface, atf_line, source, image_type,
                         ref_image_width, ref_image_height)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    batch = []

            # Insert remaining
            if batch:
                cursor.executemany("""
                    INSERT INTO sign_annotations
                    (p_number, sign_label, bbox_x, bbox_y, bbox_width, bbox_height,
                     confidence, surface, atf_line, source, image_type,
                     ref_image_width, ref_image_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)

        total_imported += file_imported
        total_skipped += file_skipped
        print(f"      Imported: {file_imported}, Skipped: {file_skipped}")

    conn.commit()

    # Summary
    print("\n" + "=" * 60)
    print("Import Complete")
    print("=" * 60)
    print(f"\nTotal annotations imported: {total_imported}")
    print(f"Total annotations skipped: {total_skipped}")
    print(f"Unique tablets with annotations: {len(tablets_imported)}")

    if tablets_skipped:
        print(f"\nTablets skipped (no P-number mapping): {len(tablets_skipped)}")
        for t in sorted(tablets_skipped)[:10]:
            print(f"  - {t}")
        if len(tablets_skipped) > 10:
            print(f"  ... and {len(tablets_skipped) - 10} more")

    # Verify import
    cursor.execute("SELECT COUNT(*) FROM sign_annotations WHERE source = 'compvis'")
    count = cursor.fetchone()[0]
    print(f"\nDatabase verification: {count} CompVis annotations in database")

    cursor.execute("""
        SELECT COUNT(DISTINCT p_number) FROM sign_annotations WHERE source = 'compvis'
    """)
    tablet_count = cursor.fetchone()[0]
    print(f"Tablets with annotations: {tablet_count}")

    # Show sample
    print("\nSample annotations:")
    cursor.execute("""
        SELECT p_number, sign_label, bbox_x, bbox_y, bbox_width, bbox_height, surface
        FROM sign_annotations
        WHERE source = 'compvis'
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: MZL {row[1]} at ({row[2]:.1f}%, {row[3]:.1f}%) size ({row[4]:.1f}%x{row[5]:.1f}%) [{row[6]}]")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    import_compvis_annotations()
