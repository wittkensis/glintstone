"""GET /proveniences/coords — geolocated find-spots for the map layer (#319).

Publicly served as /api/v2/proveniences/coords (the nginx gateway prepends
/api/v2/ to the bare router prefix, same as every other API route). Backs the
Corpus map viz (#197–#200) and Corpus Atlas Wave 2: each canonical ancient site
that the Pleiades geocoder (`ops/scripts/geocode_provenience.py`, migration 049)
could locate, with its coordinates and a tablet count for the pin.

Tablets whose provenance is `uncertain` / `unknown` are not a map pin — their
combined count is returned separately under `uncertain` so the map can label
the gap honestly (#313 critique) rather than mis-placing ~25k tablets on one
incidental coordinate.
"""

from fastapi import APIRouter, Depends

from core.database import get_db
from api.repositories.provenience_repo import ProvenienceRepository

router = APIRouter(prefix="/proveniences", tags=["proveniences"])


@router.get("/coords")
def list_site_coords(conn=Depends(get_db)):
    """Geolocated ancient sites with coordinates and tablet counts.

    Returns ``{"sites": [{ancient_name, modern_name, latitude, longitude,
    pleiades_id, region, tablet_count}, ...], "uncertain": {"tablet_count":
    N}}``. Sites are ordered by tablet_count descending. Only sites the
    geocoder could locate appear; uncertain-provenance tablets are reported as
    an aggregate, never planted on a pin.
    """
    repo = ProvenienceRepository(conn)
    return repo.get_site_coords()
