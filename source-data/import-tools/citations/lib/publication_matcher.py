#!/usr/bin/env python3
"""
Cross-source publication deduplication.

Cascading match strategy:
1. DOI exact (confidence 1.0)
2. bibtex_key exact within authority (0.95)
3. title + year fuzzy (0.8)
4. short_title + volume exact (0.9)
5. Below 0.7 -> flag for manual review
"""

import re
import psycopg
import unicodedata
from dataclasses import dataclass
from typing import Optional


@dataclass
class MatchResult:
    publication_id: Optional[int]
    method: str  # "doi", "bibtex_key", "title_year", "short_title_vol", "none"
    confidence: float
    matched_bibtex_key: Optional[str] = None


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy comparison."""
    if not title:
        return ""
    # Lowercase
    t = title.lower()
    # Strip diacritics
    t = "".join(
        c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)
    )
    # Remove articles
    t = re.sub(r"\b(the|a|an|der|die|das|le|la|les|un|une)\b", "", t)
    # Remove punctuation
    t = re.sub(r"[^\w\s]", "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Levenshtein similarity ratio (0.0 to 1.0)."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    # Quick length check -- if lengths differ by > 40%, unlikely match
    if abs(len1 - len2) / max(len1, len2) > 0.4:
        return 0.0

    # Standard DP Levenshtein
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )

    distance = matrix[len1][len2]
    return 1.0 - (distance / max(len1, len2))


def find_match(
    candidate: dict,
    conn: psycopg.Connection,
) -> MatchResult:
    """
    Find a matching publication in the database.

    Args:
        candidate: dict with keys: doi, bibtex_key, title, year, short_title, volume
        conn: PostgreSQL connection to v2 database

    Returns:
        MatchResult with matched publication_id or None
    """
    cursor = conn.cursor()

    # 1. DOI exact match
    doi = candidate.get("doi")
    if doi:
        cursor.execute(
            "SELECT id, bibtex_key FROM publications WHERE doi = %s",
            (doi,),
        )
        row = cursor.fetchone()
        if row:
            return MatchResult(row[0], "doi", 1.0, row[1])

    # 2. bibtex_key exact match
    bk = candidate.get("bibtex_key")
    if bk:
        cursor.execute(
            "SELECT id, bibtex_key FROM publications WHERE bibtex_key = %s",
            (bk,),
        )
        row = cursor.fetchone()
        if row:
            return MatchResult(row[0], "bibtex_key", 0.95, row[1])

    # 3. title + year fuzzy match
    title = candidate.get("title")
    year = candidate.get("year")
    if title and year:
        norm_title = normalize_title(title)
        # Fetch candidates with matching year
        cursor.execute(
            "SELECT id, bibtex_key, title FROM publications WHERE year = %s",
            (str(year),),
        )
        best_ratio = 0.0
        best_row = None
        for row in cursor.fetchall():
            db_norm = normalize_title(row[2] or "")
            ratio = levenshtein_ratio(norm_title, db_norm)
            if ratio > best_ratio:
                best_ratio = ratio
                best_row = row

        if best_ratio >= 0.85 and best_row:
            return MatchResult(best_row[0], "title_year", 0.8, best_row[1])

    # 4. short_title + volume exact match
    short_title = candidate.get("short_title")
    volume = candidate.get("volume")
    if short_title and volume:
        cursor.execute(
            "SELECT id, bibtex_key FROM publications "
            "WHERE short_title = %s AND volume_in_series = %s",
            (short_title, str(volume)),
        )
        row = cursor.fetchone()
        if row:
            return MatchResult(row[0], "short_title_vol", 0.9, row[1])

    return MatchResult(None, "none", 0.0)


def record_dedup_candidate(
    conn: psycopg.Connection,
    pub_a_id: int,
    pub_b_id: int,
    match_method: str,
    confidence: float,
):
    """Record a potential duplicate for manual review."""
    conn.execute(
        """INSERT INTO _dedup_candidates
           (pub_a_id, pub_b_id, match_method, confidence)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT DO NOTHING""",
        (pub_a_id, pub_b_id, match_method, confidence),
    )


def ensure_dedup_table(conn: psycopg.Connection):
    """Create staging table for dedup candidates if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _dedup_candidates (
            id SERIAL PRIMARY KEY,
            pub_a_id INTEGER NOT NULL,
            pub_b_id INTEGER NOT NULL,
            match_method TEXT NOT NULL,
            confidence REAL NOT NULL,
            resolved INTEGER DEFAULT 0,
            resolution TEXT,
            UNIQUE(pub_a_id, pub_b_id)
        )
    """)
    conn.commit()
