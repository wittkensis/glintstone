"""Assemble structured fact lists for grounded synthesis.

This is the data-collection step that runs before the Claude call. Every Fact
carries (n, text, citation) so the synthesis call can reference it by number
and the validator can confirm round-trip integrity.

Three assemblers:
  assemble_artifact_facts(p_number, focus)          → for summarize_artifact
  assemble_token_facts(p_number, token_id)          → for interpret_token
  assemble_line_facts(p_number, surface, line_num)  → for suggest_line_translation

All query the DB via the existing repository layer where possible to stay
inside the project's idiom. They return dataclasses, not SQL rows — the
synthesis layer renders them to numbered prompt text.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

import psycopg

from core.schemas.citation import Citation

logger = logging.getLogger(__name__)


@dataclass
class Fact:
    n: int
    text: str
    citation: Citation


@dataclass
class SimilarTablet:
    n: int  # citation slot
    p_number: str
    designation: str | None
    period: str | None
    provenience: str | None
    cosine: float


@dataclass
class ArtifactFactBundle:
    p_number: str
    facts: list[Fact] = field(default_factory=list)
    similar_tablets: list[SimilarTablet] = field(default_factory=list)
    completeness_score: int = 0
    best_guess_allowed: bool = False


@dataclass
class TokenFactBundle:
    p_number: str
    token_id: int
    facts: list[Fact] = field(default_factory=list)
    is_fully_lemmatized: bool = False


@dataclass
class LineFactBundle:
    p_number: str
    line_id: int | None
    surface_name: str
    line_number: str  # ATF line number string e.g. "4" or "3'"
    atf_text: str  # raw ATF of the target line
    language: str
    dialect: str | None
    is_mixed_language: bool
    language_shift_position: int | None
    language_supported: bool
    context_variant: str  # "a" | "b"
    facts: list[Fact] = field(default_factory=list)
    token_rows: list[dict] = field(default_factory=list)  # raw DB token rows
    missing_layers: list[str] = field(default_factory=list)
    surface_atf: str | None = None  # full surface ATF for variant B


# ── Helpers ───────────────────────────────────────────────────────────────────


def _next_n(facts: list[Fact]) -> int:
    return (facts[-1].n + 1) if facts else 1


def _add_fact(
    facts: list[Fact],
    text: str,
    source_kind: str,
    source_id: int | str,
    retrieval_field: str,
    annotation_run_id: int | None = None,
    scholar_id: int | None = None,
    scholar_name: str | None = None,
    publication_short: str | None = None,
) -> Fact:
    n = _next_n(facts)
    citation = Citation(
        n=n,
        source_kind=source_kind,
        source_id=source_id,
        annotation_run_id=annotation_run_id,
        scholar_id=scholar_id,
        scholar_name=scholar_name,
        publication_short=publication_short,
        retrieval_field=retrieval_field,
    )
    fact = Fact(n=n, text=text, citation=citation)
    facts.append(fact)
    return fact


# ── Artifact facts ────────────────────────────────────────────────────────────


def assemble_artifact_facts(
    conn: psycopg.Connection,
    p_number: str,
    focus: Literal["general", "research", "translation_status"] = "general",
    similar_tablet_min_cosine: float = 0.72,
    similar_tablet_count: int = 5,
) -> ArtifactFactBundle | None:
    """Pull every fact about the artifact that the synthesizer can ground on."""
    bundle = ArtifactFactBundle(p_number=p_number)

    # Catalog facts (period, provenience, language, museum)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.p_number, a.designation,
                   a.period_normalized, a.provenience_normalized,
                   a.language_normalized,
                   a.museum_no
            FROM artifacts a
            WHERE a.p_number = %s
            """,
            (p_number,),
        )
        row = cur.fetchone()
        if not row:
            return None

    # Fix 2d: append "(CDLI catalog)" source tag to each catalog-derived fact so the
    # synthesizer and readers can trace provenance without opening citations.
    if row.get("period_normalized"):
        _add_fact(
            bundle.facts,
            f"period: {row['period_normalized']} (CDLI catalog)",
            "annotation_run",
            "cdli_catalog",
            "period",
        )
    if row.get("provenience_normalized"):
        _add_fact(
            bundle.facts,
            f"provenience: {row['provenience_normalized']} (CDLI catalog)",
            "annotation_run",
            "cdli_catalog",
            "provenience",
        )
    if row.get("museum_no"):
        _add_fact(
            bundle.facts,
            f"museum: {row['museum_no']} (CDLI catalog)",
            "annotation_run",
            "cdli_catalog",
            "museum",
        )
    if row.get("designation"):
        _add_fact(
            bundle.facts,
            f"designation: {row['designation']} (CDLI catalog)",
            "annotation_run",
            "cdli_catalog",
            "designation",
        )

    # Genre facts (canonical genres via junction table, primary first).
    # genre_normalized is the canonical form; fall back to raw genre if absent.
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cg.name, ag.is_primary
            FROM artifact_genres ag
            JOIN canonical_genres cg ON cg.id = ag.genre_id
            WHERE ag.p_number = %s
            ORDER BY ag.is_primary DESC, cg.name
            LIMIT 3
            """,
            (p_number,),
        )
        genre_rows = cur.fetchall()

    if genre_rows:
        genre_names = [r["name"] for r in genre_rows]
        _add_fact(
            bundle.facts,
            f"genre: {', '.join(genre_names)} (CDLI catalog)",
            "annotation_run",
            "cdli_catalog",
            "genre",
        )

    # Language and dialect facts.
    # Base language from catalog; rendered with ISO code where available from lemmatization data.
    # Format: "primary language: Sumerian (sux)" mirrors ORACC display conventions.
    if row.get("language_normalized"):
        lang_label = row["language_normalized"]
        # Map common normalized language names to ISO/ORACC codes for scholars
        _LANG_CODE_MAP = {
            "Sumerian": "sux",
            "Akkadian": "akk",
            "Elamite": "elx",
            "Hurrian": "hur",
            "Hittite": "hit",
            "Ugaritic": "uga",
            "Eblaite": "xeb",
        }
        iso_code = _LANG_CODE_MAP.get(lang_label)
        if iso_code:
            lang_label = f"{lang_label} ({iso_code})"
        _add_fact(
            bundle.facts,
            f"primary language: {lang_label} (CDLI catalog)",
            "annotation_run",
            "cdli_catalog",
            "language_normalized",
        )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT lz.language
            FROM tokens t
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN surfaces s ON tl.surface_id = s.id
            JOIN lemmatizations lz ON lz.token_id = t.id
            WHERE s.p_number = %s
              AND lz.language IS NOT NULL
            """,
            (p_number,),
        )
        lang_rows = [r["language"] for r in cur.fetchall()]

    if lang_rows:
        # Detect Akkadian dialect variants (akk-x-* subtags)
        dialects = sorted({lc for lc in lang_rows if lc.startswith("akk-x-")})
        if dialects:
            _add_fact(
                bundle.facts,
                f"Akkadian dialect(s) attested: {', '.join(dialects)} (ORACC)",
                "annotation_run",
                "oracc_lemmatization",
                "dialect",
            )

        # Mixed-language flag: both Sumerian and Akkadian lemmatizations present
        has_sumerian = any(lc.startswith("sux") for lc in lang_rows)
        has_akkadian = any(lc.startswith("akk") for lc in lang_rows)
        if has_sumerian and has_akkadian:
            _add_fact(
                bundle.facts,
                "mixed language: Sumerian and Akkadian lemmatizations coexist in this text (ORACC)",
                "annotation_run",
                "oracc_lemmatization",
                "mixed_language",
            )

    # Composite membership (Q-number and sibling exemplars)
    with conn.cursor() as cur:
        try:
            cur.execute(
                """
                SELECT c.q_number, c.designation, c.exemplar_count
                FROM artifact_composites ac
                JOIN composites c ON c.q_number = ac.q_number
                WHERE ac.p_number = %s
                """,
                (p_number,),
            )
            composite = cur.fetchone()
        except psycopg.errors.UndefinedTable:
            conn.rollback()
            composite = None

    if composite:
        _add_fact(
            bundle.facts,
            f"part of composite {composite['q_number']} "
            f"({composite.get('designation') or 'untitled'}; "
            f"{composite.get('exemplar_count') or '?'} known exemplars)",
            "annotation_run",
            "cdli_catalog",
            f"composite:{composite['q_number']}",
        )
        # Best-attested sibling (highest pipeline completeness among exemplars)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ac2.p_number, pc.completeness_score, a.designation
                FROM artifact_composites ac2
                JOIN pipeline_completeness pc ON pc.p_number = ac2.p_number
                JOIN artifacts a ON a.p_number = ac2.p_number
                WHERE ac2.q_number = %s
                  AND ac2.p_number <> %s
                ORDER BY pc.completeness_score DESC
                LIMIT 1
                """,
                (composite["q_number"], p_number),
            )
            best_sibling = cur.fetchone()
        if best_sibling and best_sibling.get("completeness_score", 0) > 0:
            _add_fact(
                bundle.facts,
                f"best-attested sibling exemplar: {best_sibling['p_number']} "
                f"({best_sibling.get('designation') or 'unnamed'}, "
                f"completeness {best_sibling['completeness_score']}/5)",
                "computed",
                "pipeline_completeness",
                f"sibling:{best_sibling['p_number']}",
            )

    # Pipeline completeness
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT completeness_score, has_atf, has_tokens, has_lemmatization,
                   has_translation, has_entities, has_image, token_count, lemma_ratio
            FROM pipeline_completeness
            WHERE p_number = %s
            """,
            (p_number,),
        )
        pc = cur.fetchone() or {}

    completeness = int(pc.get("completeness_score", 0))
    bundle.completeness_score = completeness
    stages_done = []
    if pc.get("has_atf"):
        stages_done.append("ATF")
    if pc.get("has_tokens"):
        stages_done.append("tokens")
    if pc.get("has_lemmatization"):
        stages_done.append("lemmatization")
    if pc.get("has_translation"):
        stages_done.append("translation")
    if pc.get("has_entities"):
        stages_done.append("named entities")

    _add_fact(
        bundle.facts,
        f"pipeline completeness: {completeness}/5 ({', '.join(stages_done) or 'none of the stages completed'})",
        "computed",
        "pipeline_completeness",
        "completeness",
    )

    # Top lemmas (when lemmatized) — emit up to 5.
    # Fix 2f: append (uncertain) when annotation_runs.trust < 0.7 if column exists.
    # The trust column may not be present (see LEARNINGS.md) — catch UndefinedColumn gracefully.
    with conn.cursor() as cur:
        try:
            cur.execute(
                """
                SELECT lz.citation_form, lz.guide_word, COUNT(*) AS attestations,
                       bool_or(ar.trust IS NOT NULL AND ar.trust < 0.7) AS any_uncertain
                FROM tokens t
                JOIN text_lines tl ON t.line_id = tl.id
                JOIN surfaces s ON tl.surface_id = s.id
                JOIN lemmatizations lz ON lz.token_id = t.id
                LEFT JOIN annotation_runs ar ON ar.id = lz.annotation_run_id
                WHERE s.p_number = %s AND lz.citation_form IS NOT NULL
                GROUP BY lz.citation_form, lz.guide_word
                ORDER BY attestations DESC
                LIMIT 5
                """,
                (p_number,),
            )
            for r in cur.fetchall():
                uncertain_tag = " (uncertain)" if r.get("any_uncertain") else ""
                cf = r.get("citation_form", "")
                _add_fact(
                    bundle.facts,
                    f'mentions lemma "{r.get("guide_word") or cf}" '
                    f"({r.get('attestations')} attestations){uncertain_tag} (ORACC)",
                    "lexical_lemma",
                    cf,
                    f"lemma:{cf}",
                )
        except psycopg.errors.UndefinedColumn:
            # annotation_runs.trust column not yet added (migration pending) — fall back without trust signal
            conn.rollback()
            cur.execute(
                """
                SELECT lz.citation_form, lz.guide_word, COUNT(*) AS attestations
                FROM tokens t
                JOIN text_lines tl ON t.line_id = tl.id
                JOIN surfaces s ON tl.surface_id = s.id
                JOIN lemmatizations lz ON lz.token_id = t.id
                WHERE s.p_number = %s AND lz.citation_form IS NOT NULL
                GROUP BY lz.citation_form, lz.guide_word
                ORDER BY attestations DESC
                LIMIT 5
                """,
                (p_number,),
            )
            for r in cur.fetchall():
                cf = r.get("citation_form", "")
                _add_fact(
                    bundle.facts,
                    f'mentions lemma "{r.get("guide_word") or cf}" '
                    f"({r.get('attestations')} attestations) (ORACC)",
                    "lexical_lemma",
                    cf,
                    f"lemma:{cf}",
                )

    # Competing lemmatizations — tokens where >1 annotation_run offers a different reading.
    # Signals scholarly disagreement; the synthesizer should flag uncertainty.
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.raw_form, COUNT(DISTINCT lz.annotation_run_id) AS run_count,
                   array_agg(DISTINCT lz.guide_word ORDER BY lz.guide_word) AS readings
            FROM tokens t
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN surfaces s ON tl.surface_id = s.id
            JOIN lemmatizations lz ON lz.token_id = t.id
            WHERE s.p_number = %s AND lz.citation_form IS NOT NULL
            GROUP BY t.id, t.raw_form
            HAVING COUNT(DISTINCT lz.annotation_run_id) > 1
            ORDER BY run_count DESC
            LIMIT 3
            """,
            (p_number,),
        )
        competing = cur.fetchall()

    if competing:
        examples = "; ".join(
            f'"{r["raw_form"]}" read as {"/".join(r["readings"] or [])}'
            for r in competing
        )
        _add_fact(
            bundle.facts,
            f"scholarly disagreement on {len(competing)} token(s): {examples} (ORACC)",
            "annotation_run",
            "oracc_lemmatization",
            "competing_lemmatizations",
        )

    # Named entities (when populated) — up to 5
    with conn.cursor() as cur:
        try:
            cur.execute(
                """
                SELECT DISTINCT ne.id, ne.canonical_name, ne.entity_type
                FROM entity_mentions em
                JOIN named_entities ne ON em.entity_id = ne.id
                LEFT JOIN tokens t ON em.token_id = t.id
                LEFT JOIN text_lines tl_t ON t.line_id = tl_t.id
                LEFT JOIN text_lines tl_l ON em.line_id = tl_l.id
                JOIN surfaces s ON s.id = COALESCE(tl_t.surface_id, tl_l.surface_id)
                WHERE s.p_number = %s
                LIMIT 5
                """,
                (p_number,),
            )
            for r in cur.fetchall():
                _add_fact(
                    bundle.facts,
                    f'mentions named entity "{r["canonical_name"]}" ({r.get("entity_type") or "unknown"})',
                    "named_entity",
                    r["id"],
                    f"entity:{r['id']}",
                )
        except (psycopg.errors.UndefinedTable, psycopg.errors.UndefinedColumn):
            # named_entities not yet populated; skip
            conn.rollback()

    # Citation count (research-importance signal)
    with conn.cursor() as cur:
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM publication_citations pc
                WHERE pc.p_number = %s
                """,
                (p_number,),
            )
            row = cur.fetchone()
            if row and row.get("n", 0) > 0:
                _add_fact(
                    bundle.facts,
                    f"cited in {row['n']} publications",
                    "computed",
                    "publication_citations",
                    "citation_count",
                )
        except (psycopg.errors.UndefinedTable, psycopg.errors.UndefinedColumn):
            conn.rollback()

    # Similar tablets via embedding.
    # Primary: artifact_lemma_bag (requires lemmatization). Fallback: artifact_designation
    # (text embedding of the designation string; available for most artifacts, threshold 0.65).
    _embedding_query = """
        WITH this_vec AS (
            SELECT vec
            FROM entity_embeddings
            WHERE entity_type = %s
              AND entity_id = %s
              AND model = 'voyage-3-large'
            LIMIT 1
        )
        SELECT ee.entity_id AS p_number,
               a.designation, a.period_normalized, a.provenience_normalized,
               1 - (ee.vec <=> tv.vec) AS cosine
        FROM entity_embeddings ee, this_vec tv
        JOIN artifacts a ON a.p_number = ee.entity_id
        WHERE ee.entity_type = %s
          AND ee.model = 'voyage-3-large'
          AND ee.entity_id <> %s
        ORDER BY ee.vec <=> tv.vec
        LIMIT %s
    """

    def _load_similar(cur: psycopg.Cursor, entity_type: str, min_cosine: float) -> None:
        cur.execute(
            _embedding_query,
            (entity_type, p_number, entity_type, p_number, similar_tablet_count),
        )
        for r in cur.fetchall():
            if (r.get("cosine") or 0) < min_cosine:
                continue
            n = _next_n(bundle.facts)
            citation = Citation(
                n=n,
                source_kind="computed",
                source_id=f"similar:{r['p_number']}",
                retrieval_field=f"similar_tablet:{r['p_number']}",
            )
            fact = Fact(
                n=n,
                text=(
                    f"{r['p_number']} — "
                    f"{r.get('period_normalized') or 'unknown period'}, "
                    f"{r.get('provenience_normalized') or 'unknown provenience'}; "
                    f"cosine {r['cosine']:.2f}"
                ),
                citation=citation,
            )
            bundle.facts.append(fact)
            bundle.similar_tablets.append(
                SimilarTablet(
                    n=n,
                    p_number=r["p_number"],
                    designation=r.get("designation"),
                    period=r.get("period_normalized"),
                    provenience=r.get("provenience_normalized"),
                    cosine=r["cosine"],
                )
            )

    with conn.cursor() as cur:
        try:
            _load_similar(cur, "artifact_lemma_bag", similar_tablet_min_cosine)
            if not bundle.similar_tablets:
                # Sparse tablet: try designation embedding at a lower threshold
                _load_similar(cur, "artifact_designation", 0.65)
        except (psycopg.errors.UndefinedTable, psycopg.errors.UndefinedFunction):
            conn.rollback()

    # Best-guess gate: completeness ≤ 2 AND ≥3 similar tablets found via either embedding type
    bundle.best_guess_allowed = completeness <= 2 and len(bundle.similar_tablets) >= 3

    return bundle


