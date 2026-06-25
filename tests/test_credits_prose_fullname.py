"""Unit tests for the shared prose full-name resolver (#473).

``core.credits_parser.resolve_prose_fullname`` is the #262 prose-disambiguation
logic, lifted into the shared module so the LIVE write-time path (the ORACC
credits connector's ``_attribute``) attributes J.N. Postgate / Tyler Yoder
correctly at INGEST time — not only in the one-time #262 backfill.

These guard that contract on the real prod surname namespaces, modelling the
``scholars_full_by_surname`` index exactly as the connector builds it from
``scholars.name`` via ``parse_person_tokens``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.credits_parser import (  # noqa: E402
    GivenToken,
    parse_person_tokens,
    resolve_prose_fullname,
)

# Real Postgate/Yoder scholar namespaces on prod: (id, scholars.name display form).
_SCHOLARS = {
    1048: "Postgate, John Nicholas",  # postgate_jn  (target)
    56894: "J. P. Postgate",  # postgate_jp  (classicist — must NOT be hit)
    24619: "Nicholas Postgate",  # postgate_n
    25368: "Carolyn Postgate",  # postgate_c
    34899: "Tyler R. Yoder",  # yoder_tr     (target)
    39039: "Perry B. Yoder",  # yoder_pb
    83861: "David E. Yoder",  # yoder_de
    84434: "William Yoder",  # yoder_w
}


def _full_index() -> dict[str, list[tuple[int, list[GivenToken]]]]:
    """Build the surname -> [(id, given-tokens)] index the connector feeds in."""
    out: dict[str, list[tuple[int, list[GivenToken]]]] = {}
    for sid, name in _SCHOLARS.items():
        parsed = parse_person_tokens(name)
        if parsed is None:
            continue
        surname, given = parsed
        out.setdefault(surname, []).append((sid, given))
    return out


def test_jn_postgate_attributes_at_write_time() -> None:
    # The #262 case: J.N. Postgate must land on postgate_jn (1048) at ingest.
    assert resolve_prose_fullname("J.N. Postgate", _full_index()) == 1048


def test_jp_postgate_attributes_to_classicist() -> None:
    assert resolve_prose_fullname("J.P. Postgate", _full_index()) == 56894


def test_tyler_yoder_attributes_to_tr() -> None:
    # Tyler Yoder normalizes to yoder_t (no scholar) under the lossy key, but the
    # full word "Tyler" uniquely fits yoder_tr (34899).
    assert resolve_prose_fullname("Tyler Yoder", _full_index()) == 34899


def test_nicholas_postgate_attributes_uniquely() -> None:
    assert resolve_prose_fullname("Nicholas Postgate", _full_index()) == 24619


@pytest.mark.parametrize("ambiguous", ["J. Postgate", "Postgate"])
def test_bare_ambiguous_initial_is_refused(ambiguous: str) -> None:
    # Accuracy over coverage: a bare ambiguous form fits 2+ scholars (or parses
    # as no person) -> resolver returns None, leaving it UNATTRIBUTED.
    assert resolve_prose_fullname(ambiguous, _full_index()) is None


def test_unknown_surname_is_refused() -> None:
    assert resolve_prose_fullname("Jane Doe", _full_index()) is None
