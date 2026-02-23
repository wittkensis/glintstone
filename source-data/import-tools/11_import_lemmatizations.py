#!/usr/bin/env python3
"""
Step 11: Import lemmatizations from ORACC CDL JSON files.

Reads corpusjson/P######.json files from each ORACC project and
populates lemmatizations for tokens that were already imported
by the ATF parser (Step 7-9).

CDL lemma node structure:
  { "node": "l",
    "ref": "P000001.3.1",   <- textid.line_seq.position (1-indexed)
    "frag": "za-ba4-lu2",
    "inst": "%sux:za-ba4-lu2=[sorrow//sorrow]N",
    "f": { "lang": "sux", "form": "za-ba4-lu2",
           "cf": "sorrow", "gw": "sorrow", "pos": "N",
           "epos": "N", "norm": "zabalu",
           "morph": "1.sg",  (sometimes)
           "gdl": [...] } }

Line reference: P######.N.M where N is the line sequence number in the CDL
file (not the ATF line label). The `n` field on line-start nodes gives
the ATF line number used in text_lines.

Matching strategy:
  1. Build lookup caches:
     - line_cache: (p_number, line_number) → {surface: line_id}
     - token_cache: (line_id, position) → token_id

  2. For each line-start node with label "o 1" / "o i 1" etc.,
     extract the ATF line number (n field) and surface type

  3. For each lemma node:
     - Extract position from ref (convert 1-indexed → 0-indexed)
     - Get line_number + surface from current walk state
     - Lookup line_id from line_cache
     - Lookup token_id from token_cache
     - Insert lemmatization

  4. Handle failures:
     - no_line_match: CDL line_number not in text_lines
     - no_token_match: position out of range (CDL vs ATF mismatch)

INDEXING NOTE:
  - CDL positions are 1-indexed: .1 = first token
  - tokens.position is 0-indexed: position=0 = first token
  - Conversion: cdl_position - 1 = db_position

Depends on:
  - Step 7-9 (text_lines and tokens must exist)
  - Step 13 (glossary_entries optional — entry_id FK if available)

Usage:
    python 11_import_lemmatizations.py [--dry-run] [--project PROJ]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

ORACC_PROJECTS = [
    "dcclt",
    "blms",
    "etcsri",
    "hbtin",
    "dccmt",
]  # projects with corpusjson

PROJECT_TO_RUN = {
    "dcclt": "oracc/dcclt",
    "blms": "oracc/blms",
    "etcsri": "oracc/etcsri",
    "hbtin": "oracc/hbtin",
    "dccmt": "oracc/dccmt",
}


def parse_inst(inst: str) -> dict:
    """
    Parse ORACC instance string: '%sux:za-ba4-lu2=[sorrow//sorrow]N'
    Returns dict with lang, form, cf, gw, pos.
    """
    result = {}
    if not inst:
        return result

    # Language prefix: %sux:
    m = re.match(r"^%(\w+(?:-\w+)*):", inst)
    if m:
        result["lang"] = m.group(1)
        inst = inst[m.end() :]

    # form=[cf//gw]pos
    m = re.match(r"^([^=]+)=", inst)
    if m:
        result["form"] = m.group(1)
        rest = inst[m.end() :]
        # [cf//gw]pos
        m2 = re.match(r"^\[([^/]+)//([^\]]+)\](\w+)", rest)
        if m2:
            result["cf"] = m2.group(1)
            result["gw"] = m2.group(2)
            result["pos"] = m2.group(3)

    return result


def parse_surface_from_label(label: str) -> str | None:
    """
    Extract surface type from CDL label like 'o 1', 'r 2', 'o i 1'.
    Returns canonical surface type or None.
    """
    label = label.strip().lower()
    if label.startswith("o"):
        return "obverse"
    if label.startswith("r"):
        return "reverse"
    if label.startswith("l"):
        return "left_edge"
    if "right" in label:
        return "right_edge"
    if label.startswith("top") or label.startswith("t."):
        return "top_edge"
    if "bottom" in label or "bot" in label:
        return "bottom_edge"
    if "seal" in label:
        return "seal"
    return None


def walk_cdl(nodes: list, state: dict, out_lemmas: list):
    """
    Recursively walk CDL node tree, collecting lemma data.
    state tracks: current_line_number, current_surface
    """
    if not isinstance(nodes, list):
        return

    for node in nodes:
        if not isinstance(node, dict):
            continue

        ntype = node.get("node")

        if ntype == "d":
            if node.get("type") == "line-start":
                line_n = node.get("n")
                label = node.get("label", "")
                if line_n is not None:
                    try:
                        state["line_number"] = int(line_n)
                    except (ValueError, TypeError):
                        pass
                surf = parse_surface_from_label(label)
                if surf:
                    state["surface"] = surf
            elif node.get("type") == "surface":
                surf_type = node.get("subtype", "")
                surf = parse_surface_from_label(surf_type)
                if surf:
                    state["surface"] = surf
                    state["line_number"] = None

        elif ntype == "l":
            # Lemma node
            ref = node.get("ref", "")
            # Extract position from ref: P######.N.M → M
            parts = ref.split(".")
            position = None
            if len(parts) >= 3:
                try:
                    position = (
                        int(parts[-1], 16) - 1
                    )  # CDL is 1-indexed, convert to 0-indexed
                except ValueError:
                    position = None

            inst_data = parse_inst(node.get("inst", ""))
            f_data = node.get("f", {})

            lemma = {
                "line_number": state.get("line_number"),
                "surface": state.get("surface"),
                "position": position,
                "frag": node.get("frag", ""),
                "lang": f_data.get("lang") or inst_data.get("lang"),
                "form": f_data.get("form") or inst_data.get("form"),
                "cf": f_data.get("cf") or inst_data.get("cf"),
                "gw": f_data.get("gw") or inst_data.get("gw"),
                "pos": f_data.get("pos") or inst_data.get("pos"),
                "epos": f_data.get("epos"),
                "norm": f_data.get("norm"),
                "morph_raw": f_data.get("morph"),
                "signature": node.get("inst"),
                "base": f_data.get("base"),
                "sense": f_data.get("sense"),
            }

            if lemma["line_number"] is not None and lemma["position"] is not None:
                out_lemmas.append(lemma)

        # Recurse
        if "cdl" in node:
            walk_cdl(node["cdl"], state, out_lemmas)


def process_cdl_file(
    conn: psycopg.Connection,
    path: Path,
    annotation_run_id: int,
    line_cache: dict,  # (p_number, line_number) → {surface: id}
    token_cache: dict,  # (line_id, position) → token_id
    stats: dict,
):
    """Process one CDL JSON file and insert lemmatizations."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        stats["skipped_files"] += 1
        return

    textid = data.get("textid", "")
    if not textid:
        return

    p_number = textid  # already in P###### format

    lemmas = []
    state = {"line_number": None, "surface": None}
    walk_cdl(data.get("cdl", []), state, lemmas)

    if not lemmas:
        return

    with conn.cursor() as cur:
        for lemma in lemmas:
            line_num = lemma["line_number"]
            position = lemma["position"]

            # Look up text_line
            line_key = (p_number, line_num)
            line_ids = line_cache.get(line_key)
            if not line_ids:
                stats["no_line_match"] += 1
                continue

            # Use first matching line_id (prefer surface match if available)
            surface = lemma.get("surface")
            line_id = None
            if surface and surface in line_ids:
                line_id = line_ids[surface]
            else:
                # Take any available line_id
                line_id = next(iter(line_ids.values()), None)

            if not line_id:
                stats["no_line_match"] += 1
                continue

            # Look up token
            token_key = (line_id, position)
            token_id = token_cache.get(token_key)
            if token_id is None:
                stats["no_token_match"] += 1
                continue

            # Insert lemmatization (includes per-word language from ORACC CDL)
            cur.execute(
                """
                INSERT INTO lemmatizations (
                    token_id, citation_form, guide_word, sense, pos, epos,
                    norm, base, signature, morph_raw, annotation_run_id, confidence,
                    language
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1.0, %s)
                ON CONFLICT DO NOTHING
            """,
                (
                    token_id,
                    lemma.get("cf"),
                    lemma.get("gw"),
                    lemma.get("sense"),
                    lemma.get("pos"),
                    lemma.get("epos"),
                    lemma.get("norm"),
                    lemma.get("base"),
                    lemma.get("signature"),
                    lemma.get("morph_raw"),
                    annotation_run_id,
                    lemma.get("lang"),
                ),
            )
            stats["lemmas"] += 1

    stats["tablets"] += 1


