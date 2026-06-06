"""Typed GlintstoneAPI client for App → API communication.

All domain methods degrade gracefully on failure — they return an empty Page or {}
rather than raising. This keeps the degrade-to-empty rule in one place instead of
scattered across 40 route call sites.

The low-level passthrough methods (get/post/put/patch/delete) ARE allowed to raise;
they are used by auth callbacks, admin routes, and any route that needs explicit
error propagation (e.g., redirect on 401 via httpx.HTTPStatusError).
"""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from app.transports import Transport

T = TypeVar("T")


class AuthRequiredError(Exception):
    """Raised by transport when the API returns 401.

    The web app exception handler in main.py catches this and redirects to /auth/login.
    """


@dataclass
class Page(Generic[T]):
    """Paginated response envelope from the Glintstone API."""

    items: list[T] = field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 24
    total_pages: int = 0
    has_next: bool = False
    filter_options: dict = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "Page":
        return cls()

    @classmethod
    def from_dict(cls, data: dict) -> "Page":
        return cls(
            items=data.get("items", []),
            total=data.get("total", 0),
            page=data.get("page", 1),
            per_page=data.get("per_page", 24),
            total_pages=data.get("total_pages", 0),
            has_next=data.get(
                "has_next",
                (data.get("page", 1) < data.get("total_pages", 0))
                if data.get("total_pages")
                else False,
            ),
            filter_options=data.get("filter_options") or {},
        )


class GlintstoneAPI:
    """Typed API client — wraps a Transport and exposes domain-level methods.

    Domain methods never raise; they return Page.empty() or {} on any error.
    Passthrough methods (get/post/put/patch/delete) do raise — for routes that
    need explicit error handling (auth callbacks, admin actions, etc.).
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    @property
    def base_url(self) -> str:
        """Expose base_url for templates that need to build API image URLs."""
        client = getattr(self._t, "_client", None)
        if client is None:
            return ""
        return str(getattr(client, "base_url", ""))

    def close(self) -> None:
        self._t.close()

    # ── Artifacts ──────────────────────────────────────────────────────────────

    def list_artifacts(self, params: dict) -> "Page":
        try:
            return Page.from_dict(self._t.get("/artifacts", params=params))  # type: ignore[arg-type]
        except Exception:
            return Page.empty()

    def get_artifact(self, p_number: str, token: str | None = None) -> dict:
        try:
            return self._t.get(f"/artifacts/{p_number}", token=token)  # type: ignore[return-value]
        except Exception:
            return {}

    def get_artifact_debug(self, p_number: str) -> dict:
        try:
            return self._t.get(f"/artifacts/{p_number}/debug")  # type: ignore[return-value]
        except Exception:
            return {}

    # ── Auth / User ────────────────────────────────────────────────────────────

    def get_me(self, token: str) -> dict:
        try:
            return self._t.get("/auth/me", token=token)  # type: ignore[return-value]
        except Exception:
            return {}

    def get_saved_items(self, params: dict, token: str) -> list:
        try:
            result = self._t.get("/users/me/saved-items", params=params, token=token)
            return result if isinstance(result, list) else []
        except Exception:
            return []

    def save_item(self, body: dict, token: str) -> dict:
        try:
            return self._t.post("/users/me/saved-items", json=body, token=token)
        except Exception:
            return {}

    def delete_saved_item(self, item_id: str, token: str) -> None:
        try:
            self._t.delete(f"/users/me/saved-items/{item_id}", token=token)
        except Exception:
            pass

    # ── Dictionary ─────────────────────────────────────────────────────────────

    def browse_dictionary(self, params: dict) -> "Page":
        try:
            return Page.from_dict(self._t.get("/dictionary/browse", params=params))  # type: ignore[arg-type]
        except Exception:
            return Page.empty()

    def get_dictionary_filter_options(self, params: dict) -> dict:
        try:
            result = self._t.get("/dictionary/filter-options", params=params)
            return result if isinstance(result, dict) else {}  # type: ignore[return-value]
        except Exception:
            return {}

    def get_lemma(self, lemma_id: int) -> dict:
        try:
            return self._t.get(f"/dictionary/lemmas/{lemma_id}")  # type: ignore[return-value]
        except Exception:
            return {}

    def get_sign(self, sign_id: int) -> dict:
        try:
            return self._t.get(f"/dictionary/signs/{sign_id}")  # type: ignore[return-value]
        except Exception:
            return {}

    # ── Scholars ───────────────────────────────────────────────────────────────

    def list_scholars(self, params: dict) -> "Page":
        try:
            return Page.from_dict(self._t.get("/scholars", params=params))  # type: ignore[arg-type]
        except Exception:
            return Page.empty()

    def get_scholar(self, scholar_id: int) -> dict:
        try:
            return self._t.get(f"/scholars/{scholar_id}")  # type: ignore[return-value]
        except Exception:
            return {}

    # ── Collections ────────────────────────────────────────────────────────────

    def list_collections(self, params: dict | None = None) -> "Page":
        try:
            return Page.from_dict(self._t.get("/collections", params=params))  # type: ignore[arg-type]
        except Exception:
            return Page.empty()

    def get_collection(self, collection_id: int) -> dict:
        try:
            return self._t.get(f"/collections/{collection_id}")  # type: ignore[return-value]
        except Exception:
            return {}

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(self, params: dict) -> dict:
        """Returns the raw search envelope (not a Page — search has nested 'data.groups' shape)."""
        try:
            result = self._t.get("/search", params=params)
            return result if isinstance(result, dict) else {}  # type: ignore[return-value]
        except Exception:
            return {}

    # ── Compositions / Composites ──────────────────────────────────────────────
    # API uses /composites (canonical texts); app routes use /compositions (UI path).

    def list_composites(self, params: dict) -> "Page":
        try:
            return Page.from_dict(self._t.get("/composites", params=params))  # type: ignore[arg-type]
        except Exception:
            return Page.empty()

    def get_composite(self, q_number: str) -> dict:
        try:
            return self._t.get(f"/composites/{q_number}")  # type: ignore[return-value]
        except Exception:
            return {}

    def get_composite_exemplars(self, q_number: str) -> dict:
        try:
            data = self._t.get(f"/composites/{q_number}/exemplars")
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    # ── Stats / Homepage ───────────────────────────────────────────────────────

    def get_kpi(self) -> dict:
        try:
            return self._t.get("/stats/kpi") or {}  # type: ignore[return-value]
        except Exception:
            return {}

    def get_coverage_gaps(self, params: dict) -> dict:
        try:
            return self._t.get("/stats/coverage-gaps", params=params) or {}  # type: ignore[return-value]
        except Exception:
            return {}

    # ── Feedback / Agentic ─────────────────────────────────────────────────────

    def post_feedback(self, body: dict, token: str | None = None) -> dict:
        try:
            return self._t.post("/agentic/feedback", json=body, token=token)
        except Exception:
            return {}

    # ── Low-level passthrough ──────────────────────────────────────────────────
    # Intentionally raising — used by auth callbacks, admin routes, and any route
    # that catches specific exception types (httpx.HTTPStatusError, etc.).

    def get(
        self, path: str, params: dict | None = None, token: str | None = None
    ) -> dict | list:
        return self._t.get(path, params=params, token=token)

    def post(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict:
        return self._t.post(path, json=json, token=token)

    def put(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict:
        return self._t.put(path, json=json, token=token)

    def patch(
        self, path: str, json: dict | None = None, token: str | None = None
    ) -> dict | None:
        return self._t.patch(path, json=json, token=token)

    def delete(self, path: str, token: str | None = None) -> dict | None:
        return self._t.delete(path, token=token)
