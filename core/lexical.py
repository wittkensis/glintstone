#!/usr/bin/env python3
"""
Unified lexical resource API for token exploration and full-chain retrieval.

Provides functions for:
- Looking up lemmas by token form
- Retrieving senses and signs for lemmas
- Full chain retrieval (Sign → Lemmas → Senses)
- Token integration (form → lexical context)
"""

from typing import List, Dict, Optional
import psycopg
from psycopg.rows import dict_row
from core.config import get_settings


# ============================================================================
# DATABASE CONNECTION
# ============================================================================


def get_connection() -> psycopg.Connection:
    """Get database connection with dict_row factory."""
    settings = get_settings()
    return psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=dict_row,
    )


# ============================================================================
# BASIC LOOKUPS
# ============================================================================


def lookup_lemmas_by_form(
    form: str, language: str = "sux", source: Optional[str] = None
) -> List[Dict]:
    """
    Find all lemmas matching a token form.

    Args:
        form: Citation form to search for (e.g., "lugal", "šarru")
        language: Language code (sux, akk, elx, xhu, hit, uga)
        source: Optional source filter (epsd2, oracc/dcclt, etc.)

    Returns:
        List of lemma dicts with sense_count and sign_count
    """
    conn = get_connection()

    query = """
        SELECT
            l.*,
            COUNT(DISTINCT s.id) as sense_count,
            COUNT(DISTINCT sla.sign_id) as sign_count
        FROM lexical_lemmas l
        LEFT JOIN lexical_senses s ON l.id = s.lemma_id
        LEFT JOIN lexical_sign_lemma_associations sla ON l.id = sla.lemma_id
        WHERE l.citation_form = %s
          AND l.language_code = %s
    """

    params = [form, language]

    if source:
        query += " AND l.source = %s"
        params.append(source)

    query += """
        GROUP BY l.id
        ORDER BY l.attestation_count DESC NULLS LAST
    """

    with conn:
        results = conn.execute(query, params).fetchall()

    return results


def get_lemma_senses(lemma_id: int) -> List[Dict]:
    """
    Get all senses for a lemma (polysemy).

    Args:
        lemma_id: ID of the lemma

    Returns:
        List of sense dicts ordered by sense_number
    """
    conn = get_connection()

    with conn:
        return conn.execute(
            """
            SELECT * FROM lexical_senses
            WHERE lemma_id = %s
            ORDER BY sense_number
            """,
            (lemma_id,),
        ).fetchall()


def get_signs_for_lemma(lemma_id: int) -> List[Dict]:
    """
    Find all signs that can write this lemma.

    Args:
        lemma_id: ID of the lemma

    Returns:
        List of sign dicts with association metadata
    """
    conn = get_connection()

    with conn:
        return conn.execute(
            """
            SELECT
                s.*,
                sla.reading_type,
                sla.value,
                sla.frequency,
                sla.context_distribution
            FROM lexical_signs s
            JOIN lexical_sign_lemma_associations sla ON s.id = sla.sign_id
            WHERE sla.lemma_id = %s
            ORDER BY sla.frequency DESC
            """,
            (lemma_id,),
        ).fetchall()


def get_lemmas_for_sign(sign_id: int) -> List[Dict]:
    """
    Find all lemmas that a sign can represent.

    Args:
        sign_id: ID of the sign

    Returns:
        List of lemma dicts with association metadata
    """
    conn = get_connection()

    with conn:
        return conn.execute(
            """
            SELECT
                l.*,
                sla.reading_type,
                sla.value,
                sla.frequency
            FROM lexical_lemmas l
            JOIN lexical_sign_lemma_associations sla ON l.id = sla.lemma_id
            WHERE sla.sign_id = %s
            ORDER BY sla.frequency DESC
            """,
            (sign_id,),
        ).fetchall()


def get_tablets_for_sign(sign_id: int, limit: int = 100) -> List[Dict]:
    """
    Get tablets where this sign appears.

    Args:
        sign_id: ID of the sign
        limit: Maximum number of tablets to return

    Returns:
        List of dicts with p_number and occurrence_count
    """
    conn = get_connection()

    with conn:
        return conn.execute(
            """
            SELECT p_number, occurrence_count
            FROM lexical_tablet_occurrences
            WHERE sign_id = %s
            ORDER BY occurrence_count DESC
            LIMIT %s
            """,
            (sign_id, limit),
        ).fetchall()


