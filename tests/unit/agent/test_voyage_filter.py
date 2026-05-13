"""filter_unchanged hash-skip logic — no Voyage API calls."""

from core.agent.voyage_client import _hash, filter_unchanged


def test_filter_unchanged_returns_only_changed():
    texts = {"a": "hello", "b": "world", "c": "again"}
    existing = {"a": _hash("hello"), "b": _hash("OLD"), "c": _hash("again")}
    changed = filter_unchanged(texts, existing)
    assert changed == {"b": "world"}


def test_filter_unchanged_includes_new_ids():
    texts = {"a": "hello", "b": "world"}
    existing = {"a": _hash("hello")}  # b not yet embedded
    changed = filter_unchanged(texts, existing)
    assert changed == {"b": "world"}


def test_hash_is_deterministic():
    assert _hash("foo") == _hash("foo")
    assert _hash("foo") != _hash("FOO")
