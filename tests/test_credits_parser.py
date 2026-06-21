"""Unit tests for the #261 credit-prose parser + name normalizer.

These guard the two accuracy-critical behaviours:

1.  ``normalize_name`` reproduces the exact ``surname_initials`` form stored in
    ``scholars.normalized_name`` (the conservative match key). A drift here
    silently mis-attributes or drops scholars.
2.  ``parse_credits`` extracts the right (name, role) pairs from real ORACC
    credit prose, and — critically — does NOT invent names from titles or
    co-authored citations (under-attribute rather than mis-attribute).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.credits_parser import normalize_name, parse_credits  # noqa: E402


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Mikko Luukko", "luukko_m"),
        ("Luukko, Mikko", "luukko_m"),
        ("Karen Radner", "radner_k"),
        ("Heather D. Baker", "baker_hd"),
        ("Manfred L. G. Dietrich", "dietrich_mlg"),
        ("von Bothmer, Dietrich", "bothmer_d"),
        ("Giovanni B. Lanfranchi", "lanfranchi_gb"),
        # ß is preserved (matches the stored "groß_m"), diacritics are folded.
        ("Melanie Groß", "groß_m"),
        ("Mikkö Lüükko", "luukko_m"),
    ],
)
def test_normalize_matches_stored_form(raw, expected):
    assert normalize_name(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "Luukko",  # surname only, no initial
        "M.",  # initial only
        "2017",
    ],
)
def test_normalize_rejects_non_names(raw):
    assert normalize_name(raw) == ""


def test_parse_saao_full_credit():
    text = (
        "Adapted from Mikko Luukko, The Correspondence of Tiglath-Pileser III "
        "and Sargon II (State Archives of Assyria, 19), 2012. Lemmatised by "
        "Mikko Luukko, 2012, as part of the AHRC-funded research project "
        "directed by Karen Radner."
    )
    pairs = {(m.name, m.role) for m in parse_credits(text)}
    assert ("Mikko Luukko", "lemmatizer") in pairs
    assert ("Mikko Luukko", "adapter") in pairs
    assert ("Karen Radner", "director") in pairs


def test_parse_multi_editor():
    pairs = {
        (m.name, m.role)
        for m in parse_credits("Edition by John Carnahan and Jeremie Peterson.")
    }
    assert ("John Carnahan", "editor") in pairs
    assert ("Jeremie Peterson", "editor") in pairs


def test_parse_lemmatized_variant_and_for_project():
    text = (
        "After Stefan M. Maul, `Herzberuhigungsklagen' 98; adapted for BLMS "
        "and lemmatized by Jeremie Peterson."
    )
    pairs = {(m.name, m.role) for m in parse_credits(text)}
    assert ("Jeremie Peterson", "lemmatizer") in pairs


def test_citation_with_coauthors_is_left_unattributed():
    # "Giovanni B. Lanfranchi and Simo Parpola, <title>" — ambiguous co-author
    # boundary in a citation: the adapter role must yield NO name (conservative).
    text = (
        "Adapted from Giovanni B. Lanfranchi and Simo Parpola, The "
        "Correspondence of Sargon II (SAA 5), 1990. Lemmatised by Mikko Luukko."
    )
    roles = {m.role for m in parse_credits(text)}
    assert "adapter" not in roles  # neither co-author guessed
    assert ("Mikko Luukko", "lemmatizer") in {
        (m.name, m.role) for m in parse_credits(text)
    }


def test_title_words_are_not_treated_as_names():
    # "Court Poetry and Literary Miscellanea" is a title; no fake names emerge.
    text = (
        "Adapted from Alasdair Livingstone, Court Poetry and Literary "
        "Miscellanea (SAA 3), 1989. Lemmatised by Mikko Luukko."
    )
    names = {normalize_name(m.name) for m in parse_credits(text)}
    assert "livingstone_a" in names
    assert "miscellanea_l" not in names  # title fragment rejected


def test_empty_credit_yields_nothing():
    assert parse_credits("") == []
    assert parse_credits("   ") == []
