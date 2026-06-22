"""Unit tests for the wikidata-entities connector (issue #164).

These cover the accuracy-critical, pure logic — SPARQL building, result parsing,
ambiguity rejection, and qid de-duplication — without touching the network or a
database. The DB load path is exercised by the ingestion integration tests
(skipped unless DATABASE_URL is set).
"""

from __future__ import annotations

from ingestion.connectors.wikidata_entities import (
    PLEIADES_PROPERTY,
    _build_pleiades_query,
    _chunked,
    _parse_pleiades_results,
)


def _binding(pid: str, qid: str, label: str | None = None) -> dict:
    b = {
        "pleiades": {"value": pid},
        "item": {"value": f"http://www.wikidata.org/entity/{qid}"},
    }
    if label is not None:
        b["itemLabel"] = {"value": label}
    return b


def test_query_uses_p1584_and_quotes_values() -> None:
    q = _build_pleiades_query(["893951", "894019"])
    assert f"wdt:{PLEIADES_PROPERTY}" in q
    assert '"893951"' in q and '"894019"' in q
    assert "VALUES ?pleiades" in q


def test_parse_single_match() -> None:
    payload = {"results": {"bindings": [_binding("893951", "Q5684", "Babylon")]}}
    grouped = _parse_pleiades_results(payload)
    assert grouped == {"893951": [{"qid": "Q5684", "label": "Babylon"}]}


def test_parse_preserves_ambiguity() -> None:
    # One Pleiades ID resolving to two distinct items must stay a 2-element list
    # so the connector can reject it (accuracy over coverage).
    payload = {
        "results": {
            "bindings": [
                _binding("629040", "Q165995"),
                _binding("629040", "Q705132"),
            ]
        }
    }
    grouped = _parse_pleiades_results(payload)
    assert len(grouped["629040"]) == 2
    assert {m["qid"] for m in grouped["629040"]} == {"Q165995", "Q705132"}


def test_parse_dedupes_repeated_qid() -> None:
    # The label service can emit the same (pleiades, qid) twice; that is NOT
    # ambiguity and must collapse to a single match.
    payload = {
        "results": {
            "bindings": [
                _binding("894019", "Q237614", "Nimrud"),
                _binding("894019", "Q237614", "Nimrud"),
            ]
        }
    }
    grouped = _parse_pleiades_results(payload)
    assert grouped["894019"] == [{"qid": "Q237614", "label": "Nimrud"}]


def test_parse_skips_malformed_rows() -> None:
    payload = {
        "results": {
            "bindings": [
                {"pleiades": {"value": "1"}},  # no item
                {"item": {"value": "http://www.wikidata.org/entity/Q1"}},  # no pid
                _binding("2", "P31"),  # not a Q-id
                _binding("3", "Q42", "Valid"),
            ]
        }
    }
    grouped = _parse_pleiades_results(payload)
    assert grouped == {"3": [{"qid": "Q42", "label": "Valid"}]}


def test_chunked_splits_evenly_and_remainder() -> None:
    assert list(_chunked(["a", "b", "c"], 2)) == [["a", "b"], ["c"]]
    assert list(_chunked([], 2)) == []
