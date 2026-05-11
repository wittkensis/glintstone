"""Annotation run seeder — registers canonical source records for downstream FKs.

Every import row carries an annotation_run_id FK. This connector creates the
13 canonical records so downstream connectors can reference them by source_name.
Must run before any connector that writes annotation_run_id values.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

# (source_name, source_type, method, corpus_scope, notes)
ANNOTATION_RUNS = [
    (
        "cdli-catalog",
        "import",
        "import",
        "353,283 artifacts",
        "CDLI bulk data dump (Aug 2022). cdli_cat.csv. CC0.",
    ),
    (
        "cdli-atf",
        "import",
        "import",
        "CDLI ATF transliterations",
        "CDLI bulk ATF dump (Aug 2022). cdliatf_unblocked.atf. CC0.",
    ),
    (
        "compvis",
        "import",
        "ML_model",
        "81 tablets, ~8,100 sign annotations",
        "Heidelberg CompVis sign detection annotations. CC BY 4.0.",
    ),
    (
        "oracc/dcclt",
        "import",
        "import",
        "Digital Corpus of Cuneiform Lexical Texts",
        "ORACC DCCLT project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/epsd2",
        "import",
        "import",
        "Electronic PSD 2",
        "ORACC ePSD2 Sumerian dictionary corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap",
        "import",
        "import",
        "Royal Inscriptions of the Neo-Assyrian Period",
        "ORACC RINAP project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao",
        "import",
        "import",
        "State Archives of Assyria Online",
        "ORACC SAAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/blms",
        "import",
        "import",
        "Babylonian Lunar Six Micro Signs",
        "ORACC BLMS project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams",
        "import",
        "import",
        "Corpus of Ancient Mesopotamian Scholarship",
        "ORACC CAMS project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/etcsri",
        "import",
        "import",
        "Electronic Text Corpus of Sumerian Royal Inscriptions",
        "ORACC ETCSRI project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/riao",
        "import",
        "import",
        "Royal Inscriptions of Assyria Online",
        "ORACC RIAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rimanum",
        "import",
        "import",
        "Rulers of the Ancient Near East",
        "ORACC RImanum project corpus. CC BY-SA 3.0.",
    ),
    (
        "ebl-annotations",
        "import",
        "import",
        "eBL sign annotation training data",
        "Electronic Babylonian Library annotation corpus. CC BY 4.0.",
    ),
]


class AnnotationRunsConnector(SourceConnector):
    id = "annotation-runs"
    display_name = "Annotation Runs (Source Registry)"
    description = "Seeds canonical annotation_run records so downstream connectors can reference them by source_name."
    kind = "lookup"
    runs_after = ["lookup-tables"]

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        for source_name, source_type, method, corpus_scope, notes in ANNOTATION_RUNS:
            yield {
                "source_name": source_name,
                "source_type": source_type,
                "method": method,
                "corpus_scope": corpus_scope,
                "notes": notes,
            }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="annotation_runs",
            rows=rows,
            unique_key=["source_name"],
            policy=ConflictPolicy.SKIP,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM annotation_runs").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        if n < len(ANNOTATION_RUNS):
            raise AssertionError(
                f"annotation_runs has {n} rows; expected ≥ {len(ANNOTATION_RUNS)}"
            )
