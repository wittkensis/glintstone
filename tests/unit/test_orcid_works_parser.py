"""Unit tests for the #207 ORCID works parser.

These guard the accuracy-critical behaviours of ``parse_works`` and the helper
normalizers — the connector's correctness rests on them, and they run without a
database or any network access (the fetch layer is shelled out to curl and not
exercised here).

What we assert:
1.  A DOI is extracted from any summary in an ORCID work-group (different
    sources in the group may carry the identifier), and normalized to a bare
    lowercase '10.x/...' form.
2.  Work type maps into our publications enum; unknown types fall back to
    "other" so we never violate the enum CHECK constraint.
3.  Titleless works are dropped (we can neither display nor dedup them safely).
4.  Title/DOI normalization is stable so the idempotent upsert keys are stable.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.connectors.orcid_works import (  # noqa: E402
    _normalize_doi,
    _normalize_title,
    parse_works,
)


def _work_group(
    title=None, doi=None, year=None, work_type="journal-article", second_summary=None
):
    """Build a minimal ORCID /works 'group' shaped like the real v3.0 payload."""
    ext_ids = []
    if doi is not None:
        ext_ids.append({"external-id-type": "doi", "external-id-value": {"value": doi}})
    summary = {
        "title": {"title": {"value": title}} if title is not None else {},
        "type": work_type,
        "external-ids": {"external-id": ext_ids},
    }
    if year is not None:
        summary["publication-date"] = {"year": {"value": str(year)}}
    summaries = [summary]
    if second_summary is not None:
        summaries.append(second_summary)
    return {"work-summary": summaries}


def test_extracts_doi_title_year_type():
    payload = {
        "group": [
            _work_group(
                title="A Neo-Assyrian Letter",
                doi="10.1234/ABC.5678",
                year=2019,
                work_type="journal-article",
            )
        ]
    }
    works = parse_works("0000-0001-0000-0001", payload)
    assert len(works) == 1
    w = works[0]
    assert w["title"] == "A Neo-Assyrian Letter"
    assert w["doi"] == "10.1234/abc.5678"  # normalized lowercase
    assert w["year"] == 2019
    assert w["publication_type"] == "journal_article"
    assert w["orcid"] == "0000-0001-0000-0001"


def test_doi_found_in_secondary_summary_of_group():
    # Primary summary has no DOI; a later summary in the same group does.
    secondary = {
        "title": {"title": {"value": "A Neo-Assyrian Letter"}},
        "type": "journal-article",
        "external-ids": {
            "external-id": [
                {"external-id-type": "doi", "external-id-value": {"value": "10.9/xyz"}}
            ]
        },
    }
    payload = {
        "group": [
            _work_group(
                title="A Neo-Assyrian Letter", doi=None, second_summary=secondary
            )
        ]
    }
    works = parse_works("0000-0001-0000-0001", payload)
    assert len(works) == 1
    assert works[0]["doi"] == "10.9/xyz"


def test_doi_at_group_level_with_bare_string_value():
    # Live ORCID payloads put the DOI in group.external-ids with a BARE STRING
    # external-id-value (not the {"value": ...} wrapper), and the work-summary
    # may carry none. The parser must still find it.
    payload = {
        "group": [
            {
                "external-ids": {
                    "external-id": [
                        {
                            "external-id-type": "doi",
                            "external-id-value": "10.1080/00015458.2024.2437271",
                        }
                    ]
                },
                "work-summary": [
                    {
                        "title": {"title": {"value": "Al-Tasrif Surgical Instruments"}},
                        "type": "journal-article",
                        "publication-date": {"year": {"value": "2025"}},
                    }
                ],
            }
        ]
    }
    works = parse_works("0000-0003-3746-774X", payload)
    assert len(works) == 1
    assert works[0]["doi"] == "10.1080/00015458.2024.2437271"
    assert works[0]["year"] == 2025


def test_unknown_type_falls_back_to_other():
    payload = {"group": [_work_group(title="X", work_type="magic-scroll")]}
    works = parse_works("0000-0001-0000-0001", payload)
    assert works[0]["publication_type"] == "other"


def test_titleless_work_is_dropped():
    payload = {"group": [_work_group(title=None, doi="10.1/none")]}
    assert parse_works("0000-0001-0000-0001", payload) == []


def test_no_doi_work_is_kept_with_none_doi():
    payload = {"group": [_work_group(title="No DOI Here", doi=None, year=2001)]}
    works = parse_works("0000-0001-0000-0001", payload)
    assert len(works) == 1
    assert works[0]["doi"] is None
    assert works[0]["year"] == 2001


def test_empty_payload_yields_nothing():
    assert parse_works("0000-0001-0000-0001", {}) == []
    assert parse_works("0000-0001-0000-0001", {"group": []}) == []


def test_normalize_doi_strips_url_and_prefix():
    assert _normalize_doi("https://doi.org/10.1/ABC") == "10.1/abc"
    assert _normalize_doi("https://dx.doi.org/10.2/Def") == "10.2/def"
    assert _normalize_doi("doi:10.3/GHI") == "10.3/ghi"
    assert _normalize_doi("  10.4/JKL  ") == "10.4/jkl"


def test_normalize_title_is_stable_and_punctuation_insensitive():
    # Same title text always normalizes to the same key (idempotent upsert
    # depends on this). Punctuation/case/whitespace differences collapse.
    a = _normalize_title("The Letter:  A Study!")
    b = _normalize_title("the letter a study")
    assert a == b
    assert a == "the letter a study"
    # Apostrophes become a word break — deterministic, applied identically to
    # every occurrence, so the key stays stable across runs.
    assert _normalize_title("King's Letter") == _normalize_title("King s Letter")
