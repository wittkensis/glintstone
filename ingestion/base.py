"""Connector contract + RunContext for the ingestion framework.

A connector subclasses `SourceConnector` and implements:

    class CdliCatalogConnector(SourceConnector):
        id = "cdli-catalog"
        display_name = "CDLI Artifact Catalog"
        kind = "catalog"
        runs_after = ["lookup-tables"]
        license = "CC-BY-NC-3.0"
        upstream_url = "https://cdli.mpiwg-berlin.mpg.de/cdli_cat.csv"

        def discover(self, ctx) -> SourceManifest: ...
        def extract(self, ctx) -> Iterator[dict]: ...
        def transform(self, ctx, record) -> Iterator[dict]: ...
        def load(self, ctx, rows) -> LoadStats: ...
        def verify(self, ctx) -> None: ...

The framework wraps these into a single run with progress tracked in the
database (import_runs), every dead-letter routed (import_dead_letters), and
structured events logged (import_run_events).
"""

from __future__ import annotations

import abc
import json as _json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Iterable, Iterator, Optional

# Set GLINTSTONE_LOG_FORMAT=json to emit JSON lines; default is human-readable.
_LOG_FORMAT = os.environ.get("GLINTSTONE_LOG_FORMAT", "human")


class RunMode(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    RANGE = "range"
    DRY_RUN = "dry_run"
    VERIFY_ONLY = "verify_only"


class ConflictPolicy(str, Enum):
    SKIP = "skip"
    UPDATE = "update"
    REPLACE = "replace"


@dataclass
class SourceManifest:
    """What `discover()` returns: what's upstream right now.

    A connector compares this against the previous successful run's
    `source_checksum` and `source_fetched_at` to decide whether to skip.
    """

    checksum: Optional[str] = None
    fetched_at: Optional[datetime] = None
    record_count_estimate: Optional[int] = None
    raw_path: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class LoadStats:
    """Result of `load()` — what got written, what was skipped."""

    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    dead_lettered: int = 0

    def merge(self, other: "LoadStats") -> "LoadStats":
        return LoadStats(
            inserted=self.inserted + other.inserted,
            updated=self.updated + other.updated,
            skipped=self.skipped + other.skipped,
            dead_lettered=self.dead_lettered + other.dead_lettered,
        )


class RunContext:
    """Per-run state passed to every connector method.

    Owns the DB connection used for upserts, the run_id for correlation in
    `import_runs` / `import_run_events`, and the DeadLetterSink. Provides
    `log()` for structured events, `record_stats()` for incremental progress,
    and a `dead_letter()` shortcut.
    """

    def __init__(
        self,
        *,
        run_id: int,
        connector_id: str,
        mode: RunMode,
        db_conn: Any,
        dead_letter_sink: Any,
        config: Optional[dict] = None,
    ) -> None:
        self.run_id = run_id
        self.connector_id = connector_id
        self.mode = mode
        self.db = db_conn
        self.dead_letters = dead_letter_sink
        self.config = config or {}
        self.stats = LoadStats()

    def log(
        self,
        level: str,
        message: str,
        **context: Any,
    ) -> None:
        """Write a row to import_run_events and emit to stdout.

        Set GLINTSTONE_LOG_FORMAT=json for JSON-lines output (log aggregators).
        Default is human-readable for interactive sessions.
        """
        self.db.execute(
            """
            INSERT INTO import_run_events (run_id, level, message, context)
            VALUES (%s, %s, %s, %s::jsonb)
            """,
            (self.run_id, level, message, _json_or_null(context)),
        )
        self.db.commit()
        if _LOG_FORMAT == "json":
            entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "run_id": self.run_id,
                "connector": self.connector_id,
                "level": level,
                "msg": message,
            }
            if context:
                entry.update(context)
            print(_json.dumps(entry, default=str), file=sys.stderr)
        else:
            print(f"  [{level}] {message}" + (f"  {context}" if context else ""))

    def info(self, msg: str, **ctx: Any) -> None:
        self.log("info", msg, **ctx)

    def warn(self, msg: str, **ctx: Any) -> None:
        self.log("warn", msg, **ctx)

    def error(self, msg: str, **ctx: Any) -> None:
        self.log("error", msg, **ctx)

    def dead_letter(
        self,
        *,
        category: str,
        payload: dict,
        reason: str,
        subcategory: Optional[str] = None,
        source_key: Optional[str] = None,
    ) -> None:
        self.dead_letters.write(
            run_id=self.run_id,
            connector_id=self.connector_id,
            category=category,
            subcategory=subcategory,
            source_key=source_key,
            payload=payload,
            reason=reason,
        )
        self.stats.dead_lettered += 1

    def add_stats(self, other: LoadStats) -> None:
        self.stats = self.stats.merge(other)


