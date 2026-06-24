"""Unit tests for the eBL English-translation connector (issue #165).

Covers the accuracy-critical pure logic — pulling the English segment out of the
eBL multi-language translation string and normalising eBL line numbers — without
touching the network or a database. The DB load path is exercised by the
ingestion integration tests (skipped unless DATABASE_URL is set).
"""

from __future__ import annotations

from ingestion.connectors.ebl_translations import (
    _line_number_str,
    _reconstruction_str,
    extract_en,
)


def test_extract_en_basic_en_then_ar() -> None:
    s = "#tr.en: When on high no word was used for heaven,\n#tr.ar: ،حينَما"
    assert extract_en(s) == "When on high no word was used for heaven,"


def test_extract_en_only_arabic_returns_none() -> None:
    assert extract_en("#tr.ar: ،حين") is None


def test_extract_en_missing_returns_none() -> None:
    assert extract_en(None) is None
    assert extract_en("") is None
    assert extract_en("no markers here") is None


def test_extract_en_wraps_continuation_lines() -> None:
    # A #tr.en segment may continue on following lines until the next #tr. marker.
    s = "#tr.en: first part\nsecond part\n#tr.ar: arabic"
    assert extract_en(s) == "first part second part"


def test_extract_en_stops_at_next_language_marker() -> None:
    s = "#tr.en: english only\n#tr.de: deutsch\n#tr.en: more english"
    # Both English segments are captured; the German one is excluded.
    assert extract_en(s) == "english only more english"


def test_line_number_str_plain_string() -> None:
    assert _line_number_str("23") == "23"
    assert _line_number_str("  7a ") == "7a"


def test_line_number_str_dict_with_prime() -> None:
    assert _line_number_str({"number": 12, "hasPrime": True}) == "12'"


def test_line_number_str_dict_plain() -> None:
    assert _line_number_str({"number": 1, "hasPrime": False}) == "1"


def test_line_number_str_none() -> None:
    assert _line_number_str(None) is None


def test_reconstruction_str_from_string() -> None:
    line = {"variants": [{"reconstruction": "%n enuma elis"}]}
    assert _reconstruction_str(line) == "%n enuma elis"


def test_reconstruction_str_from_token_list() -> None:
    line = {
        "variants": [
            {"reconstruction": [{"value": "enuma"}, {"value": "elis"}, {"foo": "bar"}]}
        ]
    }
    assert _reconstruction_str(line) == "enuma elis"


def test_reconstruction_str_missing() -> None:
    assert _reconstruction_str({}) is None
    assert _reconstruction_str({"variants": []}) is None
