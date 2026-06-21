"""Regression: the Voyage query vector must reach `%s::vector` as pgvector's
text form ("[a, b, c]"), not a Python list (which psycopg sends as a Postgres
array "{a,b,c}" that `::vector` cannot cast). When that cast failed the
exception was swallowed and semantic search silently degraded to lexical —
0 semantic hits despite 1.3M embeddings (#235).
"""

from __future__ import annotations

from core.agent.search_engine import SearchEngine


class _FakeVoyage:
    def embed_query(self, q: str):  # mirrors VoyageClient.embed_query
        class _R:
            vector = [0.1, 0.2, 0.3]

        return _R()


class _FakeCursor:
    def __init__(self, captured: list) -> None:
        self._captured = captured

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def execute(self, sql: str, params) -> None:
        self._captured.append((sql, params))

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self) -> None:
        self.captured: list = []

    def cursor(self):
        return _FakeCursor(self.captured)


def test_query_vector_passed_as_pgvector_string():
    engine = SearchEngine(voyage=_FakeVoyage())
    conn = _FakeConn()

    engine._semantic_search(conn, "a sealed envelope", ["tablets"], limit=5)

    assert conn.captured, "semantic query was never executed"
    # The engine first issues `SET LOCAL hnsw.ef_search` (no bound params) to tune
    # HNSW recall, then the vector query. Find the query that carries params.
    vector_calls = [(sql, p) for sql, p in conn.captured if p]
    assert vector_calls, "vector query was never executed"
    _sql, params = vector_calls[0]
    # First and third positional params are the vector (used twice per KNN leg).
    vec_param = params[0]
    assert isinstance(vec_param, str), (
        "query vector must be a string for ::vector cast, "
        f"got {type(vec_param).__name__}"
    )
    assert vec_param.startswith("[") and vec_param.endswith("]"), (
        f"vector must be pgvector text form '[...]', got {vec_param!r}"
    )
    # Same string is reused for the ORDER BY cast.
    assert params[2] == vec_param
