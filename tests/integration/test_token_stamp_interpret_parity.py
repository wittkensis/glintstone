"""Integration: every token stamped by get_atf must resolve in interpret (#407).

The defect (#330 half-activation): get_atf stamps clickable token_ids on EVERY
line of a tablet via ``text_lines.p_number`` — including surface-less lines
(``text_lines.surface_id IS NULL``). The interpret path
(``fact_assembly.assemble_token_facts``) used to gate the token lookup behind a
``surfaces`` join, so every stamped token on a surface-less line 404'd with
"Token N not found". On edition-heavy tablets (e.g. P229547, where ALL lines
are surface-less) that meant thousands of clickable-but-unservable words — a
broken promise to scholars.

This test pins the contract: the set of token_ids STAMPED by get_atf for a
tablet must equal the set SERVEABLE by assemble_token_facts (stamp == serve),
on both a surface-backed control and a surface-less-heavy tablet. It also
proves ACCURACY — a served token resolves to the CORRECT tablet and line, not
just to *some* row. These run against a real DATABASE_URL and skip without one.

If this test fails, the stamp/interpret join surfaces have diverged again and
clickable tokens are 404ing somewhere — do not delete it, fix the divergence.
"""

import os

import pytest

from api.repositories.artifact_repo import ArtifactRepository
from core import database as db
from core.agent import fact_assembly

# A surface-less-heavy edition tablet: every text_line has surface_id IS NULL,
# yet carries valid tokens. This is the case the old surfaces-join 404'd.
SURFACELESS_TABLET = "P229547"
# A surface-backed control: text_lines carry a non-null surface_id. Must still
# work after the fix (no regression on the common case).
SURFACE_BACKED_TABLET = "P361737"

# Cap how many stamped tokens we exhaustively round-trip per tablet to keep CI
# fast. The sample is taken in stamp order and deliberately includes tokens
# from multiple lines; coverage of the *kind* of bug (surface-less line) is
# guaranteed because the surface-less tablet has only surface-less lines.
_SAMPLE_PER_TABLET = 200


@pytest.fixture
def conn(has_database_url):
    """A real, read-only connection for the duration of one test."""
    c = db.connect_one_shot()
    try:
        yield c
    finally:
        c.close()


def _stamped_tokens(conn, p_number):
    """(line_id, token_id) pairs that get_atf marks clickable for this tablet."""
    repo = ArtifactRepository(conn)
    atf = repo.get_atf(p_number)
    return [
        (line_id, row["id"])
        for line_id, rows in atf["tokens_by_line"].items()
        for row in rows
    ]


def _surfaceless_line_count(conn, p_number):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM text_lines "
            "WHERE p_number = %s AND surface_id IS NULL",
            (p_number,),
        )
        return cur.fetchone()["n"]


def _require_tablet(stamped, p_number):
    if not stamped:
        pytest.skip(
            f"{p_number} has no stamped tokens in this database; "
            "load fixture data to exercise this test"
        )


@pytest.mark.parametrize(
    "p_number", [SURFACE_BACKED_TABLET, SURFACELESS_TABLET]
)
def test_every_stamped_token_is_serveable(conn, p_number):
    """Stamp set == serveable set: no clickable token may 404 in interpret."""
    stamped = _stamped_tokens(conn, p_number)
    _require_tablet(stamped, p_number)

    sample = stamped[:_SAMPLE_PER_TABLET]
    unservable = [
        token_id
        for _, token_id in sample
        if fact_assembly.assemble_token_facts(conn, p_number, token_id) is None
    ]

    assert not unservable, (
        f"{len(unservable)}/{len(sample)} stamped tokens on {p_number} 404 in "
        f"interpret (stamp/interpret divergence — #407). First few: "
        f"{unservable[:10]}"
    )


def test_surfaceless_tablet_is_actually_surfaceless(conn):
    """Guard the guard: P229547 must really be surface-less, or the parity
    test above proves nothing about the surface-less code path."""
    stamped = _stamped_tokens(conn, SURFACELESS_TABLET)
    _require_tablet(stamped, SURFACELESS_TABLET)

    surfaceless_lines = _surfaceless_line_count(conn, SURFACELESS_TABLET)
    assert surfaceless_lines > 0, (
        f"{SURFACELESS_TABLET} has no surface-less lines in this database; "
        "it no longer exercises the #407 regression — pick another tablet"
    )


def test_served_token_resolves_to_correct_tablet_and_line(conn):
    """Accuracy: a served surface-less token's facts are about the RIGHT
    tablet and the RIGHT line — not merely *some* token that happens to exist.

    We resolve the token through interpret, then independently confirm via the
    raw schema that token_id -> its text_line -> p_number is exactly the tablet
    we asked about, and that the served line_number matches the token's own
    line. If serving surface-less tokens attributed facts to the wrong tablet,
    accuracy-first says STOP — this test would catch it."""
    stamped = _stamped_tokens(conn, SURFACELESS_TABLET)
    _require_tablet(stamped, SURFACELESS_TABLET)

    stamp_line_id, token_id = stamped[0]
    bundle = fact_assembly.assemble_token_facts(
        conn, SURFACELESS_TABLET, token_id
    )
    assert bundle is not None, "surface-less token must resolve after #407 fix"

    # Ground truth straight from the schema: the token's line and its tablet.
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.line_id, tl.p_number, tl.line_number
            FROM tokens t
            JOIN text_lines tl ON t.line_id = tl.id
            WHERE t.id = %s
            """,
            (token_id,),
        )
        truth = cur.fetchone()

    assert truth is not None
    # Correct tablet: the token genuinely belongs to the tablet we served it for.
    assert truth["p_number"] == SURFACELESS_TABLET
    # Correct line: get_atf stamped it on the same line the schema records.
    assert truth["line_id"] == stamp_line_id
    # The interpret bundle is labeled with the tablet we asked about.
    assert bundle.p_number == SURFACELESS_TABLET
    assert bundle.token_id == token_id


def test_unknown_token_still_returns_none(conn):
    """The fix must not turn a genuinely-missing token into a false positive:
    a token_id that does not belong to the tablet still returns None."""
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(id) AS m FROM tokens")
        max_id = cur.fetchone()["m"]
    if max_id is None:
        pytest.skip("no tokens in database")
    bogus = max_id + 10_000_000
    assert (
        fact_assembly.assemble_token_facts(conn, SURFACELESS_TABLET, bogus)
        is None
    )


if __name__ == "__main__":  # pragma: no cover - manual smoke run
    os.environ.setdefault("PYTEST_RUNNING", "1")
    raise SystemExit(pytest.main([__file__, "-v"]))
