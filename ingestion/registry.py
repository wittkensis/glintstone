"""Connector discovery and dependency-graph ordering.

Importing this module crawls `ingestion.connectors.*` and collects every
concrete subclass of SourceConnector. The CLI uses this to list connectors,
order them by `runs_after`, and dispatch by id.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from ingestion.base import SourceConnector


def discover_connectors() -> list[type[SourceConnector]]:
    """Import every module in `ingestion.connectors` and collect subclasses.

    Idempotent — calling twice doesn't double-register because Python's import
    cache returns the same class objects.
    """
    import ingestion.connectors as pkg

    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"ingestion.connectors.{name}")

    seen: dict[str, type[SourceConnector]] = {}
    stack: list[type[SourceConnector]] = list(SourceConnector.__subclasses__())
    while stack:
        cls = stack.pop()
        stack.extend(cls.__subclasses__())
        # Skip abstract bases (those still carrying unimplemented abstractmethods
        # like ModelConnector, which has `predict` but no concrete `id`).
        if getattr(cls, "__abstractmethods__", set()):
            continue
        # Only register classes that live in the ingestion.connectors package.
        # Test fixtures and synthetic in-test subclasses are excluded so the
        # production registry stays focused on shipped connectors.
        module = cls.__module__ or ""
        if not module.startswith("ingestion.connectors"):
            continue
        if not getattr(cls, "id", None):
            raise TypeError(
                f"{cls.__module__}.{cls.__name__} is concrete but missing `id`"
            )
        if not getattr(cls, "display_name", None):
            raise TypeError(
                f"{cls.__module__}.{cls.__name__} is concrete but missing `display_name`"
            )
        if cls.id in seen and seen[cls.id] is not cls:
            raise RuntimeError(
                f"Duplicate connector id {cls.id!r}: "
                f"{seen[cls.id].__module__} vs {cls.__module__}"
            )
        seen[cls.id] = cls
    return list(seen.values())


class ConnectorRegistry:
    """Registry built from discover_connectors()."""

    def __init__(
        self, connectors: Iterable[type[SourceConnector]] | None = None
    ) -> None:
        self._connectors: dict[str, type[SourceConnector]] = {
            c.id: c
            for c in (connectors if connectors is not None else discover_connectors())
        }

    def __contains__(self, connector_id: str) -> bool:
        return connector_id in self._connectors

    def get(self, connector_id: str) -> type[SourceConnector]:
        if connector_id not in self._connectors:
            raise KeyError(
                f"Unknown connector: {connector_id!r}. "
                f"Known: {sorted(self._connectors)}"
            )
        return self._connectors[connector_id]

    def all(self) -> list[type[SourceConnector]]:
        return list(self._connectors.values())

    def ordered(self) -> list[type[SourceConnector]]:
        """Return connectors in topological order respecting `runs_after`.

        Raises ValueError on a cycle.
        """
        return topological_sort(self._connectors)


def topological_sort(
    connectors: dict[str, type[SourceConnector]],
) -> list[type[SourceConnector]]:
    """Kahn's algorithm over connector ids, returning concrete classes."""
    # Build adjacency: dependency → connectors that depend on it.
    indegree: dict[str, int] = {cid: 0 for cid in connectors}
    children: dict[str, list[str]] = {cid: [] for cid in connectors}
    for cid, cls in connectors.items():
        for dep in cls.runs_after:
            if dep not in connectors:
                # Unknown deps are tolerated (might not be registered yet);
                # they just count as already satisfied.
                continue
            indegree[cid] += 1
            children[dep].append(cid)

    ready = sorted(cid for cid, n in indegree.items() if n == 0)
    out: list[type[SourceConnector]] = []
    while ready:
        cid = ready.pop(0)
        out.append(connectors[cid])
        for child in children[cid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort()

    if len(out) != len(connectors):
        cycle_members = sorted(cid for cid, n in indegree.items() if n > 0)
        raise ValueError(f"Dependency cycle among connectors: {cycle_members}")
    return out
