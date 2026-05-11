"""Glintstone v2 ingestion framework.

Every data source — external dataset, ML model, derived computation — is a
subclass of `SourceConnector`. The framework supplies:

- A `RunContext` that tracks progress in DB tables (import_runs,
  import_run_events) instead of disk JSON files
- A `DeadLetterSink` that routes every record that fails to integrate to
  `import_dead_letters` with category, payload, and resolution status
- A `Loader` with safe-rerun (upsert) helpers
- Source fingerprinting (checksum + timestamp) so unchanged sources exit
  immediately on re-run
- A CLI (`glintstone-ingest`) that discovers connectors, orders them by
  declared dependencies, and runs them

A new connector subclasses `SourceConnector`, declares its `id`, `kind`,
`runs_after`, and overrides `discover`, `extract`, `transform`, `load`,
`verify`. A new HuggingFace model subclasses `ModelConnector` and supplies
`predict()` instead of `extract()`.
"""

from ingestion.base import (
    ConflictPolicy,
    LoadStats,
    ModelConnector,
    RunContext,
    RunMode,
    SourceConnector,
    SourceManifest,
)
from ingestion.dead_letters import DeadLetterCategory, DeadLetterSink
from ingestion.registry import ConnectorRegistry, discover_connectors

__all__ = [
    "ConflictPolicy",
    "ConnectorRegistry",
    "DeadLetterCategory",
    "DeadLetterSink",
    "LoadStats",
    "ModelConnector",
    "RunContext",
    "RunMode",
    "SourceConnector",
    "SourceManifest",
    "discover_connectors",
]
