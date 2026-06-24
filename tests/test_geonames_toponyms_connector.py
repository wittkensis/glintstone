"""Unit tests for the GeoNames toponym resolver (issue #166).

Covers the accuracy-critical pure logic — name folding and the confident-vs-
ambiguous resolution rule (accuracy over coverage) — without touching the
network or a database. The DB load + coordinate-backfill path is exercised by
the ingestion integration tests (skipped unless DATABASE_URL is set).
"""

from __future__ import annotations

from ingestion.connectors.geonames_toponyms import (
    CONF_NAME,
    CONF_SITE,
    _modern_candidates,
    _resolve,
    fold,
)


def _cand(gid: str, name: str, feature: str = "PPL") -> dict:
    return {
        "geonames_id": gid,
        "name": name,
        "lat": 1.0,
        "lon": 2.0,
        "feature_code": feature,
        "country": "IQ",
    }


def test_fold_strips_diacritics_and_transliteration() -> None:
    # NFKD decomposition strips combining marks, so precomposed š/ṣ/ṭ fold to
    # their base letter (Aššur -> assur). This matches the shared fold() doctrine
    # in ops/scripts/geocode_provenience.py, so both gazetteers fold names the
    # same way and a GeoNames alternate name folds to the same key.
    assert fold("Bābili") == "babili"
    assert fold("Aššur") == "assur"
    assert fold("Nineveh") == "nineveh"
    # ḫ has no canonical decomposition, so the explicit ḫ->h replace applies.
    assert fold("Ḫattuša") == "hattusa"


def test_fold_drops_punctuation_and_empty() -> None:
    assert fold("Tell  Açana") == "tellacana"
    assert fold(None) == ""
    assert fold("   ") == ""


def test_modern_candidates_skips_uncertain() -> None:
    assert _modern_candidates("uncertain") == []
    assert _modern_candidates("Uncertain (north)") == []
    assert _modern_candidates(None) == []


def test_modern_candidates_splits_country_suffix() -> None:
    # "Abydos, Egypt" should yield both the whole string and the place part.
    keys = _modern_candidates("Abydos, Egypt")
    assert "abydos" in keys


def test_resolve_single_candidate_generic() -> None:
    chosen, reason, conf = _resolve([_cand("1", "Mosul", "PPL")])
    assert chosen is not None and chosen["geonames_id"] == "1"
    assert reason is None
    assert conf == CONF_NAME


def test_resolve_single_candidate_site_gets_higher_confidence() -> None:
    chosen, reason, conf = _resolve([_cand("2", "Nimrud", "TELL")])
    assert chosen is not None
    assert conf == CONF_SITE


def test_resolve_multiple_generic_is_ambiguous() -> None:
    # Two unrelated populated places with the same folded name => never guess.
    chosen, reason, conf = _resolve(
        [_cand("1", "Kish", "PPL"), _cand("2", "Kish", "PPL")]
    )
    assert chosen is None
    assert reason == "ambiguous"


def test_resolve_multiple_with_one_site_disambiguates() -> None:
    # A single archaeological-site code among the candidates is the confident pick.
    cands = [
        _cand("1", "Foo", "PPL"),
        _cand("2", "Foo", "TELL"),
        _cand("3", "Foo", "PPL"),
    ]
    chosen, reason, conf = _resolve(cands)
    assert chosen is not None and chosen["geonames_id"] == "2"
    assert conf == CONF_SITE


def test_resolve_multiple_sites_stays_ambiguous() -> None:
    cands = [_cand("1", "Foo", "TELL"), _cand("2", "Foo", "RUIN")]
    chosen, reason, _ = _resolve(cands)
    assert chosen is None
    assert reason == "ambiguous"


def test_resolve_empty_is_no_match() -> None:
    chosen, reason, _ = _resolve([])
    assert chosen is None
    assert reason == "no_match"
