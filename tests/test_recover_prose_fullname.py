"""Unit tests for the #262 prose full-name recovery pass.

These guard the accuracy-critical core of
``scripts/recover_ambiguous_contributors.py`` PASS 1: re-reading the FULL prose
form a credit carries (every given initial AND every full given word) and
attributing ONLY when that fuller form is consistent with exactly one scholar.

The motivating real case (orphaned-no-roster, prod 2026-06-25):
  * "J.N. Postgate" must resolve to ``postgate_jn`` ONLY — never the classicist
    ``postgate_jp`` ("J. P. Postgate"), and never the bare ``postgate_j`` collapse.
  * "Tyler Yoder" must resolve to ``yoder_tr`` ONLY (full given word "Tyler"),
    distinct from the other Yoders on file.
  * A bare ambiguous "J. Postgate" with no fuller form must stay REFUSED.

The functions under test are pure (no DB), so the scholar table is modelled here
as the parsed (surname, given-tokens) the script builds from ``scholars.name``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.recover_ambiguous_contributors import (  # noqa: E402
    full_name_consistent,
    parse_person_tokens,
)

# The real Postgate/Yoder scholar surname namespaces on prod (id, scholars.name).
_POSTGATES = {
    1048: "Postgate, John Nicholas",  # postgate_jn  (target)
    56894: "J. P. Postgate",  # postgate_jp  (classicist, must NOT be hit)
    24619: "Nicholas Postgate",  # postgate_n
    25368: "Carolyn Postgate",  # postgate_c
}
_YODERS = {
    34899: "Tyler R. Yoder",  # yoder_tr     (target)
    39039: "Perry B. Yoder",  # yoder_pb
    83861: "David E. Yoder",  # yoder_de
    84434: "William Yoder",  # yoder_w
}


def _candidates(raw: str, scholars: dict[int, str]) -> list[int]:
    """Mimic the script's global match: surname + full_name_consistent."""
    parsed = parse_person_tokens(raw)
    if parsed is None:
        return []
    surname, credit_given = parsed
    out: list[int] = []
    for sid, name in scholars.items():
        sp = parse_person_tokens(name)
        if sp is None or sp[0] != surname:
            continue
        if full_name_consistent(credit_given, sp[1]):
            out.append(sid)
    return sorted(out)


# --- parse_person_tokens -------------------------------------------------


def test_parse_expands_compound_initials() -> None:
    assert parse_person_tokens("J.N. Postgate") == (
        "postgate",
        [("init", "j"), ("init", "n")],
    )


def test_parse_full_given_word() -> None:
    assert parse_person_tokens("Tyler Yoder") == ("yoder", [("word", "tyler")])


def test_parse_surname_comma_given() -> None:
    assert parse_person_tokens("Postgate, John Nicholas") == (
        "postgate",
        [("word", "john"), ("word", "nicholas")],
    )


def test_parse_mixed_word_and_initial() -> None:
    assert parse_person_tokens("Tyler R. Yoder") == (
        "yoder",
        [("word", "tyler"), ("init", "r")],
    )


def test_parse_rejects_single_token() -> None:
    assert parse_person_tokens("Postgate") is None


def test_parse_drops_date_tokens() -> None:
    assert parse_person_tokens("Karen Radner 1972-") == ("radner", [("word", "karen")])


# --- full_name_consistent ------------------------------------------------


def test_consistent_initial_prefix_of_word() -> None:
    # "J.N." (j,n) fits "John Nicholas" (word john, word nicholas).
    assert full_name_consistent(
        [("init", "j"), ("init", "n")],
        [("word", "john"), ("word", "nicholas")],
    )


def test_inconsistent_second_initial_differs() -> None:
    # "J.P." (j,p) must NOT fit "John Nicholas" (john, nicholas).
    assert not full_name_consistent(
        [("init", "j"), ("init", "p")],
        [("word", "john"), ("word", "nicholas")],
    )


def test_word_vs_initial_is_refused() -> None:
    # A credit full word claims more than a scholar initial proves -> refuse.
    assert not full_name_consistent([("word", "tyler")], [("init", "t")])


def test_two_full_words_must_be_equal() -> None:
    assert not full_name_consistent([("word", "tyler")], [("word", "tobias")])


def test_more_credit_tokens_than_scholar_refused() -> None:
    assert not full_name_consistent([("init", "j"), ("init", "n")], [("word", "john")])


def test_empty_credit_refused() -> None:
    assert not full_name_consistent([], [("word", "john")])


# --- end-to-end global uniqueness on the real namespaces -----------------


def test_jn_postgate_resolves_uniquely_to_jn() -> None:
    assert _candidates("J.N. Postgate", _POSTGATES) == [1048]


def test_jp_postgate_resolves_uniquely_to_jp() -> None:
    assert _candidates("J.P. Postgate", _POSTGATES) == [56894]


def test_bare_j_postgate_is_ambiguous_and_refused() -> None:
    # "J. Postgate" fits both J.N. (1048) and J.P. (56894) -> 2 candidates -> refuse.
    assert _candidates("J. Postgate", _POSTGATES) == [1048, 56894]


def test_nicholas_postgate_resolves_uniquely() -> None:
    assert _candidates("Nicholas Postgate", _POSTGATES) == [24619]


def test_tyler_yoder_resolves_uniquely_to_tr() -> None:
    assert _candidates("Tyler Yoder", _YODERS) == [34899]


def test_tyler_r_yoder_resolves_uniquely_to_tr() -> None:
    assert _candidates("Tyler R. Yoder", _YODERS) == [34899]


@pytest.mark.parametrize("bare", ["W. Yoder", "Yoder"])
def test_yoder_underspecified_does_not_falsely_hit_tr(bare: str) -> None:
    assert 34899 not in _candidates(bare, _YODERS)
