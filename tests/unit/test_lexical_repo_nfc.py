"""NFC normalization helper in the lexical repo. No DB needed.

The bug being defended against: same logical sign written with different
Unicode normalization (NFD vs NFC) wouldn't match in DB lookups.
"""

from __future__ import annotations

import unicodedata

from api.repositories.lexical_repo import _nfc


def test_nfc_normalizes_decomposed_to_composed():
    """`š` written as `s` + COMBINING CARON should collapse to U+0161."""
    nfd = unicodedata.normalize("NFD", "š")
    nfc = unicodedata.normalize("NFC", "š")
    assert nfd != nfc
    assert _nfc(nfd) == nfc


def test_nfc_idempotent_on_already_nfc():
    s = "lugal"
    assert _nfc(s) == s


def test_nfc_handles_cuneiform_codepoints():
    s = "𒀭"  # AN — single codepoint, no normalization change
    assert _nfc(s) == s


def test_nfc_mixed_string():
    nfd_string = unicodedata.normalize("NFD", "šarru")
    result = _nfc(nfd_string)
    assert result == "šarru"
    assert result == unicodedata.normalize("NFC", result)
