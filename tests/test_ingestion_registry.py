"""Tests for the connector registry: discovery, topo sort, cycle detection."""

from __future__ import annotations

import pytest

from ingestion.base import LoadStats, SourceConnector
from ingestion.registry import ConnectorRegistry, topological_sort


def _make_connector(connector_id: str, *, runs_after=()):
    """Build a concrete SourceConnector subclass on the fly.

    Note: class bodies have their own scope and can't close over outer
    locals, so we capture runs_after into a class-body local via a default
    value trick on a method, then assign to the class attribute below.
    """

    deps = list(runs_after)

    class _Tmp(SourceConnector):
        id = connector_id
        display_name = connector_id.replace("-", " ").title()

        def extract(self, ctx):
            return iter([])

        def load(self, ctx, rows):
            return LoadStats()

    _Tmp.runs_after = deps
    _Tmp.__name__ = f"Connector_{connector_id}"
    return _Tmp


def test_topological_sort_orders_by_dependencies():
    a = _make_connector("a")
    b = _make_connector("b", runs_after=["a"])
    c = _make_connector("c", runs_after=["b"])
    connectors = {"c": c, "b": b, "a": a}
    out = topological_sort(connectors)
    ids = [cls.id for cls in out]
    assert ids == ["a", "b", "c"]


def test_topological_sort_independent_connectors_alphabetical():
    z = _make_connector("z")
    a = _make_connector("a")
    m = _make_connector("m")
    out = topological_sort({"z": z, "a": a, "m": m})
    assert [cls.id for cls in out] == ["a", "m", "z"]


def test_topological_sort_detects_cycle():
    a = _make_connector("cycle-a", runs_after=["cycle-b"])
    b = _make_connector("cycle-b", runs_after=["cycle-a"])
    with pytest.raises(ValueError, match="cycle"):
        topological_sort({"cycle-a": a, "cycle-b": b})


def test_topological_sort_unknown_dep_tolerated():
    """A runs_after id we don't know about counts as already satisfied."""
    a = _make_connector("only-a", runs_after=["never-registered"])
    out = topological_sort({"only-a": a})
    assert [cls.id for cls in out] == ["only-a"]


def test_registry_get_raises_on_unknown_id():
    reg = ConnectorRegistry([_make_connector("only-known")])
    with pytest.raises(KeyError):
        reg.get("nope")


def test_registry_contains():
    reg = ConnectorRegistry([_make_connector("known-one")])
    assert "known-one" in reg
    assert "unknown" not in reg


def test_registry_discovers_real_connectors():
    """The default registry should find at least the two we ship."""
    reg = ConnectorRegistry()
    ids = {c.id for c in reg.all()}
    assert "cdli-catalog" in ids
    assert "translation-line-matcher" in ids


def test_registry_ordering_respects_real_deps():
    """cdli-catalog must come before translation-line-matcher per declared deps."""
    reg = ConnectorRegistry()
    ordered = [c.id for c in reg.ordered()]
    if "cdli-catalog" in ordered and "translation-line-matcher" in ordered:
        assert ordered.index("cdli-catalog") < ordered.index("translation-line-matcher")
