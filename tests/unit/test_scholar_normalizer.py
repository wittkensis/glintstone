"""Scholar name normalization. No DB needed.

Validates the contract used by the scholars connector to dedup author lists
between CDLI and ORACC.
"""

from __future__ import annotations

from ingestion.connectors.scholars import _normalize_name, _parse_name_list


# ── _normalize_name ─────────────────────────────────────────────────────────


def test_normalize_strips_whitespace():
    assert _normalize_name("  Jane Doe  ") == "Jane Doe"


def test_normalize_collapses_internal_whitespace():
    assert _normalize_name("Jane   Doe") == "Jane Doe"


def test_normalize_removes_et_al():
    assert _normalize_name("Jane Doe et al.") == "Jane Doe"
    assert _normalize_name("Jane Doe & others") == "Jane Doe"
    assert _normalize_name("Jane Doe and others") == "Jane Doe"


def test_normalize_strips_trailing_comma():
    assert _normalize_name("Jane Doe,") == "Jane Doe"


def test_normalize_nfc_unicode():
    nfd = "Janánek"  # "Janánek" decomposed
    result = _normalize_name(nfd)
    assert result == "Janánek"


def test_normalize_empty_input():
    assert _normalize_name("") == ""
    assert _normalize_name("   ") == ""


# ── _parse_name_list ────────────────────────────────────────────────────────


def test_parse_ampersand_separated():
    assert _parse_name_list("Jane Doe & John Smith") == ["Jane Doe", "John Smith"]


def test_parse_semicolon_separated():
    assert _parse_name_list("Jane Doe; John Smith") == ["Jane Doe", "John Smith"]


def test_parse_and_separated():
    assert _parse_name_list("Jane Doe and John Smith") == ["Jane Doe", "John Smith"]


def test_parse_mixed_separators():
    assert _parse_name_list("Jane Doe; John Smith & Alice Brown") == [
        "Jane Doe",
        "John Smith",
        "Alice Brown",
    ]


def test_parse_filters_short_names():
    # Names ≤2 chars are filtered (initials, junk)
    assert "JD" not in _parse_name_list("JD; Jane Doe")
    assert _parse_name_list("JD; Jane Doe") == ["Jane Doe"]


def test_parse_empty_input():
    assert _parse_name_list("") == []
    assert _parse_name_list("   ") == []