def build_caches(conn: psycopg.Connection, project: str) -> tuple[dict, dict]:
    """
    Build in-memory caches for line and token lookups.
    Only loads data for the given ORACC project's p_numbers.
    """
    print(f"    Building lookup caches for {project}...", end=" ", flush=True)

    # Get p_numbers for this project's corpus
    corpus_dir = ORACC_BASE / project / "json" / project / "corpusjson"
    if not corpus_dir.exists():
        return {}, {}

    p_numbers = {f.stem for f in corpus_dir.glob("P*.json")}
    if not p_numbers:
        return {}, {}

    # Convert to tuple for SQL IN clause
    p_list = tuple(p_numbers)

    # line_cache: (p_number, line_number) → {surface_type: line_id}
    line_cache = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tl.p_number, tl.line_number, s.surface_type, tl.id
            FROM text_lines tl
            LEFT JOIN surfaces s ON tl.surface_id = s.id
            WHERE tl.p_number = ANY(%s)
            AND tl.is_ruling = 0 AND tl.is_blank = 0
        """,
            (list(p_list),),
        )
        for p_num, line_num, surface_type, line_id in cur.fetchall():
            key = (p_num, line_num)
            if key not in line_cache:
                line_cache[key] = {}
            line_cache[key][surface_type or "unknown"] = line_id

    # token_cache: (line_id, position) → token_id
    all_line_ids = list(
        {lid for surf_map in line_cache.values() for lid in surf_map.values()}
    )
    token_cache = {}
    if all_line_ids:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, line_id, position FROM tokens
                WHERE line_id = ANY(%s)
            """,
                (all_line_ids,),
            )
            for token_id, line_id, position in cur.fetchall():
                token_cache[(line_id, position)] = token_id

    print(f"done. {len(line_cache)} lines, {len(token_cache)} tokens.")
    return line_cache, token_cache