def get_tablets_for_lemma(lemma_id: int, limit: int = 100) -> List[Dict]:
    """
    Get tablets where this lemma appears.

    Args:
        lemma_id: ID of the lemma
        limit: Maximum number of tablets to return

    Returns:
        List of dicts with p_number and occurrence_count
    """
    conn = get_connection()

    with conn:
        return conn.execute(
            """
            SELECT p_number, occurrence_count
            FROM lexical_tablet_occurrences
            WHERE lemma_id = %s
            ORDER BY occurrence_count DESC
            LIMIT %s
            """,
            (lemma_id, limit),
        ).fetchall()


# ============================================================================
# FULL CHAIN RETRIEVALS (for detail pages)
# ============================================================================


def get_sign_full_chain(sign_id: int) -> Optional[Dict]:
    """
    Get complete chain: Sign → all Lemmas → all Senses for each Lemma.

    Args:
        sign_id: ID of the sign

    Returns:
        Dict with sign data, lemmas (with nested senses), and tablets
        Structure:
        {
          "sign": {...sign data + source attribution...},
          "lemmas": [
            {
              "lemma": {...lemma data...},
              "association": {reading_type, value, frequency, context_distribution},
              "senses": [...all senses for this lemma...]
            }
          ],
          "tablets": [...tablets where this sign appears...],
          "total_occurrences": 15234
        }
    """
    conn = get_connection()

    with conn:
        # Get sign
        sign = conn.execute(
            "SELECT * FROM lexical_signs WHERE id = %s", (sign_id,)
        ).fetchone()

        if not sign:
            return None

        # Get lemmas with senses (nested query)
        lemmas_raw = conn.execute(
            """
            SELECT
                l.*,
                sla.reading_type,
                sla.value,
                sla.frequency,
                sla.context_distribution,
                (
                    SELECT json_agg(
                        json_build_object(
                            'id', s.id,
                            'sense_number', s.sense_number,
                            'definition_parts', s.definition_parts,
                            'translations', s.translations,
                            'semantic_domain', s.semantic_domain,
                            'usage_notes', s.usage_notes,
                            'source', s.source,
                            'source_citation', s.source_citation
                        )
                        ORDER BY s.sense_number
                    )
                    FROM lexical_senses s
                    WHERE s.lemma_id = l.id
                ) as senses
            FROM lexical_lemmas l
            JOIN lexical_sign_lemma_associations sla ON l.id = sla.lemma_id
            WHERE sla.sign_id = %s
            ORDER BY sla.frequency DESC
            """,
            (sign_id,),
        ).fetchall()

        # Get tablets (pre-computed)
        tablets = get_tablets_for_sign(sign_id, limit=50)

        # Get total occurrences
        total_occurrences = (
            sum(t["occurrence_count"] for t in tablets) if tablets else 0
        )

    return {
        "sign": sign,
        "lemmas": lemmas_raw,
        "tablets": tablets,
        "total_occurrences": total_occurrences,
    }


def get_lemma_full_chain(lemma_id: int) -> Optional[Dict]:
    """
    Get complete chain: Lemma → all Senses + all Signs.

    Args:
        lemma_id: ID of the lemma

    Returns:
        Dict with lemma data, senses, signs, and tablets
        Structure:
        {
          "lemma": {...lemma data + source attribution...},
          "senses": [...all senses...],
          "signs": [...all signs that can write this...],
          "tablets": [...tablets where this lemma appears...],
          "total_occurrences": 15234
        }
    """
    conn = get_connection()

    with conn:
        # Get lemma
        lemma = conn.execute(
            "SELECT * FROM lexical_lemmas WHERE id = %s", (lemma_id,)
        ).fetchone()

        if not lemma:
            return None

    # Get senses
    senses = get_lemma_senses(lemma_id)

    # Get signs
    signs = get_signs_for_lemma(lemma_id)

    # Get tablets
    tablets = get_tablets_for_lemma(lemma_id, limit=50)

    return {
        "lemma": lemma,
        "senses": senses,
        "signs": signs,
        "tablets": tablets,
        "total_occurrences": lemma["attestation_count"],
    }


