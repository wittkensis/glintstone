"""Backfill Voyage embeddings into entity_embeddings.

Run on the deploy server (not locally — DB lives on the VPS).

Targets, in priority order:
  1. translations.text             → entity_type='artifact_translation'  (~44k rows)
  2. artifact lemma_bag synthesized → entity_type='artifact_lemma_bag'   (~353k rows)
  3. artifact designations         → entity_type='artifact_designation'  (~353k rows)
  4. lexical_senses.definition_parts → entity_type='lemma_gloss'         (~155k rows)
  5. named_entities.canonical_name → entity_type='named_entity'          (~1.8k rows)
  6. scholars blob                 → entity_type='scholar_blob'          (~20k rows)

Resumable via source_hash: skips rows whose source text is unchanged.

Cost estimate at voyage-3-large ($0.18 / 1M tokens), ~one-time:
  translations           2.2M tokens  → ~$0.40
  lemma_bag             10.6M tokens  → ~$1.91
  designations           3.5M tokens  → ~$0.63
  glosses                1.5M tokens  → ~$0.27
  entities               18k tokens   → ~$0.00
  scholars               2M tokens    → ~$0.36
  -------------------------------------------
  TOTAL                              ≈ ~$3.60

Usage:
  python -m scripts.backfill_embeddings --target translations
  python -m scripts.backfill_embeddings --target all --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable

import psycopg

from core.agent.voyage_client import VoyageClient, _hash
from core.database import get_connection

logger = logging.getLogger("backfill")

_BATCH_SIZE = 64
_MODEL = "voyage-3-large"
_DIM = 1024


def _load_existing_hashes(conn: psycopg.Connection, entity_type: str) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT entity_id, source_hash FROM entity_embeddings "
            "WHERE entity_type = %s AND model = %s",
            (entity_type, _MODEL),
        )
        return {r["entity_id"]: r["source_hash"] for r in cur.fetchall()}


def _upsert_embeddings(
    conn: psycopg.Connection,
    entity_type: str,
    rows: list[tuple[str, str, str, list[float]]],
    dry_run: bool = False,
) -> None:
    """rows: (entity_id, source_text, source_hash, vec)"""
    if not rows or dry_run:
        return
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO entity_embeddings
                (entity_type, entity_id, model, dim, vec, source_text, source_hash)
            VALUES (%s, %s, %s, %s, %s::vector, %s, %s)
            ON CONFLICT (entity_type, entity_id, model)
            DO UPDATE SET
                vec = EXCLUDED.vec,
                source_text = EXCLUDED.source_text,
                source_hash = EXCLUDED.source_hash,
                generated_at = now()
            """,
            [
                (entity_type, eid, _MODEL, _DIM, str(vec), text, h)
                for eid, text, h, vec in rows
            ],
        )
    conn.commit()


def _run_chunked(
    conn: psycopg.Connection,
    voyage: VoyageClient,
    entity_type: str,
    iter_rows: Iterable[tuple[str, str]],
    dry_run: bool = False,
) -> tuple[int, int]:
    """Iterate (entity_id, source_text) pairs; embed in batches; upsert.

    Returns (embedded_count, skipped_count).
    """
    existing = _load_existing_hashes(conn, entity_type)
    pending: list[tuple[str, str]] = []
    embedded = 0
    skipped = 0

    def flush():
        nonlocal embedded
        if not pending:
            return
        ids = [p[0] for p in pending]
        texts = [p[1] for p in pending]
        if dry_run:
            embedded += len(pending)
        else:
            results = voyage.embed(texts, input_type="document")
            rows = [
                (eid, r.text, r.source_hash, r.vector) for eid, r in zip(ids, results)
            ]
            _upsert_embeddings(conn, entity_type, rows, dry_run=False)
            embedded += len(rows)
        pending.clear()

    for entity_id, text in iter_rows:
        if not text or not text.strip():
            continue
        text_hash = _hash(text)
        if existing.get(entity_id) == text_hash:
            skipped += 1
            continue
        pending.append((entity_id, text))
        if len(pending) >= _BATCH_SIZE:
            flush()
            logger.info("%s: embedded=%d skipped=%d", entity_type, embedded, skipped)
    flush()
    return embedded, skipped


# ── Per-target source iterators ──────────────────────────────────────────────


