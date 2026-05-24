"""Hybrid lexical + semantic search engine.

Pipeline:
  1. Exact match (P-number, full designation, full name) — short-circuit
  2. Lexical: pg_trgm similarity + tsvector rank against search_entities
  3. Semantic: Voyage query embedding → pgvector cosine over entity_embeddings
     (label hydration merged into a single JOIN query)
  4. Fusion: Reciprocal Rank Fusion (k=60) across the three signals
  5. Group by entity_type, paginate via opaque cursor

In hybrid mode, steps 2 and 3 run in parallel via ThreadPoolExecutor — each
acquires its own pool connection so that the ~200-1000 ms Voyage network call
overlaps with the lexical DB query instead of sitting after it.

Cursor format: base64-encoded JSON of {q_hash, score_floor, last_id, types}.
Query embeddings cached in-process by q_hash for 5 minutes (cursor TTL).
"""

from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field

import psycopg

from core.agent.voyage_client import VoyageClient
from core.database import get_connection
from core.schemas.search import EntityType, SearchFilters, SearchParams

logger = logging.getLogger(__name__)

_P_NUMBER_RE = re.compile(r"^P\d{6,7}$", re.I)
_Q_NUMBER_RE = re.compile(r"^Q\d{6,7}$", re.I)
_RRF_K = 60
_CURSOR_TTL_SECONDS = 300


@dataclass
class SearchHit:
    entity_type: str
    entity_id: str
    primary_label: str
    secondary_label: str | None
    sources: list[str]
    score: float
    p_number_ref: str | None = None
    int_ref: int | None = None
    rank_components: dict[str, float] = field(default_factory=dict)
    # Display extras hydrated after fusion for tablet hits only (drawer rows
    # show a thumbnail + a 5-dot pipeline mini-badge per artifact).
    thumbnail_url: str | None = None
    pipeline_completeness: int | None = None
    pipeline_stages: list[int] | None = (
        None  # 5-element 0/1 list: atf, tokens, lemma, translation, entities
    )


@dataclass
class SearchResults:
    groups: dict[str, list[SearchHit]]
    totals: dict[str, int]
    cursor_data: dict | None = None


# ── In-process query embedding cache ─────────────────────────────────────────


_QUERY_VEC_CACHE: dict[str, tuple[float, list[float]]] = {}


def _cached_query_vector(voyage: VoyageClient, q: str) -> list[float]:
    h = hashlib.sha256(q.encode()).hexdigest()
    now = time.time()
    cached = _QUERY_VEC_CACHE.get(h)
    if cached and (now - cached[0]) < _CURSOR_TTL_SECONDS:
        logger.debug("voyage cache hit q_hash=%s", h[:8])
        return cached[1]
    t0 = time.monotonic()
    result = voyage.embed_query(q)
    logger.info(
        "voyage embed duration_ms=%d q_hash=%s",
        int((time.monotonic() - t0) * 1000),
        h[:8],
    )
    _QUERY_VEC_CACHE[h] = (now, result.vector)
    return result.vector


# ── Search engine ────────────────────────────────────────────────────────────


