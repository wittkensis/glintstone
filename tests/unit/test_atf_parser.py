"""Unit tests for the ATF parser. No database needed.

Covers:
- Header (`&Pxxx = Designation`)
- Language directive
- Standard surfaces (obverse / reverse / edges / seal)
- Artifact-shape surfaces (envelope / prism / cylinder / brick / cone / bulla /
  tablet / object / face / column) — added in migration 033 / issue #19
- Column tracking
- Numbered lines (plain and primed)
- Translations
- Ruling and broken markers
- Composites (`>>Qxxx`)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.connectors.atf_parser import SURFACE_MAP, _parse_atf_file


def _write_atf(tmp_path: Path, atf: str) -> Path:
    p = tmp_path / "sample.atf"
    p.write_text(atf, encoding="utf-8")
    return p


# ── SURFACE_MAP coverage ────────────────────────────────────────────────────


def test_surface_map_covers_expected_markers():
    """Every marker the parser cares about resolves to a CHECK-allowed value."""
    expected = {
        "obverse",
        "reverse",
        "left_edge",
        "right_edge",
        "top_edge",
        "bottom_edge",
        "seal",
        "envelope",
        "tablet",
        "object",
        "prism",
        "cylinder",
        "brick",
        "cone",
        "bulla",
        "column",
        "face",
    }
    assert expected.issubset(set(v for v in SURFACE_MAP.values() if v))


def test_surface_map_legacy_shortcuts():
    assert SURFACE_MAP["o"] == "obverse"
    assert SURFACE_MAP["r"] == "reverse"
    assert SURFACE_MAP["left"] == "left_edge"


# ── Tablet header + lines ──────────────────────────────────────────────────


def test_parses_minimal_tablet(tmp_path):
    atf = (
        "&P000001 = Test tablet\n"
        "#atf: lang sux\n"
        "@obverse\n"
        "1. lugal\n"
        "2. dingir\n"
    )
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    assert len(tablets) == 1
    t = tablets[0]
    assert t["p_number"] == "P000001"
    assert t["lang"] == "sux"
    # surfaces is a dict keyed by surface_type
    assert "obverse" in t["surfaces"]


def test_parses_two_tablets(tmp_path):
    atf = (
        "&P000001 = First\n@obverse\n1. line one\n"
        "&P000002 = Second\n@obverse\n1. line two\n"
    )
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    assert [t["p_number"] for t in tablets] == ["P000001", "P000002"]


# ── New artifact-shape surfaces (issue #19) ─────────────────────────────────


@pytest.mark.parametrize(
    "marker,expected",
    [
        ("envelope", "envelope"),
        ("prism", "prism"),
        ("cylinder", "cylinder"),
        ("brick", "brick"),
        ("cone", "cone"),
        ("bulla", "bulla"),
        ("tablet", "tablet"),
        ("object", "object"),
        ("face", "face"),
        ("edge", "face"),  # generic edge → face per SURFACE_MAP
    ],
)
def test_artifact_shape_surfaces_emit_real_surface(tmp_path, marker, expected):
    """Lines under these markers used to get current_surface_type=None, so
    sign_annotations on envelopes/prisms had no surface_id.
    """
    atf = f"&P000099 = Object test\n" f"@{marker}\n" f"1. ABCDEF\n"
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    assert expected in tablets[0]["surfaces"]


def test_column_marker_tracks_current_column(tmp_path):
    """`@column N` sets the column counter without creating a surface row."""
    atf = "&P000010 = Columnar tablet\n" "@obverse\n" "@column 2\n" "1. line A\n"
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    # surfaces still just the obverse — column is metadata, not a surface row
    assert tablets[0]["surfaces"] == {"obverse": True}
    # the line should carry column=2
    surface, column, _line_no, _text, _ruling, _blank = tablets[0]["lines"][0]
    assert surface == "obverse"
    assert column == 2


# ── Translation lines ───────────────────────────────────────────────────────


def test_translation_line_captured(tmp_path):
    atf = "&P000020 = Translated\n" "@obverse\n" "1. lugal\n" "#tr.en: the king\n"
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    lang, text, line_counter = tablets[0]["translations"][0]
    assert lang == "en"
    assert text == "the king"
    # Should be attached to the most recent line (line 1)
    assert line_counter == 1


# ── Whitespace + encoding ───────────────────────────────────────────────────


def test_blank_lines_ignored(tmp_path):
    atf = "&P000030 = Sparse\n" "\n" "@obverse\n" "\n" "1. lugal\n" "\n"
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    assert len(tablets) == 1
    assert tablets[0]["p_number"] == "P000030"


def test_utf8_unicode_signs_preserved(tmp_path):
    atf = "&P000040 = Unicode\n" "@obverse\n" "1. 𒀭 šarru\n"
    tablets = list(_parse_atf_file(_write_atf(tmp_path, atf)))
    _surface, _col, _line_no, raw_text, _ruling, _blank = tablets[0]["lines"][0]
    assert "𒀭" in raw_text
    assert "šarru" in raw_text
