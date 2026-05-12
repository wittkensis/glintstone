"""Named test/demo records.

Mirror of .claude/skills/gs-curator-artifacts/catalog.yaml. Update both files
together when adding a new fixture (gs-curator-docs flags drift on push).

Naming convention: <USEFULNESS>_<SCENARIO>[_<ENTITY_TYPE>].
"""

# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

ONBOARDING_DEMO_LEXICAL = "P227657"
"""KTT 188 — Sumerian Old Babylonian word list, 265 lines, 259 translations."""

EDGE_CASE_JOINED_FRAGMENT = "P229672"
"""K 03254 + K 03779 — Neo-Assyrian joined fragments. Tests `+` parsing,
composite linkage, complex ATF."""

REGRESSION_UR_III_LEXICAL = "P247526"
"""BM 103142 — Ur III Sumerian lexical text, compound terms, broken lines."""

REGRESSION_BILINGUAL = "P001282"
"""Sumerian-Akkadian bilingual; tests post-migration-011 per-word language
column. Verify against Neon before relying on this in CI."""

# ---------------------------------------------------------------------------
# Lemmas
# ---------------------------------------------------------------------------

ONBOARDING_DEMO_LEMMA_SUMERIAN = "epsd2/lugal"
"""Sumerian 'king'. 20+ senses, 2,000+ attestations. The classic
high-polysemy example."""

DOMAIN_RICH_LEMMA_AKKADIAN_LOGOGRAM = (
    "oracc/saao/sharru"  # write 'sharru' as šarru in queries
)
"""Akkadian 'king', written with the LUGAL Sumerogram. Demonstrates
cross-language Sumerogram resolution via cad_logograms."""

PERFORMANCE_TEST_TOP_LEMMA = "epsd2/ninda"
"""Sumerian 'bread, food'. 109,427 attestations — the top of the
critical-cache. Tests the hot path."""

# ---------------------------------------------------------------------------
# Signs
# ---------------------------------------------------------------------------

ONBOARDING_DEMO_SIGN_POLYVALENT = "KA"
"""KA sign — reads as ka, gu, dug, inim, zu in Sumerian; serves as Sumerogram
for Akkadian pû 'mouth'. The polyvalency teaching example."""

# ---------------------------------------------------------------------------
# Periods / proveniences / genres
# ---------------------------------------------------------------------------

ONBOARDING_DEMO_PERIOD = "Ur III"
REGRESSION_TEST_PERIOD = "Neo-Assyrian"
ONBOARDING_DEMO_PROVENIENCE = "Nippur"
REGRESSION_TEST_PROVENIENCE = "Tello"  # canonical form may be "Girsu"
ONBOARDING_DEMO_GENRE = "Lexical"
UX_STRESS_GENRE = "Royal inscription"

# ---------------------------------------------------------------------------
# Search terms
# ---------------------------------------------------------------------------

ONBOARDING_DEMO_SEARCH = "lugal"
EDGE_CASE_SEARCH_BIGRAM = "ninda kasz"
UX_STRESS_SEARCH_UNICODE = "\U00012157"  # 𒈗 LUGAL

# ---------------------------------------------------------------------------
# Annotation runs
# ---------------------------------------------------------------------------

DOMAIN_RICH_ML_RUN = "babylemmatizer-v2.1"
"""Demonstrates ML-vs-human competing-interpretations pattern."""

ONBOARDING_DEMO_HUMAN_RUN = "oracc/rinap"
"""Project-scoped ORACC annotation run."""


# ---------------------------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------------------------

SCENARIO_SIMPLE_ONBOARDING = {
    "artifact": ONBOARDING_DEMO_LEXICAL,
    "genre": ONBOARDING_DEMO_GENRE,
    "period": "Old Babylonian",
    "search": ONBOARDING_DEMO_SEARCH,
}

SCENARIO_JOINED_DAMAGED = {
    "artifact": EDGE_CASE_JOINED_FRAGMENT,
}

SCENARIO_CROSS_LANGUAGE_SUMEROGRAM = {
    "sign": ONBOARDING_DEMO_SIGN_POLYVALENT,
    "sumerian_lemma": "epsd2/ka",
    "akkadian_lemma": DOMAIN_RICH_LEMMA_AKKADIAN_LOGOGRAM,
}

SCENARIO_COMPETING_INTERPRETATIONS = {
    "artifact": REGRESSION_BILINGUAL,
    "ml_run": DOMAIN_RICH_ML_RUN,
    "human_run": ONBOARDING_DEMO_HUMAN_RUN,
}

SCENARIO_HIGH_POLYSEMY = {
    "lemma": ONBOARDING_DEMO_LEMMA_SUMERIAN,
}

SCENARIO_PERFORMANCE_HOT_PATH = {
    "lemma": PERFORMANCE_TEST_TOP_LEMMA,
}
