"""Unit tests for the gloss-browse domain rule (api/repositories/lexical_repo.py).

A "gloss" is a guide-word / translation entry. It is only meaningful for common
vocabulary (nouns, verbs, prepositions, …). Proper nouns (PN/DN/GN/…) carry a
*numeric* guide_word ("1", "00", "2") that is a homonym-disambiguation index, not
a translation. The gloss browse must exclude those purely-numeric guide_words so
the landing page surfaces real translations rather than tens of thousands of
unrelated names collapsed under one meaningless "gloss".

These tests are purely in-memory — no HTTP, no database, no app startup. They
lock in the predicate's intent so a future refactor cannot silently re-admit the
numeric proper-noun indices.
"""

import re

from api.repositories.lexical_repo import (
    _GLOSS_PREVIEW_PER_LANG,
    _REAL_GLOSS_PREDICATE,
)


# The predicate is interpolated into SQL; here we mirror its Postgres regex
# (`!~ '^[0-9]+$'`) with the equivalent Python check to assert its intent.
def _is_real_gloss(guide_word: str | None) -> bool:
    if guide_word is None or guide_word == "":
        return False
    return re.fullmatch(r"[0-9]+", guide_word) is None


def test_predicate_excludes_numeric_indices() -> None:
    # Proper-noun homonym indices — must be treated as NOT real glosses.
    for gw in ("1", "00", "2", "12", "007"):
        assert not _is_real_gloss(gw), f"{gw!r} is a numeric index, not a gloss"


def test_predicate_keeps_textual_glosses() -> None:
    # Real translation guide-words — must be kept.
    for gw in ("king", "house", "in", "to", "and", "(meaning unknown)"):
        assert _is_real_gloss(gw), f"{gw!r} is a real gloss"


def test_predicate_excludes_null_and_empty() -> None:
    assert not _is_real_gloss(None)
    assert not _is_real_gloss("")


def test_predicate_sql_targets_numeric_only() -> None:
    # Guard the actual SQL fragment so the regex anchor/character-class can't
    # drift (e.g. to a substring match that would drop "Ash1ur").
    assert "!~ '^[0-9]+$'" in _REAL_GLOSS_PREDICATE
    assert "guide_word IS NOT NULL" in _REAL_GLOSS_PREDICATE


def test_alphanumeric_guide_word_is_kept() -> None:
    # A guide_word that merely contains digits but is not purely numeric is a
    # real gloss and must survive the filter.
    assert _is_real_gloss("type-2 diabetes")
    assert _is_real_gloss("1st")


def test_preview_cap_is_small_positive() -> None:
    # The inline lemma preview must be bounded so the list payload stays small.
    assert isinstance(_GLOSS_PREVIEW_PER_LANG, int)
    assert 0 < _GLOSS_PREVIEW_PER_LANG <= 25