def _iter_translations(conn: psycopg.Connection) -> Iterable[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.p_number, string_agg(t.text, ' ' ORDER BY tl.line_number) AS blob
            FROM translations t
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN surfaces s ON tl.surface_id = s.id
            GROUP BY s.p_number
            """
        )
        for row in cur:
            yield row["p_number"], row["blob"]


def _iter_lemma_bag(conn: psycopg.Connection) -> Iterable[tuple[str, str]]:
    """For each artifact, concatenate guide_word and citation_form of its lemmas."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.p_number,
                   string_agg(DISTINCT COALESCE(ll.guide_word, ll.citation_form),
                              ', ' ORDER BY COALESCE(ll.guide_word, ll.citation_form)) AS bag
            FROM tokens t
            JOIN lemmatizations lz ON lz.token_id = t.id
            JOIN lexical_lemmas ll ON ll.id = lz.lemma_id
            JOIN text_lines tl ON t.line_id = tl.id
            JOIN surfaces s ON tl.surface_id = s.id
            GROUP BY s.p_number
            """
        )
        for row in cur:
            yield row["p_number"], row["bag"]


def _iter_designations(conn: psycopg.Connection) -> Iterable[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p_number,
                   COALESCE(designation, '')
                   || COALESCE(' ' || period_normalized, '')
                   || COALESCE(' ' || provenience_normalized, '') AS blob
            FROM artifacts
            WHERE designation IS NOT NULL OR period_normalized IS NOT NULL
            """
        )
        for row in cur:
            yield row["p_number"], row["blob"]


def _iter_glosses(conn: psycopg.Connection) -> Iterable[tuple[str, str]]:
    """lexical_senses stores glosses as definition_parts (text[]).
    Join with ' ; ' for embedding input."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   array_to_string(definition_parts, ' ; ') AS blob
            FROM lexical_senses
            WHERE definition_parts IS NOT NULL
              AND array_length(definition_parts, 1) > 0
            """
        )
        for row in cur:
            yield str(row["id"]), row["blob"]


def _iter_named_entities(conn: psycopg.Connection) -> Iterable[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, canonical_name || COALESCE(' (' || entity_type || ')', '') AS blob
            FROM named_entities
            WHERE canonical_name IS NOT NULL
            """
        )
        for row in cur:
            yield str(row["id"]), row["blob"]


def _iter_scholars(conn: psycopg.Connection) -> Iterable[tuple[str, str]]:
    """scholars has only `name` — no affiliation column. Embed name + their
    publications as the semantic signal."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id,
                   s.name
                   || COALESCE(' ' || string_agg(p.title, ' '), '') AS blob
            FROM scholars s
            LEFT JOIN publication_authors pa ON pa.scholar_id = s.id
            LEFT JOIN publications p ON p.id = pa.publication_id
            GROUP BY s.id, s.name
            """
        )
        for row in cur:
            yield str(row["id"]), row["blob"]


_TARGETS = {
    "translations": ("artifact_translation", _iter_translations),
    "lemma_bag": ("artifact_lemma_bag", _iter_lemma_bag),
    "designations": ("artifact_designation", _iter_designations),
    "glosses": ("lemma_gloss", _iter_glosses),
    "named_entities": ("named_entity", _iter_named_entities),
    "scholars": ("scholar_blob", _iter_scholars),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill Voyage embeddings")
    parser.add_argument(
        "--target",
        choices=list(_TARGETS) + ["all"],
        required=True,
        help="Which entity type to backfill, or 'all'",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Skip Voyage and DB writes"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    targets = list(_TARGETS) if args.target == "all" else [args.target]
    voyage = VoyageClient() if not args.dry_run else None

    # core.database.get_connection() expects the pool to be initialized; the
    # api/web services do this at startup. As a standalone CLI we init it here.
    from core.database import close_pool, init_pool

    init_pool(min_size=0, max_size=2, timeout=30.0)
    try:
        with get_connection() as conn:
            for t in targets:
                entity_type, iter_fn = _TARGETS[t]
                logger.info("==> backfilling %s (entity_type=%s)", t, entity_type)
                embedded, skipped = _run_chunked(
                    conn=conn,
                    voyage=voyage,  # type: ignore[arg-type]
                    entity_type=entity_type,
                    iter_rows=iter_fn(conn),
                    dry_run=args.dry_run,
                )
                logger.info("    done: embedded=%d skipped=%d", embedded, skipped)
    finally:
        close_pool()

    return 0


if __name__ == "__main__":
    sys.exit(main())
