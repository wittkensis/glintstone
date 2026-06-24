"""Corpus map projection (#197–#199) — proportional-symbol find-spot maps.

These pin the load-bearing geometry of app/corpus_map.py — the equirectangular
projection, the area-proportional radius, and the honest handling of missing or
out-of-box coordinates — independent of the database. The render layer (Jinja
macro) trusts this math, so it must stay correct.
"""

import math

from app.corpus_map import (
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    PAD_X,
    PAD_Y,
    R_MAX,
    R_MIN,
    SINGLE_PIN_R,
    VIEW_H,
    VIEW_W,
    build_pins,
    build_single_pin,
    project,
)


def test_project_corners_map_to_padded_box():
    # NW corner (max lat, min lon) → top-left of the drawable area.
    x, y, ok = project(LAT_MAX, LON_MIN)
    assert ok is True
    assert math.isclose(x, PAD_X, abs_tol=0.01)
    assert math.isclose(y, PAD_Y, abs_tol=0.01)
    # SE corner (min lat, max lon) → bottom-right.
    x, y, ok = project(LAT_MIN, LON_MAX)
    assert math.isclose(x, VIEW_W - PAD_X, abs_tol=0.01)
    assert math.isclose(y, VIEW_H - PAD_Y, abs_tol=0.01)


def test_project_north_is_smaller_y():
    # Higher latitude must render higher up (smaller y) — map north at top.
    _, y_north, _ = project(36.0, 44.0)
    _, y_south, _ = project(31.0, 44.0)
    assert y_north < y_south


def test_project_east_is_larger_x():
    x_west, _, _ = project(33.0, 40.0)
    x_east, _, _ = project(33.0, 47.0)
    assert x_east > x_west


def test_project_out_of_box_clamps_and_flags():
    # A point far outside the box is clamped into the drawable area but flagged.
    x, y, ok = project(10.0, 0.0)
    assert ok is False
    assert PAD_X <= x <= VIEW_W - PAD_X
    assert PAD_Y <= y <= VIEW_H - PAD_Y


def test_radius_is_area_proportional():
    # Circle AREA ∝ count → radius ∝ √count. A 4× count is a 2× radius (above
    # the floor). Build two pins sharing a max and check the ratio.
    pins = build_pins(
        [
            {
                "ancient_name": "Big",
                "latitude": 32.0,
                "longitude": 45.0,
                "tablet_count": 400,
            },
            {
                "ancient_name": "Small",
                "latitude": 33.0,
                "longitude": 44.0,
                "tablet_count": 100,
            },
        ]
    )
    by = {p.ancient_name: p for p in pins}
    # radius(count) = R_MIN + sqrt(count)/sqrt(max) * (R_MAX - R_MIN)
    exp_big = R_MIN + 1.0 * (R_MAX - R_MIN)
    exp_small = R_MIN + (math.sqrt(100) / math.sqrt(400)) * (R_MAX - R_MIN)
    assert math.isclose(by["Big"].r, round(exp_big, 1), abs_tol=0.1)
    assert math.isclose(by["Small"].r, round(exp_small, 1), abs_tol=0.1)


def test_radius_clamped_to_min():
    pins = build_pins(
        [{"ancient_name": "X", "latitude": 32.0, "longitude": 45.0, "tablet_count": 1}]
    )
    # A single site is its own max → full radius; but a zero-count site floors.
    pins0 = build_pins(
        [
            {
                "ancient_name": "Z",
                "latitude": 32.0,
                "longitude": 45.0,
                "tablet_count": 0,
            },
            {
                "ancient_name": "Y",
                "latitude": 33.0,
                "longitude": 44.0,
                "tablet_count": 50,
            },
        ]
    )
    z = next(p for p in pins0 if p.ancient_name == "Z")
    assert z.r == R_MIN
    assert pins[0].r >= R_MIN


def test_build_pins_drops_missing_coords():
    pins = build_pins(
        [
            {
                "ancient_name": "HasCoords",
                "latitude": 32.0,
                "longitude": 45.0,
                "tablet_count": 10,
            },
            {
                "ancient_name": "NoLat",
                "latitude": None,
                "longitude": 45.0,
                "tablet_count": 99,
            },
            {
                "ancient_name": "NoLon",
                "latitude": 32.0,
                "longitude": None,
                "tablet_count": 99,
            },
        ]
    )
    names = {p.ancient_name for p in pins}
    assert names == {"HasCoords"}


def test_build_pins_paints_largest_first():
    pins = build_pins(
        [
            {
                "ancient_name": "Small",
                "latitude": 33.0,
                "longitude": 44.0,
                "tablet_count": 5,
            },
            {
                "ancient_name": "Large",
                "latitude": 32.0,
                "longitude": 45.0,
                "tablet_count": 500,
            },
        ]
    )
    # Largest first so small pins paint on top and stay clickable.
    assert pins[0].ancient_name == "Large"


def test_build_single_pin_fixed_radius():
    pin = build_single_pin(
        {
            "ancient_name": "Umma",
            "latitude": 31.65,
            "longitude": 45.88,
            "tablet_count": 1,
        }
    )
    assert pin is not None
    assert pin.r == SINGLE_PIN_R
    assert pin.ancient_name == "Umma"


def test_build_single_pin_none_without_coords():
    assert (
        build_single_pin(
            {"ancient_name": "Nowhere", "latitude": None, "longitude": None}
        )
        is None
    )


def test_build_pins_empty():
    assert build_pins([]) == []
