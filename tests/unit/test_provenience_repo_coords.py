"""Unit tests for ProvenienceRepository.get_site_coords (#319).

These lock the contract the map route and viz (#197–#200 / Corpus Atlas Wave 2)
depend on — the payload shape and, critically, the #313 guarantee that the
catch-all `uncertain` provenance is reported as an aggregate count, never as a
map pin. The actual SQL (de-duplicated provenience_canon LEFT JOIN artifacts,
the uncertain exclusion) is validated against prod in the build's
data-availability gate; here the two fetch helpers are stubbed.
"""

from __future__ import annotations

import pytest

from api.repositories import provenience_repo
from api.repositories.provenience_repo import ProvenienceRepository


@pytest.fixture(autouse=True)
def _clear_coords_cache():
    """Isolate the process-level site-coords TTL cache between tests.

    ``get_site_coords`` memoises its (parameter-free) result in a module-level
    ``_COORDS_CACHE`` (speed-audit QW/ME-4). Without clearing it, the first test
    to run seeds the cache and later tests — which stub different fetch_* return
    values — would read the stale cached payload instead of their own. Mirrors
    the ``_QUERY_VEC_CACHE.clear()`` isolation in the search-engine timing tests.
    """
    provenience_repo._COORDS_CACHE.clear()
    yield
    provenience_repo._COORDS_CACHE.clear()


def _repo() -> ProvenienceRepository:
    # BaseRepository.__init__ only stores the connection; we never touch it
    # because every fetch_* is stubbed per-test.
    return ProvenienceRepository(conn=None)  # type: ignore[arg-type]


def test_payload_shape_sites_and_uncertain():
    """Located sites become the `sites` array; the uncertain bucket is carried
    through as a separate aggregate count (never a pin)."""
    repo = _repo()
    rows = [
        {
            "ancient_name": "Umma",
            "modern_name": "Tell Jokha",
            "latitude": 31.66,
            "longitude": 45.88,
            "pleiades_id": "44626252",
            "region": "Sumer",
            "tablet_count": 36963,
        },
        {
            "ancient_name": "Nippur",
            "modern_name": "Nuffar",
            "latitude": 32.12,
            "longitude": 45.23,
            "pleiades_id": "912910",
            "region": "Sumer",
            "tablet_count": 27650,
        },
    ]
    repo.fetch_all = lambda sql, params=(): rows  # type: ignore[assignment]
    repo.fetch_scalar = lambda sql, params=(): 25533  # type: ignore[assignment]

    result = repo.get_site_coords()

    assert result["sites"] == rows
    assert result["uncertain"] == {"tablet_count": 25533}
    # Every mapped site must carry real coordinates.
    assert all(s["latitude"] is not None for s in result["sites"])
    assert all(s["longitude"] is not None for s in result["sites"])


def test_no_located_sites_returns_empty_list_not_none():
    """Zero geocoded sites yields an empty `sites` list (map renders its empty
    state), and the uncertain count still comes through."""
    repo = _repo()
    repo.fetch_all = lambda sql, params=(): []  # type: ignore[assignment]
    repo.fetch_scalar = lambda sql, params=(): 0  # type: ignore[assignment]

    result = repo.get_site_coords()

    assert result["sites"] == []
    assert result["uncertain"] == {"tablet_count": 0}


def test_null_uncertain_count_coerced_to_zero():
    """A NULL scalar (no matching rows) is coerced to 0, never None — the
    consumer can render a number without a guard."""
    repo = _repo()
    repo.fetch_all = lambda sql, params=(): []  # type: ignore[assignment]
    repo.fetch_scalar = lambda sql, params=(): None  # type: ignore[assignment]

    result = repo.get_site_coords()

    assert result["uncertain"] == {"tablet_count": 0}