# ── Token facts ───────────────────────────────────────────────────────────────


def assemble_token_facts(
    conn: psycopg.Connection,
    p_number: str,
    token_id: int,
) -> TokenFactBundle | None:
    """Pull token + neighbor + sign-candidate + genre-prior facts."""
    bundle = TokenFactBundle(p_number=p_number, token_id=token_id)

    # Token itself
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.raw_form, t.position, t.line_id,
                   tl.line_number,
                   a.period_normalized AS period,
                   a.provenience_normalized AS provenience
            FROM tokens t
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN surfaces s ON tl.surface_id = s.id
            JOIN artifacts a ON s.p_number = a.p_number
            WHERE t.id = %s AND s.p_number = %s
            """,
            (token_id, p_number),
        )
        token = cur.fetchone()
        if not token:
            return None

    _add_fact(
        bundle.facts,
        f"raw form: {token['raw_form']}",
        "annotation_run",
        "atf_parser",
        "raw_form",
    )

    # Existing lemmatization (if any) — if present, this is a complete chain walk
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT lz.id AS lemmatization_id, lz.id AS lemma_id,
                   lz.citation_form, lz.guide_word, lz.pos,
                   lz.annotation_run_id
            FROM lemmatizations lz
            WHERE lz.token_id = %s AND lz.citation_form IS NOT NULL
            LIMIT 1
            """,
            (token_id,),
        )
        lem = cur.fetchone()

    if lem:
        bundle.is_fully_lemmatized = True
        _add_fact(
            bundle.facts,
            f'lemma: {lem["citation_form"]} ("{lem.get("guide_word") or "—"}", '
            f"{lem.get('pos') or 'unknown POS'})",
            "lexical_lemma",
            lem["lemma_id"],
            f"lemma:{lem['lemma_id']}",
            annotation_run_id=lem.get("annotation_run_id"),
        )

    # Neighbor context — 3 tokens before/after
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.raw_form, t.position,
                   lz.citation_form, lz.guide_word
            FROM tokens t
            LEFT JOIN lemmatizations lz ON lz.token_id = t.id AND lz.citation_form IS NOT NULL
            WHERE t.line_id = %s
              AND t.id <> %s
              AND ABS(t.position - %s) <= 3
            ORDER BY t.position
            """,
            (token["line_id"], token_id, token["position"]),
        )
        neighbors = cur.fetchall()

    for n_row in neighbors:
        offset = n_row["position"] - token["position"]
        lemma_label = (
            f' → lemma "{n_row.get("guide_word") or n_row["citation_form"]}"'
            if n_row.get("citation_form")
            else ""
        )
        _add_fact(
            bundle.facts,
            f'neighbor (position {offset:+d}): "{n_row["raw_form"]}"{lemma_label}',
            "annotation_run",
            "atf_parser",
            f"neighbor:{offset:+d}",
        )

    # Artifact context (period, provenience, genre)
    _add_fact(
        bundle.facts,
        f"artifact period: {token.get('period') or 'unknown'}",
        "annotation_run",
        "cdli_catalog",
        "period",
    )
    _add_fact(
        bundle.facts,
        f"artifact provenience: {token.get('provenience') or 'unknown'}",
        "annotation_run",
        "cdli_catalog",
        "provenience",
    )

    # Sign candidate readings (if no lemmatization)
    if not bundle.is_fully_lemmatized:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT ls.id AS sign_id, ls.sign_name, ll.id AS lemma_id,
                           ll.citation_form, ll.guide_word,
                           lsla.attestation_count
                    FROM lexical_sign_lemma_assoc lsla
                    JOIN lexical_signs ls ON ls.id = lsla.sign_id
                    JOIN lexical_lemmas ll ON ll.id = lsla.lemma_id
                    WHERE ls.sign_name = ANY(
                        SELECT regexp_split_to_table(%s, '[-.]')
                    )
                    ORDER BY lsla.attestation_count DESC NULLS LAST
                    LIMIT 5
                    """,
                    (token["raw_form"],),
                )
                for r in cur.fetchall():
                    _add_fact(
                        bundle.facts,
                        f'candidate sign reading: "{r["sign_name"]}" → '
                        f'lemma "{r.get("guide_word") or r["citation_form"]}" '
                        f"({r.get('attestation_count') or 0} attestations)",
                        "lexical_lemma",
                        r["lemma_id"],
                        f"sign_candidate:{r['sign_id']}",
                    )
            except (psycopg.errors.UndefinedTable, psycopg.errors.UndefinedColumn):
                conn.rollback()

    return bundle


