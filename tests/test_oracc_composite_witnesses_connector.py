"""Tests for the ORACC composite-witness linkage connector (#293).

The load-bearing scholarly guarantee is in `extract()`: it must derive witness
P-numbers ONLY from each composite's `cdli_id_numbers` field, and must never
mistake the composite's own `cdli_composite_id` for a witness. These tests pin
that behaviour against a small synthetic catalogue tree.
"""

from __future__ import annotations

import json
from pathlib import Path

from ingestion.connectors.oracc_composite_witnesses import (
    OraccCompositeWitnessesConnector,
)


class _FakeCtx:
    """Minimal RunContext stand-in: extract() only calls info()/warn()."""

    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    def info(self, msg: str, **ctx) -> None:
        self.events.append(("info", msg, ctx))

    def warn(self, msg: str, **ctx) -> None:
        self.events.append(("warn", msg, ctx))


def _write_catalogue(root: Path, project: str, members: dict) -> None:
    proj_dir = root / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "catalogue.json").write_text(
        json.dumps({"project": project, "members": members}),
        encoding="utf-8",
    )


def test_extracts_only_witnesses_not_composite_id(tmp_path: Path) -> None:
    _write_catalogue(
        tmp_path,
        "oimea",
        {
            "Q000376": {
                "designation": "Utu-hegal 4",
                "cdli_id_numbers": "P227538; P227539; P227540",
                "exemplar_info": "AO 06018; AO 06314; Ist Ni 04167",
                # The composite's OWN artifact P-number — must NOT become a link.
                "cdli_composite_id": "P433096",
                "id_composite": "Q000376",
            }
        },
    )
    conn = OraccCompositeWitnessesConnector(base=tmp_path)
    pairs = {(r["p_number"], r["q_number"]) for r in conn.extract(_FakeCtx())}

    assert pairs == {
        ("P227538", "Q000376"),
        ("P227539", "Q000376"),
        ("P227540", "Q000376"),
    }
    # The composite's own P-number is never emitted as a witness.
    assert ("P433096", "Q000376") not in pairs


def test_composite_without_mapping_is_skipped_not_guessed(tmp_path: Path) -> None:
    _write_catalogue(
        tmp_path,
        "noproj",
        {
            "Q111111": {
                "designation": "No witness list here",
                "exemplar_info": "BM 12345",  # museum no only, no P-numbers
            }
        },
    )
    conn = OraccCompositeWitnessesConnector(base=tmp_path)
    pairs = list(conn.extract(_FakeCtx()))
    # No cdli_id_numbers -> nothing fabricated from the prose museum number.
    assert pairs == []


def test_p_numbers_are_normalised_and_deduped(tmp_path: Path) -> None:
    # Same Q across two projects; one lists a non-padded P-number form.
    _write_catalogue(
        tmp_path,
        "a",
        {"Q000613": {"cdli_id_numbers": "P226092; P256242"}},
    )
    _write_catalogue(
        tmp_path,
        "b",
        {"Q000613": {"cdli_id_numbers": "P226092 ; P256242"}},
    )
    conn = OraccCompositeWitnessesConnector(base=tmp_path)
    pairs = {(r["p_number"], r["q_number"]) for r in conn.extract(_FakeCtx())}
    # The same witnesses listed in two projects collapse to one pair each.
    assert pairs == {("P226092", "Q000613"), ("P256242", "Q000613")}


def test_non_q_and_bad_json_are_ignored(tmp_path: Path) -> None:
    _write_catalogue(
        tmp_path,
        "mix",
        {
            "P999999": {"cdli_id_numbers": "P111111"},  # a P member, not a composite
            "Q222222": {"cdli_id_numbers": "P333333"},
        },
    )
    # A malformed catalogue must be skipped without crashing the scan.
    bad = tmp_path / "broken"
    bad.mkdir()
    (bad / "catalogue.json").write_text("{ not json", encoding="utf-8")

    conn = OraccCompositeWitnessesConnector(base=tmp_path)
    pairs = {(r["p_number"], r["q_number"]) for r in conn.extract(_FakeCtx())}
    assert pairs == {("P333333", "Q222222")}
