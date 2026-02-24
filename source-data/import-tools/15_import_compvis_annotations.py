#!/usr/bin/env python3
"""
Step 15: Import CompVis sign detection annotations.

Source: source-data/sources/compvis-annotations/annotations/

Imports bounding box annotations for cuneiform sign detection from the
Heidelberg CompVis dataset. 81 tablets, ~8,282 sign annotations.

Provider: CompVis Heidelberg (CC BY 4.0)

Populates:
  - surfaces: auto-created if missing for a tablet
  - surface_images: one record per unique (tablet, view) combination
  - sign_annotations: one row per detected sign with bbox
  - pipeline_status: sets graphemic_complete for tablets with annotations

Sign identity: mapped from MZL numbers using eBL's mzl.txt concordance
(MZL label -> OGSL sign_id). Signs without OGSL mapping get sign_id=NULL.

Usage:
    python 15_import_compvis_annotations.py [--dry-run] [--reset]
"""

import argparse
import ast
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

COMPVIS_DIR = Path(__file__).resolve().parents[1] / "sources/compvis-annotations"
ANNOTATIONS_DIR = COMPVIS_DIR / "annotations"
MZL_TXT = (
    Path(__file__).resolve().parents[1]
    / "sources/ebl-annotations/cuneiform_ocr_data/sign_mappings/mzl.txt"
)

# Use the full train + test files, not the individual train_A..F splits
ANNOTATION_FILES = [
    ANNOTATIONS_DIR / "bbox_annotations_train_full.csv",
    ANNOTATIONS_DIR / "bbox_annotations_test_full.csv",
]

PROVIDER_NAME = "CompVis Heidelberg"
PROVIDER_LICENSE = "CC BY 4.0"
ANNOTATION_RUN_SOURCE = "compvis"

# View description -> surface_type mapping
VIEW_TO_SURFACE_TYPE = {
    "obv": "obverse",
    "obs": "obverse",
    "rev": "reverse",
    "vs": "obverse",
    "rs": "reverse",
    "": "obverse",  # Default for empty view
}


def load_mzl_concordance() -> dict[int, str]:
    """
    Load MZL number -> OGSL sign_id mapping from eBL mzl.txt.

    mzl.txt format: "SIGN_NAME MZL_NUMBER" per line.
    Returns: {mzl_number: sign_id}
    """
    if not MZL_TXT.exists():
        print(f"  Warning: MZL concordance not found at {MZL_TXT}")
        return {}

    concordance = {}
    with open(MZL_TXT) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                sign_name = parts[0]
                try:
                    mzl_no = int(parts[1])
                    concordance[mzl_no] = sign_name
                except ValueError:
                    pass
    return concordance


def normalize_museum_no(tablet_id: str) -> str:
    """
    Normalize CompVis tablet IDs (no spaces) to CDLI format (with spaces).
    E.g. "BM099070" -> "BM 099070", "VAT08803Rs" -> "VAT 08803"
    """
    # Strip trailing orientation suffixes
    clean = re.sub(r"(Vs|Rs|Obv|Rev)$", "", tablet_id, flags=re.IGNORECASE)
    # Insert space between letter prefix and digits
    m = re.match(r"^([A-Z]+)(\d.*)$", clean)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return clean


def parse_surface_type_from_tablet_id(tablet_id: str) -> str | None:
    """
    Extract view hint from tablet_id suffix if present.
    E.g. "VAT08803Rs" -> "reverse", "K09237Vs" -> "obverse"
    """
    m = re.search(r"(Vs|Rs|Obv|Rev)$", tablet_id, flags=re.IGNORECASE)
    if m:
        suffix = m.group(1).lower()
        return VIEW_TO_SURFACE_TYPE.get(suffix)
    return None


