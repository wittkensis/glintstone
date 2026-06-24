"""Popular / common hero-search queries to pre-warm the Voyage query-embed cache.

#253 — a COLD Voyage query embedding costs ~1.4-1.9s and is the dominant cost on
the hero search path on a cache miss (warm is ~240ms). The in-process cache in
``core/agent/search_engine.py`` is cleared on every process restart (deploy /
reboot), so the *first* search after a deploy — and any popular query that falls
out of the 5-minute TTL — pays the full cold cost.

This list is the warm-cache seed: the queries we expect scholars to hit first.
``warm_query_cache()`` (in search_engine) embeds them once at API startup and
PINS them so they never expire, keeping scenario-1 (the cold hero path) under the
800 ms budget for the common case.

Keep this list SMALL and HIGH-SIGNAL. Each entry is one Voyage embed call at
startup (batched), and a pinned entry never leaves memory. Add a query here when
search analytics show it is both common and semantically routed (not an exact
P-number / Q-number match, which short-circuits before embedding). Curated
2026-06 from the demo/onboarding search terms and the most common domain themes.
"""

# Common semantic hero-search queries (NOT exact P/Q-number lookups — those
# short-circuit before any embedding). Lowercased; the cache key is hashed from
# the raw query, so these should match the canonical form the UI sends.
POPULAR_QUERIES: list[str] = [
    # Genres / text types
    "administrative records",
    "royal inscriptions",
    "literary texts",
    "lexical lists",
    "legal documents",
    "letters",
    "school texts",
    "omens",
    "hymns and prayers",
    "mathematical texts",
    # Themes / topics
    "barley rations",
    "temple offerings",
    "land sale",
    "loan of silver",
    "king of ur",
    "flood story",
    "creation myth",
    "beer and bread",
    "seal impressions",
    "year names",
    # Deities / proper-noun themes commonly searched semantically
    "the goddess inanna",
    "the god enlil",
    "gilgamesh",
]


def popular_queries() -> list[str]:
    """Return the warm-cache seed list (copy, so callers can't mutate the seed)."""
    return list(POPULAR_QUERIES)
