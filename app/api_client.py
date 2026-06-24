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
    # Distinct annotation-run count for the scholar contributions ledger. 0 for
    # endpoints that don't report it (the field is simply absent in their JSON).
    run_count: int = 0

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
            run_count=data.get("run_count", 0),
        )


def _empty_publications() -> dict:
    """The publications envelope shape when there's nothing (or a fetch failed).

    Mirrors the API's keys so the template's #189 empty path is uniform whether
    the scholar genuinely has zero works or the API call errored.
    """
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "per_page": 50,
        "total_pages": 0,
        "summary": {
            "works": 0,
            "total_cites": 0,
            "top_cites": None,
            "first_year": None,
            "last_year": None,
            "type_count": 0,
            "tablets_edited": 0,
        },
        "type_counts": [],
        "type": "",
    }


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

    def get_artifacts_timeline(self, params: dict) -> list:
        """Per-period counts over the current filter (Corpus-Atlas timeline).

        Degrades to an empty list on any failure so the timeline view falls
        back to its plain period-count rendering rather than 500-ing the page.
        """
        try:
            result = self._t.get("/artifacts/timeline", params=params)
            return result.get("items", []) if isinstance(result, dict) else []
        except Exception:
            return []

    def get_artifacts_by_site(self, params: dict) -> list:
        """Ranked find-spots by tablet count over the current filter
        (Corpus-Atlas geography lens). Empty list on failure."""
        try:
            result = self._t.get("/artifacts/by-site", params=params)
            return result.get("items", []) if isinstance(result, dict) else []
        except Exception:
            return []

    def get_site_coords(self) -> dict:
        """Geolocated find-spots for the map layer (#197–#199 / #319).

        Returns ``{"sites": [{ancient_name, modern_name, latitude, longitude,
        pleiades_id, region, tablet_count}, ...], "uncertain": {"tablet_count":
        N}}`` — one entry per geocoded ancient site, ordered busiest-first, plus
        the aggregate count of uncertain-provenance tablets that are never
        pinned (#313). Degrades to an empty, well-formed envelope on any
        failure so the map view falls back to its caption-only state rather
        than 500-ing the page.
        """
        try:
            result = self._t.get("/proveniences/coords")
            if isinstance(result, dict) and "sites" in result:
                return result
        except Exception:
            pass
        return {"sites": [], "uncertain": {"tablet_count": 0}}

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

    def get_scholar_facets(self, params: dict) -> dict:
        """Facet counts for the all-scholars index filter rail (#194).

        Returns ``{total, institution: [...], has_orcid: {with, without}}``.
        Degrades to an explicit-empty envelope on any failure so the index
        renders without a rail rather than 500-ing — a facet-fetch error must
        never blank the page.
        """
        try:
            result = self._t.get("/scholars/facets", params=params)
            if isinstance(result, dict):
                return result  # type: ignore[return-value]
        except Exception:
            pass
        return {"total": 0, "institution": [], "has_orcid": {"with": 0, "without": 0}}

    def get_scholar(self, scholar_id: int) -> dict:
        try:
            return self._t.get(f"/scholars/{scholar_id}")  # type: ignore[return-value]
        except Exception:
            return {}

    def get_scholar_activity(self, scholar_id: int) -> dict:
        """Compact activity profile for a scholar (#157) — period histogram +
        role breakdown. Degrades to an explicit-empty envelope on any failure so
        the detail page renders the #189 empty state rather than 500-ing; an
        activity-fetch error must never blank the whole scholar page.
        """
        try:
            result = self._t.get(f"/scholars/{scholar_id}/activity")
            return result if isinstance(result, dict) else {}  # type: ignore[return-value]
        except Exception:
            return {}

    def get_scholar_contributions(self, scholar_id: int, params: dict) -> "Page":
        try:
            return Page.from_dict(
                self._t.get(f"/scholars/{scholar_id}/contributions", params=params)  # type: ignore[arg-type]
            )
        except Exception:
            return Page.empty()

    def get_scholar_publications(self, scholar_id: int, params: dict) -> dict:
        """Publications & works for a scholar.

        Unlike the other paginated endpoints this returns the raw envelope, not
        a ``Page``: the publications response carries a richer shape — a
        ``summary`` (five stat-strip aggregates) and a ``type_counts`` breakdown
        (for the filter pills) alongside the paginated ``items``. Wrapping it in
        the flat ``Page`` would drop those, so the template consumes the dict
        directly. On any error we degrade to an explicit empty envelope so the
        detail page renders the #189 "No publications on record" panel rather
        than 500-ing — a works-fetch failure must never blank the whole page.
        """
        try:
            result = self._t.get(f"/scholars/{scholar_id}/publications", params=params)
            return result if isinstance(result, dict) else _empty_publications()  # type: ignore[return-value]
        except Exception:
            return _empty_publications()

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

    # ── Periods ────────────────────────────────────────────────────────────────

    def get_periods(self) -> dict:
        """Canonical historical periods with BCE date ranges.

        Returns the raw ``{"items": [...]}`` envelope from the API so the
        transmission-timeline JS can read ``items[].canonical /
        date_start_bce / date_end_bce / sort_order / group_name`` directly.
        Degrades to an empty envelope on any error so the browser-side fetch
        gets valid JSON (and the timeline falls back gracefully) rather than
        a 502.
        """
        try:
            result = self._t.get("/periods")
            return result if isinstance(result, dict) else {"items": []}  # type: ignore[return-value]
        except Exception:
            return {"items": []}

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

    def get_composite_related(self, q_number: str) -> dict:
        """Compositions related to this one by shared witnesses (#160)."""
        try:
            data = self._t.get(f"/composites/{q_number}/related")
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def get_composite_summary(self, q_number: str) -> dict:
        """Grounded AI synthesis across a composition's witnesses (#168)."""
        try:
            data = self._t.get(f"/composites/{q_number}/summary")
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
