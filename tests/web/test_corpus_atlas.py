"""Corpus Atlas (#320) — timeline axis geometry.

_timeline_axis turns raw per-period counts into log-scaled bar widths and
proportional BCE positions so the server-rendered timeline reads honestly
(Tufte: the 111k Ur III skew must not drown small periods). These tests pin the
load-bearing math, independent of the database.
"""

from app.routes.tablets import _timeline_axis


def test_timeline_axis_empty():
    assert _timeline_axis([]) == []


def test_log_scale_keeps_small_periods_visible():
    rows = _timeline_axis(
        [
            {"canonical": "Ur III", "count": 111285, "date_start_bce": 2112},
            {"canonical": "Tiny", "count": 3, "date_start_bce": 1000},
        ]
    )
    big, tiny = rows[0], rows[1]
    # The largest period dominates the log scale, so its (unclamped) width is
    # far larger than the tiny period's — and both stay on-track (the bar never
    # runs past the right edge: left + width <= 100).
    assert big["bar_width"] > tiny["bar_width"]
    assert big["bar_left"] + big["bar_width"] <= 100.0
    # A 3-tablet period still gets a visible stub (well above its ~0.003%
    # raw-linear share).
    assert tiny["bar_width"] >= 4.0


def test_bar_never_overflows_track():
    rows = _timeline_axis(
        [
            # late, count-heavy period: large width + far-right start would
            # overflow without the clamp.
            {"canonical": "Neo-Babylonian", "count": 90000, "date_start_bce": 626},
            {"canonical": "Pre-Uruk", "count": 200, "date_start_bce": 8500},
        ]
    )
    for r in rows:
        assert r["bar_left"] + r["bar_width"] <= 100.0
        assert r["bar_left"] >= 0.0


def test_bce_position_maps_onto_3000_to_0_axis():
    [row] = _timeline_axis([{"canonical": "P", "count": 10, "date_start_bce": 1500}])
    # 1500 BCE is the midpoint of the 3000→0 axis → ~50% from the left.
    assert 49.0 <= row["bar_left"] <= 51.0


def test_undated_period_pins_left_and_still_bars():
    [row] = _timeline_axis(
        [{"canonical": "Undated", "count": 500, "date_start_bce": None}]
    )
    assert row["bar_left"] == 0.0
    assert row["bar_width"] >= 4.0