def resolve_p_number(tablet_id: str, conn: psycopg.Connection) -> str | None:
    """Look up p_number from tablet_id (P-number or museum no)."""
    cur = conn.cursor()

    # Direct P-number
    if re.match(r"^P\d+$", tablet_id):
        cur.execute("SELECT p_number FROM artifacts WHERE p_number = %s", (tablet_id,))
        row = cur.fetchone()
        return row[0] if row else None

    # Museum number lookup: try normalized form
    museum_no = normalize_museum_no(tablet_id)
    cur.execute(
        "SELECT p_number FROM artifacts WHERE museum_no = %s LIMIT 1",
        (museum_no,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Try artifact_identifiers
    normalized = museum_no.lower().replace(" ", "")
    cur.execute(
        """SELECT p_number FROM artifact_identifiers
           WHERE identifier_normalized = %s AND identifier_type = 'museum_no'
           LIMIT 1""",
        (normalized,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def get_or_create_surface(
    p_number: str,
    surface_type: str,
    conn: psycopg.Connection,
) -> int | None:
    """
    Find or auto-create a surface record for (p_number, surface_type).
    Returns surface_id or None on failure.
    """
    cur = conn.cursor()

    # Try exact match first
    cur.execute(
        "SELECT id FROM surfaces WHERE p_number = %s AND surface_type = %s LIMIT 1",
        (p_number, surface_type),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Try any existing surface for this tablet
    cur.execute(
        "SELECT id FROM surfaces WHERE p_number = %s LIMIT 1",
        (p_number,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # No surfaces exist — auto-create one
    cur.execute(
        """INSERT INTO surfaces (p_number, surface_type)
           VALUES (%s, %s)
           ON CONFLICT (p_number, surface_type) DO NOTHING
           RETURNING id""",
        (p_number, surface_type),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # ON CONFLICT hit — fetch the existing row
    cur.execute(
        "SELECT id FROM surfaces WHERE p_number = %s AND surface_type = %s",
        (p_number, surface_type),
    )
    row = cur.fetchone()
    return row[0] if row else None


def get_or_create_surface_image(
    p_number: str,
    view_desc: str,
    surface_type: str,
    annotation_run_id: int,
    conn: psycopg.Connection,
) -> int | None:
    """
    Get or create a surface_image record for this (p_number, surface_type).
    Auto-creates the surface if it doesn't exist.
    Returns surface_image_id or None on failure.
    """
    surface_id = get_or_create_surface(p_number, surface_type, conn)
    if not surface_id:
        return None

    cur = conn.cursor()

    # Build image_path from p_number + view_desc
    image_path = f"compvis/{p_number}/{view_desc or 'Obv'}"

    # CDLI image URL
    source_url = f"https://cdli.earth/dl/photo/{p_number.lower()}_o.jpg"

    cur.execute(
        """INSERT INTO surface_images
               (surface_id, image_path, image_type, source_url, annotation_run_id)
           VALUES (%s, %s, 'photo', %s, %s)
           ON CONFLICT (surface_id, image_path) DO NOTHING
           RETURNING id""",
        (surface_id, image_path, source_url, annotation_run_id),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Already exists — fetch it
    cur.execute(
        "SELECT id FROM surface_images WHERE surface_id = %s AND image_path = %s",
        (surface_id, image_path),
    )
    row = cur.fetchone()
    return row[0] if row else None


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float] | None:
    """Parse '[x1, y1, x2, y2]' -> (x, y, w, h)."""
    try:
        coords = ast.literal_eval(bbox_str)
        x1, y1, x2, y2 = coords
        return float(x1), float(y1), float(x2 - x1), float(y2 - y1)
    except Exception:
        return None


def reset_compvis_data(conn: psycopg.Connection, annotation_run_id: int):
    """Delete all CompVis sign_annotations and surface_images for a clean re-import."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM sign_annotations WHERE annotation_run_id = %s",
            (annotation_run_id,),
        )
        deleted_annotations = cur.rowcount
        cur.execute(
            "DELETE FROM surface_images WHERE annotation_run_id = %s",
            (annotation_run_id,),
        )
        deleted_images = cur.rowcount
        # Also clear orphaned annotations with NULL surface_image_id
        cur.execute(
            "DELETE FROM sign_annotations WHERE surface_image_id IS NULL",
        )
        deleted_orphans = cur.rowcount
    conn.commit()
    print(
        f"  Reset: deleted {deleted_annotations} annotations, {deleted_images} surface_images, {deleted_orphans} orphans"
    )


def update_pipeline_status(conn: psycopg.Connection):
    """Mark tablets with sign_annotations as having graphemic data."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE pipeline_status ps
            SET graphemic_complete = 1.0
            WHERE EXISTS (
                SELECT 1 FROM sign_annotations sa
                JOIN surface_images si ON sa.surface_image_id = si.id
                JOIN surfaces s ON si.surface_id = s.id
                WHERE s.p_number = ps.p_number
            )
            AND (ps.graphemic_complete IS NULL OR ps.graphemic_complete = 0)
        """)
        updated = cur.rowcount
    conn.commit()
    print(f"  Pipeline status: updated {updated} tablets with graphemic_complete = 1.0")


def main():
    parser = argparse.ArgumentParser(description="Import CompVis sign annotations")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing CompVis data before re-importing",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 15: IMPORT COMPVIS SIGN ANNOTATIONS")
    print("=" * 60)

    mzl_map = load_mzl_concordance()
    print(f"\n  MZL->OGSL concordance: {len(mzl_map)} entries")

    # Collect all annotations from all CSV files (deduplicate by segm_idx)
    rows_by_segm: dict[tuple, dict] = {}
    for csv_path in ANNOTATION_FILES:
        if not csv_path.exists():
            print(f"  Skipping missing: {csv_path.name}")
            continue
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (
                    row["tablet_CDLI"],
                    row["view_desc"],
                    row["mzl_label"],
                    row["bbox"],
                )
                rows_by_segm[key] = row

    all_rows = list(rows_by_segm.values())
    print(f"  Total annotations (deduplicated): {len(all_rows):,}")

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        # Show sample
        seen_tablets = set()
        for row in all_rows[:20]:
            tid = row["tablet_CDLI"]
            if tid not in seen_tablets:
                seen_tablets.add(tid)
                mzl = int(row["mzl_label"])
                sign = mzl_map.get(mzl, "?")
                print(
                    f"  {tid} | {row['view_desc']} | MZL {mzl} -> {sign} | bbox {row['bbox']}"
                )
        return

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    try:
        with conn.cursor() as cur:
            # Get annotation_run_id for compvis
            cur.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s LIMIT 1",
                (ANNOTATION_RUN_SOURCE,),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    """INSERT INTO annotation_runs
                           (source_name, source_type, method, corpus_scope, notes)
                       VALUES (%s, 'import', 'ML_model', %s, %s)
                       RETURNING id""",
                    (
                        ANNOTATION_RUN_SOURCE,
                        "81 tablets, ~8,282 sign annotations",
                        f"Heidelberg CompVis sign detection. {PROVIDER_LICENSE}.",
                    ),
                )
                row = cur.fetchone()
            annotation_run_id = row[0]

        # Reset if requested
        if args.reset:
            print("\n  Resetting existing CompVis data...")
            reset_compvis_data(conn, annotation_run_id)

        # Pre-build sign_id lookup from signs table for MZL->OGSL validation
        with conn.cursor() as cur:
            cur.execute("SELECT sign_id FROM signs")
            known_signs = {r[0] for r in cur.fetchall()}
        print(f"  Signs in DB: {len(known_signs):,}")

        # Cache p_number lookups
        p_number_cache: dict[str, str | None] = {}
        # Cache surface_image_id lookups
        surf_img_cache: dict[tuple, int | None] = {}

        annotations_inserted = 0
        annotations_skipped = 0
        tablets_not_found = set()

        for row in all_rows:
            tablet_id = row["tablet_CDLI"]
            view_desc = row.get("view_desc", "") or ""
            mzl_label = int(row["mzl_label"])
            bbox_str = row["bbox"]

            # Resolve p_number
            if tablet_id not in p_number_cache:
                p_number_cache[tablet_id] = resolve_p_number(tablet_id, conn)
            p_number = p_number_cache[tablet_id]

            if not p_number:
                tablets_not_found.add(tablet_id)
                annotations_skipped += 1
                continue

            # Determine surface_type
            surface_type_hint = parse_surface_type_from_tablet_id(tablet_id)
            view_lower = view_desc.lower()
            surface_type = surface_type_hint or VIEW_TO_SURFACE_TYPE.get(
                view_lower, "obverse"
            )

            # Get/create surface_image (auto-creates surface if needed)
            cache_key = (p_number, view_desc, surface_type)
            if cache_key not in surf_img_cache:
                surf_img_cache[cache_key] = get_or_create_surface_image(
                    p_number, view_desc, surface_type, annotation_run_id, conn
                )
            surface_image_id = surf_img_cache[cache_key]

            if not surface_image_id:
                annotations_skipped += 1
                continue

            # Parse bbox
            bbox = parse_bbox(bbox_str)
            if not bbox:
                annotations_skipped += 1
                continue
            bx, by, bw, bh = bbox

            # Map MZL -> sign_id
            sign_name = mzl_map.get(mzl_label)
            sign_id = sign_name if sign_name in known_signs else None

            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO sign_annotations
                           (surface_image_id, sign_id, bbox_x, bbox_y, bbox_w, bbox_h,
                            annotation_run_id, confidence)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT DO NOTHING""",
                    (
                        surface_image_id,
                        sign_id,
                        bx,
                        by,
                        bw,
                        bh,
                        annotation_run_id,
                        1.0,
                    ),
                )
                if cur.rowcount:
                    annotations_inserted += 1
                else:
                    annotations_skipped += 1

        conn.commit()

        print(f"\n  Annotations inserted: {annotations_inserted:,}")
        print(f"  Annotations skipped:  {annotations_skipped:,}")
        if tablets_not_found:
            print(
                f"  Tablets not found ({len(tablets_not_found)}): {sorted(tablets_not_found)}"
            )

        # Update pipeline_status for tablets with annotations
        update_pipeline_status(conn)

        conn.close()

        # Validate
        assert (
            annotations_inserted > 5000
        ), f"Expected >5000 annotations, got {annotations_inserted}"
        print("  Validation: OK")

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\nFailed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