# ── Line translation fact assembly ────────────────────────────────────────────

_SUPPORTED_LANG_PREFIXES = ("sumerian", "akkadian")

_DETERMINATIVE_RE = __import__("re").compile(r"\{[^}]+\}")

_GENRE_B_VARIANTS = frozenset(
    ["literary", "letter", "royal/monumental", "royal inscription", "lexical"]
)


def _language_supported_str(language: str) -> bool:
    lang_lc = language.lower()
    return any(lang_lc.startswith(p) for p in _SUPPORTED_LANG_PREFIXES)


def _should_use_variant_b(genre: str | None) -> bool:
    if not genre:
        return False
    return any(g in genre.lower() for g in _GENRE_B_VARIANTS)


def assemble_line_facts(
    conn: psycopg.Connection,
    p_number: str,
    surface_name: str,
    line_number: str,
    session_variant: str | None = None,  # "a"|"b"|None (None=auto)
) -> LineFactBundle | None:
    """Assemble facts for suggest_line_translation.

    Returns None if the line cannot be found.

    context_variant:
      a = target line + ±2 neighbor lines (default for administrative genre)
      b = full surface ATF, middle-truncated (for literary/epistolary)
    """
    bundle_facts: list[Fact] = []

    # 1. Resolve line from DB
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tl.id AS line_id,
                   tl.raw_atf,
                   tl.line_number,
                   s.id AS surface_id,
                   s.surface_type AS surface_name,
                   a.language_normalized,
                   a.period_normalized,
                   -- Fix 2a: prefer genre_normalized (canonical form) over raw genre string
                   a.genre AS genre
            FROM text_lines tl
            JOIN surfaces s ON s.id = tl.surface_id
            JOIN artifacts a ON a.p_number = s.p_number
            WHERE s.p_number = %s
              AND s.surface_type ILIKE %s
              AND (tl.line_number::text = %s OR tl.raw_atf ILIKE %s)
            ORDER BY tl.line_number
            LIMIT 1
            """,
            (p_number, surface_name, line_number, f"{line_number}.%"),
        )
        row = cur.fetchone()

    if not row:
        # Fallback: match by position number only
        try:
            pos_int = int(line_number.replace("'", ""))
        except ValueError:
            return None
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tl.id AS line_id,
                       tl.raw_atf,
                       tl.line_number,
                       s.id AS surface_id,
                       s.surface_type AS surface_name,
                       a.language_normalized,
                       a.period_normalized,
                       -- Fix 2a: prefer genre_normalized (canonical form) over raw genre string
                       a.genre AS genre
                FROM text_lines tl
                JOIN surfaces s ON s.id = tl.surface_id
                JOIN artifacts a ON a.p_number = s.p_number
                WHERE s.p_number = %s AND s.surface_type ILIKE %s
                ORDER BY ABS(tl.line_number - %s)
                LIMIT 1
                """,
                (p_number, surface_name, pos_int),
            )
            row = cur.fetchone()

    if not row:
        return None

    line_id: int = row["line_id"]
    atf_text: str = row["atf_text"] or ""
    surface_id: int = row["surface_id"]
    language: str = row["language_normalized"] or "Unknown"
    period: str | None = row["period_normalized"]
    genre: str | None = row["genre"]
    position: int = row["position"]

    # 2. Missing layer analysis (server-computed, not model-generated)
    missing_layers: list[str] = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(t.id) AS token_count,
                COUNT(lz.id) AS lemma_count
            FROM text_lines tl
            JOIN tokens t ON t.line_id = tl.id
            LEFT JOIN lemmatizations lz ON lz.token_id = t.id
            WHERE tl.id = %s
            """,
            (line_id,),
        )
        counts = cur.fetchone() or {}

    token_count = counts.get("token_count", 0) or 0
    lemma_count = counts.get("lemma_count", 0) or 0

    if token_count == 0:
        missing_layers.append("No tokenization — line parsed as raw ATF only")
    elif lemma_count == 0:
        missing_layers.append(
            f"Lemmatization missing for all {token_count} token(s) — suggestions inferred from sign candidates"
        )
    elif lemma_count < token_count:
        gap = token_count - lemma_count
        missing_layers.append(
            f"Lemmatization missing for {gap} of {token_count} token(s)"
        )

    # 3. Determine context variant
    auto_variant = "b" if _should_use_variant_b(genre) else "a"
    context_variant = session_variant if session_variant in ("a", "b") else auto_variant

    # 4. Catalog facts (period, language, genre)
    if period:
        _add_fact(
            bundle_facts,
            f"period: {period}",
            "annotation_run",
            "cdli_catalog",
            "period",
        )
    if genre:
        _add_fact(
            bundle_facts, f"genre: {genre}", "annotation_run", "cdli_catalog", "genre"
        )
    _add_fact(
        bundle_facts,
        f"language: {language}",
        "annotation_run",
        "cdli_catalog",
        "language",
    )

    # 5. Target line fact
    # Strip ATF line number prefix if present (e.g. "4. i-na ṭup-pi-im" → "i-na ṭup-pi-im")
    atf_clean = __import__("re").sub(r"^\s*\d+'?\.\s*", "", atf_text).strip()
    _add_fact(
        bundle_facts,
        f"TARGET LINE (line {line_number}, {surface_name}): {atf_clean or atf_text}",
        "annotation_run",
        p_number,
        "atf_text",
    )

    # 6. Context variant A: neighbor lines (±2)
    surface_atf: str | None = None
    if context_variant == "a":
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tl.line_number, tl.raw_atf
                FROM text_lines tl
                WHERE tl.surface_id = %s
                  AND tl.line_number BETWEEN %s AND %s
                  AND tl.id != %s
                ORDER BY tl.line_number
                """,
                (surface_id, position - 2, position + 2, line_id),
            )
            neighbors = cur.fetchall()
        for nb in neighbors:
            direction = "before" if nb["position"] < position else "after"
            nb_text = (
                __import__("re")
                .sub(r"^\s*\d+'?\.\s*", "", nb["atf_text"] or "")
                .strip()
            )
            _add_fact(
                bundle_facts,
                f"neighbor line ({direction}, pos {nb['position']}): {nb_text}",
                "annotation_run",
                p_number,
                f"neighbor_line:{nb['position']}",
            )
    else:
        # Variant B: full surface ATF (middle-truncated, ends preserved)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT string_agg(atf_text, E'\n' ORDER BY position) AS full_atf
                FROM text_lines
                WHERE surface_id = %s
                """,
                (surface_id,),
            )
            full_row = cur.fetchone()
        full_atf = (full_row["full_atf"] or "") if full_row else ""
        # Keep first 800 + last 400 chars; drop middle
        if len(full_atf) > 1300:
            omitted = len(full_atf) - 1200
            surface_atf = (
                full_atf[:800]
                + f"\n[... {omitted} chars omitted ...]\n"
                + full_atf[-400:]
            )
        else:
            surface_atf = full_atf
        _add_fact(
            bundle_facts,
            f"full surface ATF (variant B context):\n{surface_atf}",
            "annotation_run",
            p_number,
            "surface_atf",
        )

    # 7. Token data with determinative extraction
    token_rows: list[dict] = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id AS token_id,
                       t.raw_form,
                       lz.id AS lemma_id_on_lz,
                       ll.citation_form,
                       lz.guide_word,
                       lz.pos,
                       lz.language AS lz_language
                FROM tokens t
                LEFT JOIN lemmatizations lz ON lz.token_id = t.id AND lz.citation_form IS NOT NULL
                WHERE t.line_id = %s
                ORDER BY t.id
                """,
                (line_id,),
            )
            token_rows = [dict(r) for r in cur.fetchall()]

        for tr in token_rows:
            raw = tr.get("raw_form") or ""
            is_det = bool(_DETERMINATIVE_RE.match(raw))
            tr["is_determinative"] = is_det

            if is_det:
                det_type = raw.strip("{}")
                _add_fact(
                    bundle_facts,
                    f"determinative {raw} on token {tr['token_id']} — likely {det_type} category classifier",
                    "annotation_run",
                    p_number,
                    f"determinative:{tr['token_id']}",
                )
            elif tr.get("citation_form"):
                _add_fact(
                    bundle_facts,
                    f"token {tr['token_id']} ({raw}): lemma={tr['citation_form']}, meaning={tr.get('guide_word') or 'unknown'}",
                    "annotation_run",
                    p_number,
                    f"lemma:{tr['token_id']}",
                )
            else:
                _add_fact(
                    bundle_facts,
                    f"token {tr['token_id']} ({raw}): not yet lemmatized",
                    "annotation_run",
                    p_number,
                    f"token:{tr['token_id']}",
                )
    except (psycopg.errors.UndefinedColumn, psycopg.errors.UndefinedTable):
        conn.rollback()
        missing_layers.append(
            "Token data unavailable (schema not available in this environment)"
        )

    # 8. Dialect detection
    dialect: str | None = None
    is_mixed = False
    lang_shift_pos: int | None = None
    lz_langs = {tr.get("lz_language") for tr in token_rows if tr.get("lz_language")}
    if lz_langs:
        dialects = sorted(
            lz for lz in lz_langs if isinstance(lz, str) and lz.startswith("akk-x-")
        )
        if dialects:
            dialect = dialects[0]
        has_sux = any(isinstance(lc, str) and lc.startswith("sux") for lc in lz_langs)
        has_akk = any(isinstance(lc, str) and lc.startswith("akk") for lc in lz_langs)
        is_mixed = has_sux and has_akk

    return LineFactBundle(
        p_number=p_number,
        line_id=line_id,
        surface_name=surface_name,
        line_number=line_number,
        atf_text=atf_text,
        language=language,
        dialect=dialect,
        is_mixed_language=is_mixed,
        language_shift_position=lang_shift_pos,
        language_supported=_language_supported_str(language),
        context_variant=context_variant,
        facts=bundle_facts,
        token_rows=token_rows,
        missing_layers=missing_layers,
        surface_atf=surface_atf,
    )
