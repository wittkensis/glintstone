"""Single source of truth for per-artifact pipeline completeness.

Why this module exists (issue #257)
-----------------------------------
The 5-dot "pipeline completeness" badge is defined by the corpus-wide
``pipeline_completeness`` VIEW (migration 026). That view is built from CTEs
that each aggregate the *entire* corpus (text_lines / tokens / lemmatizations /
translations / entity_mentions — millions of rows). A ``p_number = ANY(...)``
predicate cannot push through the CTE boundary, so **any** hot path that reads
the view for a handful of artifacts recomputes corpus-wide completeness — ~9 s
on production — just to badge a few tablets.

Issue #255 worked around this for the search path by deriving the same five
flags with per-``p_number`` ``EXISTS`` / ratio subqueries that filter at the
base tables (index-driven via ``idx_tokens_line_id``, migration 048). That
dropped the stage from ~10 s to ~0.2 s.

#257 makes that the *durable* fix: this module is the ONE place the scoped SQL
lives, so no future per-artifact read can drift back onto the view. The flag
definitions are kept **byte-identical** to the view so the badge is unchanged:

  has_atf            : the tablet has any text line
  has_tokens         : it has any token
  has_lemmatization  : lemmatized-token ratio >= 0.5
  has_translation    : it has any line translation
  has_entities       : it has any entity mention
  completeness_score : sum of the five flags (0-5)

Semantics note: this is deliberately NOT the ``pipeline_status`` TABLE. That
table uses different stage definitions (e.g. linguistic = "has any lemma with a
citation_form", no entity stage at all) and would silently change what the
badge means. ``pipeline_status`` remains the source for the composites coverage
work and offline eval-set selection; it is not interchangeable with the badge.
"""

from __future__ import annotations

import psycopg
from psycopg.rows import DictRow

# The five flag definitions, scoped to a single p_number bound as %(p)s, kept
# byte-identical to the pipeline_completeness VIEW (migration 026).
_HAS_ATF = "EXISTS (SELECT 1 FROM text_lines tl WHERE tl.p_number = {p})"
_HAS_TOKENS = (
    "EXISTS (SELECT 1 FROM text_lines tl "
    "JOIN tokens t ON t.line_id = tl.id WHERE tl.p_number = {p})"
)
_HAS_LEMMATIZATION = (
    "(COALESCE(("
    "SELECT count(*) FILTER (WHERE lz.id IS NOT NULL)::float "
    "/ NULLIF(count(*), 0)::float "
    "FROM text_lines tl JOIN tokens t ON t.line_id = tl.id "
    "LEFT JOIN lemmatizations lz ON lz.token_id = t.id "
    "WHERE tl.p_number = {p}), 0.0) >= 0.5)"
)
_HAS_TRANSLATION = (
    "EXISTS (SELECT 1 FROM text_lines tl "
    "JOIN translations tn ON tn.line_id = tl.id WHERE tl.p_number = {p})"
)
_HAS_ENTITIES = (
    "EXISTS (SELECT 1 FROM entity_mentions em "
    "LEFT JOIN tokens t ON em.token_id = t.id "
    "LEFT JOIN text_lines tl_t ON t.line_id = tl_t.id "
    "LEFT JOIN text_lines tl_l ON em.line_id = tl_l.id "
    "WHERE COALESCE(tl_t.p_number, tl_l.p_number) = {p})"
)

# Ordered list of (column, expr) so completeness_score is always the sum of the
# same five flags in the same order the view defines.
_FLAGS = [
    ("has_atf", _HAS_ATF),
    ("has_tokens", _HAS_TOKENS),
    ("has_lemmatization", _HAS_LEMMATIZATION),
    ("has_translation", _HAS_TRANSLATION),
    ("has_entities", _HAS_ENTITIES),
]

# The five flag-bearing stages, in badge order. Public so callers that render
# a dot-array (e.g. search hydration) stay aligned with the score definition.
STAGE_COLUMNS = [c for c, _ in _FLAGS]


def flag_columns(p_expr: str, *, with_score: bool = True) -> str:
    """SELECT-list of the five flags (and optionally completeness_score).

    ``p_expr`` is the SQL expression that yields the p_number to score — a bind
    placeholder like ``%(p)s`` for a single-artifact query, or a column
    reference like ``ps.p_number`` for a set-scoped query. Centralizing this
    here is what keeps every per-artifact completeness read byte-identical.
    """
    cols = [f"{expr.format(p=p_expr)}::int AS {col}" for col, expr in _FLAGS]
    if with_score:
        score = " + ".join(f"({expr.format(p=p_expr)})::int" for _, expr in _FLAGS)
        cols.append(f"({score}) AS completeness_score")
    return ",\n    ".join(cols)


def _flag_columns(p_placeholder: str) -> str:
    return flag_columns(p_placeholder, with_score=True)


# Single-artifact query (replaces the per-artifact pipeline_completeness VIEW
# read in fact_assembly). Bind %(p)s = p_number.
SINGLE_SQL = f"SELECT\n    {_flag_columns('%(p)s')}"


def fetch_completeness(
    conn: psycopg.Connection[DictRow], p_number: str
) -> dict[str, int]:
    """Return the five flags + completeness_score for one artifact.

    Index-driven scoped subqueries — O(1)-ish per artifact, never a corpus
    recompute. Byte-identical to the pipeline_completeness VIEW.
    """
    with conn.cursor() as cur:
        cur.execute(SINGLE_SQL, {"p": p_number})
        return cur.fetchone() or {}