class SearchEngine:
    def __init__(self, voyage: VoyageClient | None = None) -> None:
        self._voyage = voyage

    def search(
        self,
        conn: psycopg.Connection,
        params: SearchParams,
    ) -> SearchResults:
        t_start = time.monotonic()

        types = params.types or [
            "tablets",
            "lemmas",
            "signs",
            "scholars",
            "publications",
            "entities",
        ]

        # 1. Exact match (P-number / Q-number / scholar name) — short-circuit
        exact_hit = self._exact_match(conn, params.q)
        exact_hits = [exact_hit] if exact_hit else []

        # 2 + 3. Lexical and semantic — run in parallel for hybrid mode so that
        # the Voyage HTTP call (~200-1000 ms) overlaps with the lexical DB query.
        # Each parallel worker acquires its own connection from the pool.
        lexical_hits: list[SearchHit] = []
        semantic_hits: list[SearchHit] = []

        do_semantic = params.mode in ("semantic", "hybrid") and bool(self._voyage)

        t_retrieval_start = time.monotonic()
        if params.mode == "lexical":
            lexical_hits = self._lexical_search(conn, params.q, types, params.limit * 3)
        elif params.mode == "semantic":
            if do_semantic:
                try:
                    semantic_hits = self._semantic_search_parallel(
                        params.q, types, params.limit * 3
                    )
                except Exception as exc:
                    logger.warning("semantic search degraded: %s", exc)
                    lexical_hits = self._lexical_search(
                        conn, params.q, types, params.limit * 3
                    )
            else:
                lexical_hits = self._lexical_search(
                    conn, params.q, types, params.limit * 3
                )
        else:  # hybrid
            if do_semantic:
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    lex_future = executor.submit(
                        self._lexical_search_parallel, params.q, types, params.limit * 3
                    )
                    sem_future = executor.submit(
                        self._semantic_search_parallel,
                        params.q,
                        types,
                        params.limit * 3,
                    )
                    try:
                        lexical_hits = lex_future.result(timeout=8.0)
                    except Exception as exc:
                        logger.warning("lexical search failed: %s", exc)
                    try:
                        semantic_hits = sem_future.result(timeout=15.0)
                    except Exception as exc:
                        logger.warning("semantic search degraded: %s", exc)
            else:
                lexical_hits = self._lexical_search(
                    conn, params.q, types, params.limit * 3
                )
        t_retrieval_ms = int((time.monotonic() - t_retrieval_start) * 1000)

        # 4. Fusion (lexical-only if semantic fell through)
        if params.mode == "lexical":
            fused = lexical_hits
        elif params.mode == "semantic":
            fused = semantic_hits or lexical_hits
        else:
            fused = self._rrf([lexical_hits, semantic_hits])

        # Prepend exact hits (de-duped)
        seen = set()
        ordered: list[SearchHit] = []
        for hit in exact_hits + fused:
            key = (hit.entity_type, hit.entity_id)
            if key in seen:
                continue
            seen.add(key)
            ordered.append(hit)

        # 5. Group + cap per type
        groups: dict[str, list[SearchHit]] = {t: [] for t in types}
        totals: dict[str, int] = {t: 0 for t in types}

        for hit in ordered:
            if hit.entity_type not in groups:
                continue
            totals[hit.entity_type] += 1
            if len(groups[hit.entity_type]) < params.limit:
                groups[hit.entity_type].append(hit)

        # Total counts come from a separate count query for accuracy
        t_count_start = time.monotonic()
        accurate_totals = self._count_per_type(conn, params.q, types, params.filters)
        t_count_ms = int((time.monotonic() - t_count_start) * 1000)
        for t in types:
            totals[t] = max(totals[t], accurate_totals.get(t, 0))

        # Hydrate tablet hits with thumbnail + pipeline-completeness for the
        # global-search drawer rows (cheap single-pass joins keyed by p_number).
        t_hydrate_start = time.monotonic()
        self._hydrate_tablet_extras(conn, groups.get("tablets", []))
        t_hydrate_ms = int((time.monotonic() - t_hydrate_start) * 1000)

        t_total_ms = int((time.monotonic() - t_start) * 1000)
        logger.info(
            "search mode=%s total_ms=%d retrieval_ms=%d count_ms=%d hydrate_ms=%d "
            "lexical_hits=%d semantic_hits=%d q=%r",
            params.mode,
            t_total_ms,
            t_retrieval_ms,
            t_count_ms,
            t_hydrate_ms,
            len(lexical_hits),
            len(semantic_hits),
            params.q[:60],
        )

        return SearchResults(groups=groups, totals=totals, cursor_data=None)

    def _hydrate_tablet_extras(
        self,
        conn: psycopg.Connection,
        hits: list[SearchHit],
    ) -> None:
        """Attach r2_thumbnail_key and pipeline stage flags to tablet hits.

        Joins artifact_images (display_order=0) and pipeline_completeness on
        p_number in a single query. Updates `hits` in place. Stays silent on
        failure so the search still returns results if a join misses.
        """
        if not hits:
            return
        p_numbers = [h.entity_id for h in hits if h.entity_id]
        if not p_numbers:
            return
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        a.p_number,
                        img.r2_thumbnail_key,
                        pc.has_atf,
                        pc.has_tokens,
                        pc.has_lemmatization,
                        pc.has_translation,
                        pc.has_entities,
                        pc.completeness_score
                    FROM artifacts a
                    LEFT JOIN LATERAL (
                        SELECT r2_thumbnail_key
                        FROM artifact_images
                        WHERE p_number = a.p_number
                          AND r2_thumbnail_key IS NOT NULL
                        ORDER BY display_order ASC, id ASC
                        LIMIT 1
                    ) img ON TRUE
                    LEFT JOIN pipeline_completeness pc ON pc.p_number = a.p_number
                    WHERE a.p_number = ANY(%s)
                    """,
                    (p_numbers,),
                )
                by_p: dict[str, dict] = {r["p_number"]: r for r in cur.fetchall()}
        except Exception as exc:
            logger.warning("tablet extras hydrate failed: %s", exc)
            return

        # Late import keeps core.agent free of an api dependency cycle.
        from core.storage import public_url_for_key

        for hit in hits:
            row = by_p.get(hit.entity_id)
            if not row:
                continue
            key = row.get("r2_thumbnail_key")
            hit.thumbnail_url = public_url_for_key(key) if key else None
            hit.pipeline_stages = [
                int(row.get("has_atf") or 0),
                int(row.get("has_tokens") or 0),
                int(row.get("has_lemmatization") or 0),
                int(row.get("has_translation") or 0),
                int(row.get("has_entities") or 0),
            ]
            score = row.get("completeness_score")
            hit.pipeline_completeness = int(score) if score is not None else None

    # ── Parallel wrappers (each acquires its own pool connection) ────────────

    def _lexical_search_parallel(
        self, q: str, types: list[EntityType], limit: int
    ) -> list[SearchHit]:
        with get_connection() as conn:
            return self._lexical_search(conn, q, types, limit)

    def _semantic_search_parallel(
        self, q: str, types: list[EntityType], limit: int
    ) -> list[SearchHit]:
        with get_connection() as conn:
            return self._semantic_search(conn, q, types, limit)

    # ── Implementation ───────────────────────────────────────────────────────

    def _exact_match(self, conn: psycopg.Connection, q: str) -> SearchHit | None:
        q_stripped = q.strip()
        if not q_stripped:
            return None

        if _P_NUMBER_RE.match(q_stripped):
            p_number = q_stripped.upper()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT designation, period_normalized, provenience_normalized "
                    "FROM artifacts WHERE p_number = %s",
                    (p_number,),
                )
                row = cur.fetchone()
            if row:
                return SearchHit(
                    entity_type="tablets",
                    entity_id=p_number,
                    primary_label=row.get("designation") or p_number,
                    secondary_label=" • ".join(
                        x
                        for x in [
                            row.get("period_normalized"),
                            row.get("provenience_normalized"),
                        ]
                        if x
                    )
                    or None,
                    sources=["cdli_catalog"],
                    score=1.0,
                    p_number_ref=p_number,
                    rank_components={"exact": 1.0},
                )
        return None

    def _lexical_search(
        self,
        conn: psycopg.Connection,
        q: str,
        types: list[EntityType],
        limit: int,
    ) -> list[SearchHit]:
        if not q.strip():
            return []
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    entity_type, entity_id, primary_label, secondary_label,
                    sources, p_number_ref, int_ref,
                    GREATEST(
                        similarity(search_blob, %s),
                        ts_rank_cd(tsv, plainto_tsquery('simple', %s))
                    ) AS score
                FROM search_entities
                WHERE entity_type = ANY(%s)
                  AND (search_blob %% %s OR tsv @@ plainto_tsquery('simple', %s))
                ORDER BY score DESC
                LIMIT %s
                """,
                (q, q, list(types), q, q, limit),
            )
            rows = cur.fetchall()

        return [
            SearchHit(
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                primary_label=r.get("primary_label") or r["entity_id"],
                secondary_label=r.get("secondary_label"),
                sources=list(r.get("sources") or []),
                score=float(r.get("score") or 0),
                p_number_ref=r.get("p_number_ref"),
                int_ref=r.get("int_ref"),
                rank_components={"lexical": float(r.get("score") or 0)},
            )
            for r in rows
        ]

    def _semantic_search(
        self,
        conn: psycopg.Connection,
        q: str,
        types: list[EntityType],
        limit: int,
    ) -> list[SearchHit]:
        if not q.strip() or self._voyage is None:
            return []
        vector = _cached_query_vector(self._voyage, q)

        # Map public entity_types to embedding entity_type values stored in DB
        embedding_type_map = {
            "tablets": [
                "artifact_translation",
                "artifact_lemma_bag",
                "artifact_designation",
            ],
            "lemmas": ["lemma_gloss"],
            "scholars": ["scholar_blob"],
            "entities": ["named_entity"],
            "composites": ["composite_designation"],
        }
        embedding_types: list[str] = []
        for t in types:
            embedding_types.extend(embedding_type_map.get(t, []))
        if not embedding_types:
            return []

        # Single query: vector scan + dedup to best-per-entity + label hydration.
        #
        # Artifacts have up to 3 embedding flavors (translation / lemma_bag /
        # designation) sharing the same entity_id. DISTINCT ON keeps only the
        # closest embedding per entity_id before the JOIN. The HNSW index on
        # entity_embeddings.vec handles the ORDER BY efficiently.
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH best AS (
                    SELECT DISTINCT ON (
                        CASE entity_type
                            WHEN 'artifact_translation' THEN 'tablets'
                            WHEN 'artifact_lemma_bag'   THEN 'tablets'
                            WHEN 'artifact_designation' THEN 'tablets'
                            WHEN 'lemma_gloss'           THEN 'lemmas'
                            WHEN 'scholar_blob'          THEN 'scholars'
                            WHEN 'named_entity'          THEN 'entities'
                            WHEN 'composite_designation' THEN 'composites'
                            ELSE entity_type
                        END,
                        entity_id
                    )
                        CASE entity_type
                            WHEN 'artifact_translation' THEN 'tablets'
                            WHEN 'artifact_lemma_bag'   THEN 'tablets'
                            WHEN 'artifact_designation' THEN 'tablets'
                            WHEN 'lemma_gloss'           THEN 'lemmas'
                            WHEN 'scholar_blob'          THEN 'scholars'
                            WHEN 'named_entity'          THEN 'entities'
                            WHEN 'composite_designation' THEN 'composites'
                            ELSE entity_type
                        END  AS pub_type,
                        entity_id,
                        (1 - (vec <=> %s::vector)) AS cosine
                    FROM entity_embeddings
                    WHERE entity_type = ANY(%s)
                      AND model = 'voyage-3-large'
                    ORDER BY
                        CASE entity_type
                            WHEN 'artifact_translation' THEN 'tablets'
                            WHEN 'artifact_lemma_bag'   THEN 'tablets'
                            WHEN 'artifact_designation' THEN 'tablets'
                            WHEN 'lemma_gloss'           THEN 'lemmas'
                            WHEN 'scholar_blob'          THEN 'scholars'
                            WHEN 'named_entity'          THEN 'entities'
                            WHEN 'composite_designation' THEN 'composites'
                            ELSE entity_type
                        END,
                        entity_id,
                        vec <=> %s::vector ASC
                    LIMIT %s
                )
                SELECT
                    se.entity_type,
                    se.entity_id,
                    se.primary_label,
                    se.secondary_label,
                    se.sources,
                    se.p_number_ref,
                    se.int_ref,
                    b.cosine
                FROM best b
                JOIN search_entities se
                    ON se.entity_type = b.pub_type
                   AND se.entity_id   = b.entity_id
                ORDER BY b.cosine DESC
                """,
                (vector, embedding_types, vector, limit),
            )
            rows = cur.fetchall()

        hits = [
            SearchHit(
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                primary_label=r.get("primary_label") or r["entity_id"],
                secondary_label=r.get("secondary_label"),
                sources=list(r.get("sources") or []),
                score=float(r.get("cosine") or 0),
                p_number_ref=r.get("p_number_ref"),
                int_ref=r.get("int_ref"),
                rank_components={"semantic": float(r.get("cosine") or 0)},
            )
            for r in rows
        ]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits

    def _rrf(self, ranked_lists: list[list[SearchHit]]) -> list[SearchHit]:
        """Reciprocal Rank Fusion across multiple ranked lists.

        score(d) = sum over lists L of 1 / (k + rank_L(d))
        """
        scores: dict[tuple[str, str], float] = {}
        first_hit: dict[tuple[str, str], SearchHit] = {}
        for ranked in ranked_lists:
            for rank, hit in enumerate(ranked):
                key = (hit.entity_type, hit.entity_id)
                scores[key] = scores.get(key, 0.0) + 1.0 / (_RRF_K + rank + 1)
                if key not in first_hit:
                    first_hit[key] = hit

        fused: list[SearchHit] = []
        for key, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
            hit = first_hit[key]
            fused.append(
                SearchHit(
                    entity_type=hit.entity_type,
                    entity_id=hit.entity_id,
                    primary_label=hit.primary_label,
                    secondary_label=hit.secondary_label,
                    sources=hit.sources,
                    score=score,
                    p_number_ref=hit.p_number_ref,
                    int_ref=hit.int_ref,
                    rank_components={**hit.rank_components, "rrf": score},
                )
            )
        return fused

    def _count_per_type(
        self,
        conn: psycopg.Connection,
        q: str,
        types: list[EntityType],
        filters: SearchFilters | None,
    ) -> dict[str, int]:
        if not q.strip():
            return {t: 0 for t in types}
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT entity_type, COUNT(*) AS n
                FROM search_entities
                WHERE entity_type = ANY(%s)
                  AND (search_blob %% %s OR tsv @@ plainto_tsquery('simple', %s))
                GROUP BY entity_type
                """,
                (list(types), q, q),
            )
            return {r["entity_type"]: int(r["n"]) for r in cur.fetchall()}


# ── Cursor encoding ───────────────────────────────────────────────────────────


def encode_cursor(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict | None:
    try:
        decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        # Cursor TTL: reject if older than 5 minutes
        if (time.time() - decoded.get("issued_at", 0)) > _CURSOR_TTL_SECONDS:
            return None
        return decoded
    except Exception:
        return None