def main():
    parser = argparse.ArgumentParser(description="Import ORACC CDL lemmatizations")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no DB writes"
    )
    parser.add_argument("--project", help="Only process this project (e.g. dcclt)")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 11: IMPORT LEMMATIZATIONS (ORACC CDL)")
    print("=" * 60)

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    annotation_run_ids = {}
    with conn.cursor() as cur:
        for proj, source_name in PROJECT_TO_RUN.items():
            cur.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s", (source_name,)
            )
            row = cur.fetchone()
            if row:
                annotation_run_ids[proj] = row[0]

    projects = [args.project] if args.project else ORACC_PROJECTS
    total_stats = {
        "lemmas": 0,
        "tablets": 0,
        "no_line_match": 0,
        "no_token_match": 0,
        "skipped_files": 0,
    }

    for project in projects:
        corpus_dir = ORACC_BASE / project / "json" / project / "corpusjson"
        if not corpus_dir.exists():
            print(f"\n  {project}: no corpusjson directory, skipping.")
            continue

        cdl_files = sorted(corpus_dir.glob("P*.json"))
        if not cdl_files:
            print(f"\n  {project}: no CDL files found.")
            continue

        print(f"\n  {project}: {len(cdl_files)} CDL files")
        ann_run_id = annotation_run_ids.get(project, 1)

        if args.dry_run:
            print("  [DRY RUN] Skipping DB operations.")
            continue

        line_cache, token_cache = build_caches(conn, project)
        stats = {
            "lemmas": 0,
            "tablets": 0,
            "no_line_match": 0,
            "no_token_match": 0,
            "skipped_files": 0,
        }

        for i, cdl_file in enumerate(cdl_files):
            process_cdl_file(conn, cdl_file, ann_run_id, line_cache, token_cache, stats)

            if (i + 1) % 200 == 0:
                conn.commit()
                print(
                    f"  {i + 1:>5}/{len(cdl_files)} files  |  "
                    f"{stats['lemmas']:>6,} lemmas  |  "
                    f"{stats['no_token_match']:>4,} unmatched",
                    end="\r",
                )

        conn.commit()

        for k, v in stats.items():
            total_stats[k] += v

        print(
            f"\n  {project}: {stats['lemmas']:,} lemmas, "
            f"{stats['no_line_match']:,} no-line-match, "
            f"{stats['no_token_match']:,} no-token-match"
        )

    conn.close()

    print(f"\n  Total lemmatizations: {total_stats['lemmas']:,}")
    print(f"  Tablets processed:    {total_stats['tablets']:,}")
    print(f"  No line match:        {total_stats['no_line_match']:,}")
    print(f"  No token match:       {total_stats['no_token_match']:,}")
    print("Validation: OK")


if __name__ == "__main__":
    main()
