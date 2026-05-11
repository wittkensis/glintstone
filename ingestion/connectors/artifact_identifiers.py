"""Artifact identifiers seeder.

Derives one artifact_identifiers row per identifier type per artifact:
  cdli_designation, museum_no, excavation_no, publication

Depends on: annotation-runs + cdli-catalog (artifacts must be loaded first)
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

BATCH_SIZE = 5000

MUSEUM_AUTHORITIES = [
    (r"^BM\b", "british_museum"),
    (r"^YBC\b", "yale_babylonian_collection"),
    (r"^CBS\b", "university_museum_philadelphia"),
    (r"^UM\b", "university_museum_philadelphia"),
    (r"^IM\b", "iraq_museum"),
    (r"^NBC\b", "nies_babylonian_collection_yale"),
    (r"^VAT\b", "vorderasiatisches_museum_berlin"),
    (r"^AO\b", "louvre"),
    (r"^Ni\b", "istanbul_archaeology_museum"),
    (r"^NCBT\b", "newell_collection"),
    (r"^MLC\b", "morgan_library"),
    (r"^Ashm\b", "ashmolean_museum"),
    (r"^AS\b", "ashmolean_museum"),
    (r"^FLP\b", "free_library_philadelphia"),
]


def _infer_authority(museum_no: str | None) -> str | None:
    if not museum_no:
        return None
    for pattern, authority in MUSEUM_AUTHORITIES:
        if re.match(pattern, museum_no, re.IGNORECASE):
            return authority
    return None


def _normalize_identifier(val: str) -> str:
    v = unicodedata.normalize("NFKD", val.strip())
    v = "".join(c for c in v if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", v).lower().strip()


class ArtifactIdentifiersConnector(SourceConnector):
    id = "artifact-identifiers"
    display_name = "Artifact Identifiers"
    description = "Derives museum_no, excavation_no, designation, and publication identifiers from the artifacts table."
    kind = "derived"
    runs_after = ["annotation-runs", "cdli-catalog"]

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        ann_row = ctx.db.execute(
            "SELECT id FROM annotation_runs WHERE source_name = 'cdli-catalog'"
        ).fetchone()
        if not ann_row:
            ctx.warn("artifact_identifiers.no_annotation_run")
            return
        annotation_run_id = ann_row["id"] if isinstance(ann_row, dict) else ann_row[0]

        offset = 0
        while True:
            rows = ctx.db.execute(
                "SELECT p_number, designation, museum_no, excavation_no, primary_publication "
                "FROM artifacts ORDER BY p_number LIMIT %s OFFSET %s",
                (BATCH_SIZE, offset),
            ).fetchall()
            if not rows:
                break
            for row in rows:
                if isinstance(row, dict):
                    p_number, designation, museum_no, excavation_no, primary_pub = (
                        row["p_number"],
                        row["designation"],
                        row["museum_no"],
                        row["excavation_no"],
                        row["primary_publication"],
                    )
                else:
                    p_number, designation, museum_no, excavation_no, primary_pub = row

                if designation:
                    yield {
                        "p_number": p_number,
                        "identifier_type": "cdli_designation",
                        "identifier_value": designation,
                        "identifier_normalized": _normalize_identifier(designation),
                        "authority": None,
                        "annotation_run_id": annotation_run_id,
                        "confidence": 1.0,
                    }
                if museum_no:
                    yield {
                        "p_number": p_number,
                        "identifier_type": "museum_no",
                        "identifier_value": museum_no,
                        "identifier_normalized": _normalize_identifier(museum_no),
                        "authority": _infer_authority(museum_no),
                        "annotation_run_id": annotation_run_id,
                        "confidence": 1.0,
                    }
                if excavation_no:
                    yield {
                        "p_number": p_number,
                        "identifier_type": "excavation_no",
                        "identifier_value": excavation_no,
                        "identifier_normalized": _normalize_identifier(excavation_no),
                        "authority": None,
                        "annotation_run_id": annotation_run_id,
                        "confidence": 1.0,
                    }
                if primary_pub:
                    yield {
                        "p_number": p_number,
                        "identifier_type": "publication",
                        "identifier_value": primary_pub,
                        "identifier_normalized": _normalize_identifier(primary_pub),
                        "authority": None,
                        "annotation_run_id": annotation_run_id,
                        "confidence": 0.9,
                    }
            offset += BATCH_SIZE
            if offset % 50000 == 0:
                ctx.info("artifact_identifiers.progress", offset=offset)

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="artifact_identifiers",
            rows=rows,
            unique_key=["p_number", "identifier_type", "identifier_value"],
            policy=ConflictPolicy.SKIP,
            batch_size=500,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM artifact_identifiers"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("artifact_identifiers.verify", count=n)
