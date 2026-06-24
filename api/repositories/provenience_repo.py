"""Provenience repository — geolocated find-spots for the map layer (#319).

Reads the `provenience_canon` lookup table, which maps the many raw CDLI
provenience strings to a smaller set of canonical ancient sites (one row per
`raw_provenience`, but `ancient_name` repeats). Migration 049 added best-effort
`latitude` / `longitude`, populated by `ops/scripts/geocode_provenience.py`
against the Pleiades gazetteer; sites that could not be located stay NULL.

`get_site_coords` powers the map viz (#197–#200 / Corpus Atlas Wave 2). It
returns one row per distinct geolocated ancient site with its coordinates,
Pleiades id, and a tablet count.

The #313 critique: the geocoder also resolved the catch-all `ancient_name =
'uncertain'` bucket to a coordinate (it folds to a Pleiades place), which would
plant the ~25k provenance-unknown tablets on a single misleading pin. We
exclude that bucket from the mapped sites and surface its tablet count
separately under `uncertain`, so the map can label it ("25,533 tablets of
uncertain provenance") instead of silently dropping or mis-placing them.
"""

import os
import time

from core.repository import BaseRepository

# The catch-all ancient_name buckets that do NOT represent a real located site.
# These are excluded from the map pins and reported separately. Compared
# case-insensitively against provenience_canon.ancient_name and
# artifacts.provenience_normalized.
_UNCERTAIN_NAMES = ("uncertain", "unknown")

# ── Site-coords TTL cache (speed-audit QW/ME-4, 2026-06-23) ─────────────────
# get_site_coords() runs two corpus-wide aggregate queries (~375 ms on prod)
# and its result only changes when ingestion re-geocodes proveniences, never
# per-request. Yet the web layer calls it on every tablet- and composition-
# detail page load. A short process-level TTL cache (single global result —
# the query takes no parameters) turns that 375 ms into ~0 ms for the vast
# majority of detail-page traffic. Mirrors the _FILTER_CACHE pattern in
# artifact_repo.py. Override the TTL with SITE_COORDS_CACHE_TTL (seconds, 0
# disables). The cache lives per uvicorn worker process; a fresh deploy clears
# it. Worst-case staleness is one TTL window (default 5 min) after a re-geocode.
_COORDS_CACHE: dict = {}
_COORDS_CACHE_TTL = float(os.environ.get("SITE_COORDS_CACHE_TTL", "300"))


class ProvenienceRepository(BaseRepository):
    def get_site_coords(self) -> dict:
        """Geolocated ancient sites with tablet counts, for the map layer.

        Returns::

            {
              "sites": [
                {ancient_name, modern_name, latitude, longitude,
                 pleiades_id, region, tablet_count},
                ...
              ],
              "uncertain": {"tablet_count": <int>},
            }

        One entry per distinct `ancient_name` that has coordinates, ordered by
        tablet_count descending (busiest sites first — convenient for the map's
        initial label/zoom heuristics). The catch-all `uncertain` /  `unknown`
        provenience buckets are never a pin; their combined tablet count is
        returned under `uncertain` so the consumer can label it (#313).

        Coordinates are best-effort from Pleiades; sites that could not be
        located simply do not appear (the contract is "located sites only").

        Result is served from a short process-level TTL cache (see
        ``_COORDS_CACHE_TTL``) because the underlying data only changes when
        ingestion re-geocodes proveniences, never per-request.
        """
        if _COORDS_CACHE_TTL > 0:
            entry = _COORDS_CACHE.get("coords")
            if entry is not None:
                cached, ts = entry
                if time.monotonic() - ts < _COORDS_CACHE_TTL:
                    return cached

        sites = self.fetch_all(
            """
            SELECT pc.ancient_name,
                   pc.modern_name,
                   pc.latitude,
                   pc.longitude,
                   pc.pleiades_id,
                   pc.region,
                   COUNT(a.p_number) AS tablet_count
            FROM (
                -- One row per ancient_name: provenience_canon has several raw
                -- spellings per site, all carrying the same coordinates.
                SELECT DISTINCT ON (ancient_name)
                    ancient_name, modern_name, latitude, longitude,
                    pleiades_id, region, sort_order
                FROM provenience_canon
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
                  AND LOWER(ancient_name) <> ALL(%(uncertain)s)
                ORDER BY ancient_name, sort_order NULLS LAST
            ) pc
            LEFT JOIN artifacts a
                ON a.provenience_normalized = pc.ancient_name
            GROUP BY pc.ancient_name, pc.modern_name, pc.latitude,
                     pc.longitude, pc.pleiades_id, pc.region
            ORDER BY tablet_count DESC, pc.ancient_name
            """,
            {"uncertain": list(_UNCERTAIN_NAMES)},
        )

        uncertain_count = self.fetch_scalar(
            """
            SELECT COUNT(*)
            FROM artifacts
            WHERE LOWER(provenience_normalized) = ANY(%(uncertain)s)
            """,
            {"uncertain": list(_UNCERTAIN_NAMES)},
        )

        result = {
            "sites": sites,
            "uncertain": {"tablet_count": uncertain_count or 0},
        }

        if _COORDS_CACHE_TTL > 0:
            _COORDS_CACHE["coords"] = (result, time.monotonic())

        return result
