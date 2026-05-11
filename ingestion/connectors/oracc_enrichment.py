"""ORACC artifact enrichment connector.

Adds supergenre, subgenre, pleiades_id, latitude, longitude, and oracc_projects
to existing artifact rows by scanning ORACC catalogue.json + cat.geojson files.

Depends on: cdli-catalog (artifacts must be loaded first)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

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


def _load_geojson(project: str) -> dict[str, dict]:
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
        coords = feature.get("geometry") or {}
        p_num = props.get("id_text") or props.get("id")
        if not p_num:
            continue
        coord_list = coords.get("coordinates", [])
        lat = lon = None
        if coord_list and len(coord_list) >= 2:
            lon, lat = coord_list[0], coord_list[1]
        pleiades_id = props.get("pleiades_id")
        if pleiades_id or lat is not None:
            result[p_num] = {
                "pleiades_id": str(pleiades_id) if pleiades_id else None,
                "lat": lat,
                "lon": lon,
            }
    return result


class OraccEnrichmentConnector(SourceConnector):
    id = "oracc-enrichment"
    display_name = "ORACC Artifact Enrichment"
    description = "Enriches artifact rows with ORACC supergenre, subgenre, geo coords, and project membership."
    kind = "derived"
    runs_after = ["cdli-catalog"]
    upstream_url = "https://oracc.museum.upenn.edu/"
    license = "CC-BY-SA-3.0"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield one dict per ORACC project that has a catalogue."""
        for project in ORACC_PROJECTS:
            cat_path = ORACC_BASE / project / "json" / project / "catalogue.json"
            if not cat_path.exists():
                continue
            try:
                with open(cat_path, encoding="utf-8") as f:
                    catalogue = json.load(f)
            except (json.JSONDecodeError, ValueError):
                ctx.warn("oracc_enrichment.bad_json", project=project)
                continue
            geo_data = _load_geojson(project)
            yield {
                "project": project,
                "members": catalogue.get("members", {}),
                "geo_data": geo_data,
            }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        oracc_project_map: dict[str, set] = {}

        for batch in rows:
            project = batch["project"]
            members = batch["members"]
            geo_data = batch["geo_data"]

            updates = []
            for p_num, entry in members.items():
                oracc_project_map.setdefault(p_num, set()).add(project)
                geo = geo_data.get(p_num, {})
                updates.append(
                    (
                        entry.get("supergenre"),
                        entry.get("subgenre"),
                        geo.get("pleiades_id"),
                        geo.get("lat"),
                        geo.get("lon"),
                        p_num,
                    )
                )

            if updates:
                with ctx.db.cursor() as cur:
                    cur.executemany(
                        """UPDATE artifacts SET
                            supergenre  = COALESCE(supergenre, %s),
                            subgenre    = COALESCE(subgenre, %s),
                            pleiades_id = COALESCE(pleiades_id, %s),
                            latitude    = COALESCE(latitude, %s),
                            longitude   = COALESCE(longitude, %s)
                           WHERE p_number = %s""",
                        updates,
                    )
                ctx.db.commit()
                stats.updated += len(updates)
            ctx.info(
                "oracc_enrichment.project_done", project=project, entries=len(updates)
            )

        # Update oracc_projects JSON array
        if oracc_project_map:
            project_updates = [
                (json.dumps(sorted(projects)), p_num)
                for p_num, projects in oracc_project_map.items()
            ]
            with ctx.db.cursor() as cur:
                cur.executemany(
                    "UPDATE artifacts SET oracc_projects = %s WHERE p_number = %s",
                    project_updates,
                )
            ctx.db.commit()

        return stats
