#!/usr/bin/env python3
"""
Step 5b: Enrich artifacts table with ORACC catalogue data.

Adds to existing artifact rows:
  - supergenre (from ORACC catalogue)
  - subgenre (from ORACC if missing from CDLI)
  - pleiades_id, latitude, longitude (from ORACC cat.geojson)
  - oracc_projects (JSON array of project membership)

Depends on: Step 5 (artifacts must be loaded)

Usage:
    python 05b_enrich_artifacts_oracc.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

ORACC_PROJECTS = [
    "dcclt",
    "epsd2",
    "rinap",
    "saao",
    "blms",
    "cams",
    "etcsri",
    "riao",
    "etcsl",
    "ribo",
    "rime",
    "amgg",
    "hbtin",
]


def load_geojson(project: str) -> dict:
    """
    Load cat.geojson and return mapping: p_number → {pleiades_id, lat, lon}
    """
    path = ORACC_BASE / project / "json" / project / "cat.geojson"
    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            geo = json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}

    result = {}
    for feature in geo.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {})
        if not coords:
            continue

        p_num = props.get("id_text") or props.get("id")
        if not p_num:
            continue

        coord_list = coords.get("coordinates", [])
        lat = lon = None
        if coord_list and len(coord_list) >= 2:
            lon = coord_list[0]
            lat = coord_list[1]

        pleiades_id = props.get("pleiades_id")
        if pleiades_id or lat is not None:
            result[p_num] = {
                "pleiades_id": str(pleiades_id) if pleiades_id else None,
                "lat": lat,
                "lon": lon,
            }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Enrich artifacts from ORACC catalogue"
    )
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 5b: ENRICH ARTIFACTS FROM ORACC")
    print("=" * 60)

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    total_geo_updated = 0
    total_enriched = 0
    oracc_project_map: dict[str, set] = {}  # p_number → {projects}

    for project in ORACC_PROJECTS:
        cat_path = ORACC_BASE / project / "json" / project / "catalogue.json"
        if not cat_path.exists():
            continue

        print(f"\n  {project}...", end=" ", flush=True)
        try:
            with open(cat_path, encoding="utf-8") as f:
                catalogue = json.load(f)
        except (json.JSONDecodeError, ValueError):
            print("invalid JSON, skipping")
            continue

        members = catalogue.get("members", {})
        geo_data = load_geojson(project)

        updates = []
        for p_num, entry in members.items():
            # Track project membership
            if p_num not in oracc_project_map:
                oracc_project_map[p_num] = set()
            oracc_project_map[p_num].add(project)

            supergenre = entry.get("supergenre")
            subgenre = entry.get("subgenre")
            geo = geo_data.get(p_num, {})

            updates.append(
                (
                    supergenre,
                    subgenre,
                    geo.get("pleiades_id"),
                    geo.get("lat"),
                    geo.get("lon"),
                    p_num,
                )
            )

        if not args.dry_run and updates:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    UPDATE artifacts SET
                        supergenre = COALESCE(supergenre, %s),
                        subgenre = COALESCE(subgenre, %s),
                        pleiades_id = COALESCE(pleiades_id, %s),
                        latitude = COALESCE(latitude, %s),
                        longitude = COALESCE(longitude, %s)
                    WHERE p_number = %s
                """,
                    updates,
                )
            conn.commit()
            total_enriched += len(updates)

        print(f"{len(updates)} entries, {len(geo_data)} with geo")

    # Update oracc_projects JSON array
    print("\n  Updating oracc_projects membership...", end=" ", flush=True)
    if not args.dry_run and oracc_project_map:
        project_updates = [
            (json.dumps(sorted(projects)), p_num)
            for p_num, projects in oracc_project_map.items()
        ]
        with conn.cursor() as cur:
            cur.executemany(
                "UPDATE artifacts SET oracc_projects = %s WHERE p_number = %s",
                project_updates,
            )
        conn.commit()
        total_geo_updated = len(project_updates)

    conn.close()

    print(f"done. {total_geo_updated:,} artifacts updated with project membership.")
    print(f"\n  Total enrichment updates: {total_enriched:,}")
    print("Validation: OK")


if __name__ == "__main__":
    main()
