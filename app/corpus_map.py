"""Corpus map projection — proportional-symbol find-spot maps (#197–#199).

The map viz is a deliberately *schematic* proportional-symbol map (Tufte/Victor,
from the #313 all-artifacts critique): circles sized by tablet count, placed on a
plain Mesopotamia base (the two rivers as a schematic hint, no heavy basemap
chartjunk). We do the geographic projection **here, server-side**, so:

  * the SVG is render-proven without JS (the no-JS rule — pins are real <a> links),
  * the math is unit-tested at the gate (pytest), not buried in a template, and
  * all three consumers — the /tablets atlas map (#197), the composition map
    (#198) and the tablet mini-map (#199) — share one honest projection.

Projection: a plain equirectangular (lat/lon → linear x/y) over a fixed
Mesopotamia bounding box. At this latitude band (~31–40°N) the longitude
compression is mild and a schematic base does not pretend to survey accuracy, so
an equirectangular projection is the honest, dependency-free choice — no Leaflet,
no tiles, no projection library.

Sizing: circle *area* is proportional to tablet count (radius ∝ √count), the
correct encoding for a proportional-symbol map — area, not radius, reads as
quantity. Radii are clamped to a legible [MIN, MAX] range.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Fixed schematic viewBox. The map is drawn in this coordinate space and scaled
# to fit its container by the SVG viewBox — so callers pick display size in CSS,
# not here.
VIEW_W = 1000.0
VIEW_H = 760.0
# Inner padding so edge pins (and their labels) are not clipped.
PAD_X = 70.0
PAD_Y = 60.0

# Mesopotamia bounding box (decimal degrees). Chosen to comfortably contain every
# geocoded find-spot in the corpus — from Anatolia / Ḫattusa (~40°N, ~34.6°E) in
# the NW to Susa / Elam (~32°N, ~48.3°E) and the southern Sumerian cities
# (~30.9°N). A fixed box (not data-derived) keeps the base map stable across the
# three views and across filter changes, so a site never visually "jumps".
LAT_MIN, LAT_MAX = 29.5, 40.5  # south → north
LON_MIN, LON_MAX = 33.5, 49.5  # west → east

# Proportional-symbol radius range, in viewBox units.
R_MIN = 5.0
R_MAX = 46.0


@dataclass(frozen=True)
class Pin:
    """One placed find-spot, ready to draw."""

    ancient_name: str
    modern_name: str | None
    region: str | None
    tablet_count: int
    x: float  # viewBox x
    y: float  # viewBox y
    r: float  # circle radius (area ∝ count)
    in_bounds: bool  # False when coords fell outside the schematic box


def project(latitude: float, longitude: float) -> tuple[float, float, bool]:
    """Project (lat, lon) → (x, y) in the schematic viewBox.

    Returns ``(x, y, in_bounds)``. Out-of-box coordinates are clamped to the
    drawable area (so nothing renders off-canvas) and flagged ``in_bounds=False``
    so the caller can omit them honestly rather than planting a misleading pin.
    """
    in_bounds = LAT_MIN <= latitude <= LAT_MAX and LON_MIN <= longitude <= LON_MAX
    # Longitude → x (west to east, left to right).
    fx = (longitude - LON_MIN) / (LON_MAX - LON_MIN)
    # Latitude → y (north at top, so invert: higher latitude = smaller y).
    fy = (LAT_MAX - latitude) / (LAT_MAX - LAT_MIN)
    fx = min(max(fx, 0.0), 1.0)
    fy = min(max(fy, 0.0), 1.0)
    x = PAD_X + fx * (VIEW_W - 2 * PAD_X)
    y = PAD_Y + fy * (VIEW_H - 2 * PAD_Y)
    return x, y, in_bounds


def _radius(count: int, max_count: int) -> float:
    """Radius such that circle *area* is ∝ count (radius ∝ √count), clamped."""
    if max_count <= 0 or count <= 0:
        return R_MIN
    frac = math.sqrt(count) / math.sqrt(max_count)
    return R_MIN + frac * (R_MAX - R_MIN)


def build_pins(sites: list[dict]) -> list[Pin]:
    """Turn coords-API site rows into draw-ready, projected, sized pins.

    ``sites`` is the ``sites`` list from GET /proveniences/coords (or any list of
    dicts carrying ``ancient_name / latitude / longitude / tablet_count`` and
    optionally ``modern_name / region``). Rows missing usable coordinates are
    dropped (they simply do not pin — the coverage caption owns that gap).
    Returned pins are sorted largest-circle-last so big symbols do not occlude
    small ones in normal SVG paint order — wait, we want the opposite: draw
    *large first* so small pins sit on top and stay clickable. Sorted ascending
    by radius, then reversed at draw time would flip that; instead we sort
    descending by count here and the template paints in order (big → small).
    """
    placed: list[Pin] = []
    counts = [
        int(s.get("tablet_count") or 0)
        for s in sites
        if s.get("latitude") is not None and s.get("longitude") is not None
    ]
    max_count = max(counts) if counts else 0
    for s in sites:
        lat, lon = s.get("latitude"), s.get("longitude")
        if lat is None or lon is None:
            continue
        try:
            latf, lonf = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        x, y, in_bounds = project(latf, lonf)
        count = int(s.get("tablet_count") or 0)
        placed.append(
            Pin(
                ancient_name=s.get("ancient_name") or "",
                modern_name=s.get("modern_name"),
                region=s.get("region"),
                tablet_count=count,
                x=round(x, 1),
                y=round(y, 1),
                r=round(_radius(count, max_count), 1),
                in_bounds=in_bounds,
            )
        )
    # Paint largest first so the smallest stay on top and clickable.
    placed.sort(key=lambda p: p.tablet_count, reverse=True)
    return placed


# A single fixed marker radius for the one-tablet mini-map (#199), where "how
# many tablets" is always one and proportional sizing would be meaningless.
SINGLE_PIN_R = 12.0


def build_single_pin(site: dict) -> Pin | None:
    """Project one find-spot to a single fixed-size marker (tablet mini-map).

    Returns ``None`` when the site has no usable coordinates (the caller then
    renders no map — the provenience name still shows elsewhere).
    """
    lat, lon = site.get("latitude"), site.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        latf, lonf = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    x, y, in_bounds = project(latf, lonf)
    return Pin(
        ancient_name=site.get("ancient_name") or "",
        modern_name=site.get("modern_name"),
        region=site.get("region"),
        tablet_count=int(site.get("tablet_count") or 0),
        x=round(x, 1),
        y=round(y, 1),
        r=SINGLE_PIN_R,
        in_bounds=in_bounds,
    )