def _json_or_null(value: Optional[dict]) -> Optional[str]:
    if value is None or not value:
        return None
    import json

    return json.dumps(value, default=str, ensure_ascii=False)


class SourceConnector(abc.ABC):
    """Base contract every data-source class implements.

    Subclasses declare these class attributes:

      id            stable identifier ("cdli-catalog")
      display_name  human-readable name shown in the dashboard
      kind          'catalog' | 'corpus' | 'lexicon' | 'annotation' | 'lookup' | 'derived'
      runs_after    list of connector ids that must run first
      license       upstream license (informational only — actual enforcement is editorial)
      upstream_url  where the source data lives (for docs and link-outs)
      citation      required citation string per the upstream's terms
    """

    id: ClassVar[str]
    display_name: ClassVar[str]
    kind: ClassVar[str] = "catalog"
    runs_after: ClassVar[list[str]] = []
    license: ClassVar[Optional[str]] = None
    license_url: ClassVar[Optional[str]] = None
    upstream_url: ClassVar[Optional[str]] = None
    citation: ClassVar[Optional[str]] = None
    contact_email: ClassVar[Optional[str]] = None
    description: ClassVar[Optional[str]] = None

    # Validation of `id` and `display_name` happens at registry-load time
    # (ingestion.registry.discover_connectors) — at class-creation time, the
    # ABC machinery hasn't yet populated `__abstractmethods__`, so we can't
    # reliably distinguish abstract bases from concrete subclasses here.

    # --- Lifecycle methods (override these in subclasses) ---

    def discover(self, ctx: RunContext) -> SourceManifest:
        """Return a manifest describing the upstream source's current state.

        Default implementation returns an empty manifest (always-run). Override
        when the source supports cheap freshness checks (HTTP HEAD, ETag, file
        mtime, etc.) so unchanged sources can short-circuit the run.
        """
        return SourceManifest()

    @abc.abstractmethod
    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield raw records from the upstream source, one dict per record."""

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        """Convert a raw record into one or more target-shaped rows.

        Default identity passthrough. Override when the source needs reshaping
        or splitting (one raw record → many target rows).
        """
        yield record

    @abc.abstractmethod
    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        """Persist a batch of transformed rows. Must be safe to re-run."""

    def verify(self, ctx: RunContext) -> None:
        """Post-load sanity checks. Raise on failure.

        Default is no-op. Override to add invariants like row-count floors,
        FK integrity spot-checks, etc.
        """

    # --- Optional metadata for the registry ---

    @classmethod
    def to_source_row(cls) -> dict:
        """Return a row suitable for upserting into the `sources` table."""
        return {
            "id": cls.id,
            "display_name": cls.display_name,
            "description": cls.description,
            "kind": cls.kind,
            "upstream_url": cls.upstream_url,
            "license": cls.license,
            "license_url": cls.license_url,
            "citation": cls.citation,
            "contact_email": cls.contact_email,
            "runs_after": list(cls.runs_after),
        }


class ModelConnector(SourceConnector):
    """Specialization for ML model runs (HuggingFace, BabyLemmatizer, DETR…).

    Models emit annotations rather than fetch external data, so the contract
    swaps `extract()` for `predict()`. The framework binds a `model_registry`
    row to the run so every emitted annotation traces back to a specific model
    version.
    """

    kind: ClassVar[str] = "model"

    model_name: ClassVar[str]
    model_version: ClassVar[str]
    hf_repo: ClassVar[Optional[str]] = None
    checkpoint_uri: ClassVar[Optional[str]] = None

    @abc.abstractmethod
    def predict(self, ctx: RunContext) -> Iterator[dict]:
        """Yield model output records, one per inference. Each dict should
        carry the input identifier and the predicted fields plus a confidence
        score where applicable."""

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # ModelConnector subclasses implement `predict`; framework adapts.
        return self.predict(ctx)

    def register_model_version(self, db_conn: Any) -> int:
        """Idempotently upsert this model's row into model_registry; return id."""
        row = db_conn.execute(
            """
            INSERT INTO model_registry (name, version, hf_repo, checkpoint_uri, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name, version) DO UPDATE
                SET hf_repo = EXCLUDED.hf_repo,
                    checkpoint_uri = EXCLUDED.checkpoint_uri
            RETURNING id
            """,
            (
                self.model_name,
                self.model_version,
                self.hf_repo,
                self.checkpoint_uri,
                self.description,
            ),
        ).fetchone()
        db_conn.commit()
        return row["id"] if isinstance(row, dict) else row[0]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