def get_sense_full_chain(sense_id: int) -> Optional[Dict]:
    """
    Get complete chain: Sense → Lemma → all Signs.

    Args:
        sense_id: ID of the sense

    Returns:
        Dict with sense, parent lemma, and signs
        Structure:
        {
          "sense": {...sense data...},
          "lemma": {...parent lemma...},
          "signs": [...signs that can write the parent lemma...]
        }
    """
    conn = get_connection()

    with conn:
        # Get sense
        sense = conn.execute(
            "SELECT * FROM lexical_senses WHERE id = %s", (sense_id,)
        ).fetchone()

        if not sense:
            return None

    # Get parent lemma (full chain)
    lemma_chain = get_lemma_full_chain(sense["lemma_id"])

    if not lemma_chain:
        return None

    return {
        "sense": sense,
        "lemma": lemma_chain["lemma"],
        "signs": lemma_chain["signs"],
    }


# ============================================================================
# TOKEN INTEGRATION
# ============================================================================


def get_token_lexical_context(
    token_form: str, language: str = "sux", source: Optional[str] = None
) -> Dict:
    """
    Get complete lexical context for a token.

    Args:
        token_form: The token's form (e.g., "lugal", "šarru")
        language: Language code (sux, akk, etc.)
        source: Optional source filter

    Returns:
        Dict with token form, matching lemmas (with senses and signs), and count
        Structure:
        {
          "token_form": "lugal",
          "language": "sux",
          "lemmas": [
            {
              "id": 123,
              "citation_form": "lugal",
              "guide_word": "king",
              "pos": "N",
              "senses": [...],
              "signs": [...]
            }
          ],
          "count": 1
        }
    """
    # Find matching lemmas
    lemmas = lookup_lemmas_by_form(token_form, language, source)

    # For each lemma, get senses and signs
    for lemma in lemmas:
        lemma["senses"] = get_lemma_senses(lemma["id"])
        lemma["signs"] = get_signs_for_lemma(lemma["id"])

    return {
        "token_form": token_form,
        "language": language,
        "lemmas": lemmas,
        "count": len(lemmas),
    }


# ============================================================================
# SEARCH FUNCTIONS
# ============================================================================


def search_lemmas(
    query: str,
    language: Optional[str] = None,
    pos: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    """
    Search lemmas by citation form or guide word.

    Args:
        query: Search string (matches citation_form or guide_word)
        language: Optional language filter
        pos: Optional POS filter
        source: Optional source filter
        limit: Maximum results to return

    Returns:
        List of matching lemmas with sense_count
    """
    conn = get_connection()

    sql = """
        SELECT
            l.*,
            COUNT(DISTINCT s.id) as sense_count,
            COUNT(DISTINCT sla.sign_id) as sign_count
        FROM lexical_lemmas l
        LEFT JOIN lexical_senses s ON l.id = s.lemma_id
        LEFT JOIN lexical_sign_lemma_associations sla ON l.id = sla.lemma_id
        WHERE (l.citation_form ILIKE %s OR l.guide_word ILIKE %s)
    """

    params = [f"%{query}%", f"%{query}%"]

    if language:
        sql += " AND l.language_code = %s"
        params.append(language)

    if pos:
        sql += " AND l.pos = %s"
        params.append(pos)

    if source:
        sql += " AND l.source = %s"
        params.append(source)

    sql += """
        GROUP BY l.id
        ORDER BY l.attestation_count DESC NULLS LAST
        LIMIT %s
    """
    params.append(limit)

    with conn:
        results = conn.execute(sql, params).fetchall()

    return results


def search_signs(
    query: str,
    language: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    """
    Search signs by name or values.

    Args:
        query: Search string (matches sign_name or values array)
        language: Optional language filter
        limit: Maximum results to return

    Returns:
        List of matching signs
    """
    conn = get_connection()

    sql = """
        SELECT
            s.*,
            COUNT(DISTINCT sla.lemma_id) as lemma_count
        FROM lexical_signs s
        LEFT JOIN lexical_sign_lemma_associations sla ON s.id = sla.sign_id
        WHERE (
            s.sign_name ILIKE %s
            OR %s = ANY(s.values)
        )
    """

    params = [f"%{query}%", query.lower()]

    if language:
        sql += " AND %s = ANY(s.language_codes)"
        params.append(language)

    sql += """
        GROUP BY s.id
        ORDER BY s.sign_name
        LIMIT %s
    """
    params.append(limit)

    with conn:
        results = conn.execute(sql, params).fetchall()

    return results
