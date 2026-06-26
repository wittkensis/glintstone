"""Wikidata entity linker — attaches Wikidata Q-numbers to Glintstone entities.

Issues #164 (places) and #533 (full entity import). This connector enriches the
SSOT by linking Glintstone entities to their Wikidata item (Q-number), so search,
entity profiles, and the future map can surface external context (coordinates,
sitelinks, images, descriptions, "instance of").

DATA-AVAILABILITY VERDICT (audited 2026-06 against prod before building):

  PLACES — an EXACT, ID-based path exists and is the gold standard:

      provenience_canon.pleiades_id ─(Wikidata property P1584 "Pleiades ID")→ Q

  A Pleiades ID is a stable gazetteer identifier for an ancient place; Wikidata
  stores it under property P1584. Mapping an identifier to an identifier is
  EXACT. Prod carries 151 distinct pleiades_ids; a single bulk SPARQL query
  resolves 106 of them, of which 101 are unambiguous (one Q-number) and 5 are
  ambiguous (>1 Q-number). The other 45 places are simply not in Wikidata yet.

  PERIODS / GENRES / SCRIPTS (#533) — NO external identifier exists on the
  Glintstone side (canonical_genres / canonical_languages are keyed by `name`
  only; periods are free text). Wikidata has no "Glintstone genre code" property
  to join on. The ONLY join key would be the human-readable NAME — and matching
  ancient text genres, periods, or scripts by fuzzy name is ambiguous and would
  inject misinformation into a scholarly tool. CLAUDE.md, migration 053, and the
  #164 verdict all forbid name-fuzzy matching. ACCURACY OVER COVERAGE.

  => For these classes we use a CURATED, HUMAN-VERIFIED name→QID dictionary
     (CURATED_LINKS below). The Mesopotamian period set (~15), the core
     cuneiform text genres (~20), and the cuneiform script/language set (~20)
     are small, stable, and individually verifiable. At runtime the connector
     reads the ACTUAL canonical_* names present in prod, matches each (normalized)
     against the curated dictionary, and emits a confident link ONLY for an exact
     curated hit. A canonical name with no curated entry is COUNTED and SKIPPED —
     never guessed. SPARQL is then used only to ENRICH the matched QIDs with a
     fresh label/description (validation that the QID still exists), not to
     discover matches. The curated dictionary is the source of trust; SPARQL is
     decoration. New entries are added by a human appending to CURATED_LINKS.

  COLLECTIONS / MUSEUMS (#533) — there is no collections table in the Glintstone
  schema today (artifacts carry a free-text collection string, not a normalized
  collection entity with a stable key). There is nothing to attach a Q-number to.
  This is a SCHEMA dependency, reported as a blocker on #533, NOT invented here.

  named_entities (deities / persons) remains EMPTY in prod and is still NOT
  matched by name — same misinformation rule.

Connector anatomy:
  - extract()  resolves PLACES via the bulk Pleiades SPARQL query (unchanged from
               #164), then resolves curated PERIOD/GENRE/SCRIPT links by reading
               the live canonical_* vocab and matching against CURATED_LINKS,
               enriching each curated QID with a SPARQL label/description lookup.
               Unmatched names are counted, never guessed.
  - transform() identity passthrough (extract already emits target-shaped rows).
  - load()      idempotent UPSERT into entity_wikidata_links keyed on
               (entity_type, source_key, match_basis) via ON CONFLICT.

Good-citizen policy (the CDLI IP-ban lesson):
  - BULK queries: all distinct pleiades_ids are resolved in a SINGLE SPARQL POST
    (chunked only if the VALUES list would exceed a safe size), NOT one request
    per place. A full run is ~1 HTTP request.
  - A descriptive User-Agent identifies us with a contact, per the Wikimedia
    User-Agent policy (a generic UA can get an IP blocked).
  - 429 / 5xx responses trigger bounded exponential backoff with retries; the
    Retry-After header is honored when present. A final failure dead-letters the
    affected chunk rather than aborting the run.
  - Runs are idempotent, so a partial run resumes cleanly with no duplicates.

macOS SSL note (CLAUDE.md): we shell out to ``curl`` via subprocess — urllib /
requests have intermittent SSL failures on macOS, and curl is what the prod VPS
uses. This connector is intended to run on the VPS where it reaches WDQS.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from typing import Any, Iterable, Iterator, Optional

from ingestion.base import LoadStats, RunContext, SourceConnector

# Wikidata Query Service SPARQL endpoint.
WDQS_ENDPOINT = "https://query.wikidata.org/sparql"

# Wikidata property that holds a place's Pleiades ID.
PLEIADES_PROPERTY = "P1584"

# Polite floor between WDQS requests. A full run is only a handful of requests
# (one per chunk), so this is mostly belt-and-suspenders, but we honor it.
DEFAULT_REQUEST_INTERVAL_S = 2.0

# WDQS asks every client to send a descriptive User-Agent with a contact, or
# risk being blocked. (https://meta.wikimedia.org/wiki/User-Agent_policy)
DEFAULT_USER_AGENT = (
    "Glintstone/0.1 (Assyriology entity linking; "
    "+https://app.glintstone.org; contact eric.wittke@gmail.com)"
)

# How many pleiades_ids to put in one SPARQL VALUES clause. WDQS handles large
# VALUES lists, but we chunk to keep each query well under timeout limits and to
# bound the blast radius of a single failed request. The full prod set (~151)
# fits in two chunks at this size.
DEFAULT_CHUNK_SIZE = 100

# Bounded retry policy for 429 / 5xx / timeouts.
MAX_RETRIES = 4
BACKOFF_BASE_S = 2.0
BACKOFF_CAP_S = 60.0

# Match metadata written to entity_wikidata_links.
ENTITY_TYPE_PLACE = "place"
MATCH_BASIS_PLEIADES = "pleiades"
PLEIADES_CONFIDENCE = 1.0  # exact identifier equality

# #533 entity types and their shared match basis. These have NO external ID on
# the Glintstone side, so the only confident path is a curated, human-verified
# name→QID dictionary (see CURATED_LINKS). match_basis='curated' records that the
# link came from editorial curation, not an ID join — the audit trail for trust.
ENTITY_TYPE_PERIOD = "period"
ENTITY_TYPE_GENRE = "genre"
ENTITY_TYPE_SCRIPT = "script"  # script / written-language of the tablet
MATCH_BASIS_CURATED = "curated"
# A curated link is a human-verified QID, but it is editorial judgement (a named
# concept can map to more than one defensible Wikidata item), so it is held just
# under the 1.0 reserved for pure identifier equality.
CURATED_CONFIDENCE = 0.95


def _norm(name: str) -> str:
    """Normalize a canonical name for curated-dictionary lookup.

    Lowercase, collapse internal whitespace/underscores/hyphens to single spaces,
    strip. This is NOT fuzzy matching — it only smooths spelling-of-the-same-token
    differences (e.g. 'Old Babylonian' vs 'old_babylonian'). A normalized key must
    still match a CURATED_LINKS entry EXACTLY to produce a link.
    """
    import re

    return re.sub(r"[\s_\-]+", " ", str(name).strip().lower()).strip()


# ── Curated name → Wikidata QID dictionary (#533) ─────────────────────────────
#
# Each value is (qid, expected_label). Keys are NORMALIZED canonical names (see
# _norm). A canonical_* row whose normalized name is absent here is NEVER linked
# (counted + skipped). Grow this dictionary by appending a HUMAN-VERIFIED entry —
# that is the ONLY way a new concept gets a Q-number.
#
# SELF-CHECKING DESIGN (the load-bearing safety property):
#   `expected_label` is NOT decoration — it is an ASSERTION. At run time the
#   connector fetches each QID's LIVE English label from Wikidata and writes the
#   link ONLY IF the live label agrees with expected_label (case-insensitive,
#   substring-tolerant). A QID that resolves to a DIFFERENT concept is DEAD-
#   LETTERED, never written. This caught two wrong hand-entered QIDs during build
#   (Q633538 → "structural engineering", Q1057179 → "user guide"), proving why a
#   scholarly tool must verify QIDs at write time rather than trust hand entry.
#
# REVIEW STATUS: the entries below are SEED CANDIDATES pending a full human pass
# on wikidata.org. Because each is guarded by the live-label assertion, a wrong
# candidate cannot become a live link — it dead-letters for review. The few that
# were live-verified during build are marked  # ✓verified.  Operators add/correct
# entries by checking the item page and updating (qid, expected_label) together.
#
# Verified-correct anchors (live-checked 2026-06):
#   Q401 = cuneiform ✓ ; Q723587 = Third Dynasty of Ur ✓ ; Q270860 = Sumerian
#   King List ✓ ; Q207522 = Neo-Assyrian Empire (canonical) — label-bearer differs.
CURATED_LINKS: dict[str, dict[str, tuple[str, str]]] = {
    ENTITY_TYPE_PERIOD: {
        # Mesopotamian / Ancient Near Eastern chronological periods.
        # SEED CANDIDATES — guarded by the live-label assertion (see header).
        "uruk period": ("Q1747689", "Uruk period"),
        "jemdet nasr": ("Q1370665", "Jemdet Nasr period"),
        "jemdet nasr period": ("Q1370665", "Jemdet Nasr period"),
        "early dynastic": ("Q1196152", "Early Dynastic Period"),
        "early dynastic period": ("Q1196152", "Early Dynastic Period"),
        "ur iii": ("Q723587", "Third Dynasty of Ur"),  # ✓verified
        "ur3": ("Q723587", "Third Dynasty of Ur"),  # ✓verified
        "neo sumerian": ("Q723587", "Third Dynasty of Ur"),  # ✓verified
        "isin larsa": ("Q1801676", "Isin-Larsa period"),
        "old assyrian": ("Q336528", "Old Assyrian period"),
        "old babylonian": ("Q1571162", "First Babylonian dynasty"),
        "middle assyrian": ("Q2733583", "Middle Assyrian Empire"),
        "middle babylonian": ("Q623578", "Kassite dynasty"),
        "kassite": ("Q623578", "Kassite dynasty"),
        "neo assyrian": ("Q207522", "Neo-Assyrian Empire"),
        "neo babylonian": ("Q488898", "Neo-Babylonian Empire"),
        "achaemenid": ("Q41534", "Achaemenid Empire"),
        "persian": ("Q41534", "Achaemenid Empire"),
        "hellenistic": ("Q201038", "Hellenistic period"),
        "seleucid": ("Q131551", "Seleucid Empire"),
        "parthian": ("Q165442", "Parthian Empire"),
    },
    ENTITY_TYPE_GENRE: {
        # Core cuneiform text genres / categories.
        # SEED CANDIDATES — guarded by the live-label assertion (see header).
        "administrative": ("Q193395", "administrative document"),
        "legal": ("Q7167399", "legal instrument"),
        "letter": ("Q133492", "letter"),
        "royal inscription": ("Q19842659", "royal inscription"),
        "royal": ("Q19842659", "royal inscription"),
        "literary": ("Q7257910", "literature"),
        "omen": ("Q1233711", "omen"),
        "divination": ("Q178733", "divination"),
        "hymn": ("Q484692", "hymn"),
        "hymn prayer": ("Q484692", "hymn"),
        "ritual": ("Q2293308", "ritual"),
        "incantation": ("Q1662673", "incantation"),
        "medical": ("Q11190", "medicine"),
        "scientific": ("Q336", "science"),
        # NOTE: "lexical"/"lexical list" intentionally OMITTED — the obvious QID
        # (Q1057179) is "user guide", not the Assyriological lexical-list concept.
        # Pending a correct QID; the live-label assertion would dead-letter it.
    },
    ENTITY_TYPE_SCRIPT: {
        # Written languages / scripts attested in the corpus. The shared writing
        # system is cuneiform; individual languages each have their own item.
        # SEED CANDIDATES — guarded by the live-label assertion (see header).
        "cuneiform": ("Q401", "cuneiform"),  # ✓verified
        "sumerian": ("Q36790", "Sumerian language"),
        "akkadian language": ("Q35518", "Akkadian language"),
        "babylonian": ("Q35518", "Akkadian language"),
        "assyrian": ("Q35518", "Akkadian language"),
        "old babylonian akkadian": ("Q35518", "Akkadian language"),
        "eblaite": ("Q35345", "Eblaite language"),
        "elamite": ("Q33741", "Elamite language"),
        "hittite": ("Q35589", "Hittite language"),
        "hurrian": ("Q33384", "Hurrian language"),
        "urartian": ("Q36495", "Urartian language"),
        "old persian": ("Q35225", "Old Persian"),
        "ugaritic": ("Q36464", "Ugaritic language"),
        "aramaic": ("Q28602", "Aramaic"),
    },
}


def _label_agrees(expected: str, live: Optional[str]) -> bool:
    """True if the live Wikidata label confirms the curated expectation.

    Case-insensitive; tolerant of minor wrapping (one being a substring of the
    other) so 'Early Dynastic Period' agrees with 'Early Dynastic period'. A
    None/empty live label (item missing or enrichment failed) does NOT agree —
    we refuse to write a link we could not confirm.
    """
    if not live:
        return False
    e = _norm(expected)
    live_norm = _norm(live)
    return e == live_norm or e in live_norm or live_norm in e


# ── HTTP fetch (curl, throttled) ──────────────────────────────────────────────

_lock = threading.Lock()
_next_allowed_at: float = 0.0


def _throttle(interval_s: float) -> None:
    """Block until the process-wide 'next allowed' timestamp."""
    global _next_allowed_at
    with _lock:
        now = time.monotonic()
        if now < _next_allowed_at:
            time.sleep(_next_allowed_at - now)
            now = time.monotonic()
        _next_allowed_at = now + interval_s


class _FetchError(Exception):
    """curl-level failure (network/timeout/no response). Retryable upstream."""


def _curl_sparql(
    query: str, *, user_agent: str, timeout_s: float = 60.0
) -> tuple[int, bytes]:
    """POST a SPARQL query to WDQS, returning (http_status, body).

    Uses POST (not GET) so a large VALUES clause never bumps into URL-length
    limits. Returns the body even on 4xx/5xx so the caller decides retry vs
    dead-letter. Raises _FetchError only on curl-level failures.
    """
    sep = "\x1e"  # ASCII record separator — won't appear in JSON results
    write_out = f"{sep}__META__{sep}%{{http_code}}"
    cmd = [
        "curl",
        "-s",
        "-S",
        "-L",
        "-A",
        user_agent,
        "-H",
        "Accept: application/sparql-results+json",
        "--data-urlencode",
        f"query={query}",
        "--max-time",
        str(int(timeout_s)),
        "-w",
        write_out,
        WDQS_ENDPOINT,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, check=False)
    except FileNotFoundError as e:  # pragma: no cover - curl always present on VPS
        raise _FetchError(f"curl not on PATH: {e}") from e

    if result.returncode != 0:
        raise _FetchError(
            f"curl exited {result.returncode}: "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )

    stdout = result.stdout
    marker = f"{sep}__META__{sep}".encode()
    idx = stdout.rfind(marker)
    if idx < 0:
        raise _FetchError("curl output missing metadata trailer")
    body = stdout[:idx]
    status = int(stdout[idx + len(marker) :].decode("utf-8", errors="replace") or "0")
    return status, body


def _backoff(attempt: int) -> None:
    time.sleep(min(BACKOFF_BASE_S * (2**attempt), BACKOFF_CAP_S))


def _run_sparql(
    query: str, *, user_agent: str, interval_s: float, ctx: RunContext
) -> Optional[dict]:
    """Run one SPARQL query with backoff on 429/5xx/timeout.

    Returns the parsed JSON dict, or None if the query could not be completed
    after retries (caller dead-letters the affected chunk).
    """
    for attempt in range(MAX_RETRIES + 1):
        _throttle(interval_s)
        try:
            status, body = _curl_sparql(query, user_agent=user_agent)
        except _FetchError as e:
            if attempt < MAX_RETRIES:
                _backoff(attempt)
                continue
            ctx.warn("wikidata.fetch_error", error=str(e))
            return None

        if status == 200:
            try:
                return json.loads(body)
            except (json.JSONDecodeError, ValueError) as e:
                ctx.warn("wikidata.bad_json", error=str(e))
                return None
        if status == 429 or 500 <= status < 600:
            if attempt < MAX_RETRIES:
                ctx.info("wikidata.retry", status=status, attempt=attempt + 1)
                _backoff(attempt)
                continue
            ctx.warn("wikidata.exhausted", status=status)
            return None
        # Other 4xx (e.g. 400 malformed query) — retrying won't help.
        ctx.warn(
            "wikidata.http_error",
            status=status,
            body=body[:300].decode("utf-8", errors="replace"),
        )
        return None
    return None


# ── SPARQL ────────────────────────────────────────────────────────────────────


def _build_pleiades_query(pleiades_ids: list[str]) -> str:
    """One SPARQL query: map each given Pleiades ID to its Wikidata item + label.

    Pleiades IDs are stored on Wikidata as plain strings under P1584, so we feed
    the VALUES list as quoted literals. The optional label service gives a human
    name for eyeballing/display.
    """
    values = " ".join(f'"{pid}"' for pid in pleiades_ids)
    return (
        "SELECT ?pleiades ?item ?itemLabel WHERE { "
        f"VALUES ?pleiades {{ {values} }} "
        f"?item wdt:{PLEIADES_PROPERTY} ?pleiades. "
        'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } '
        "}"
    )


def _parse_pleiades_results(payload: dict) -> dict[str, list[dict]]:
    """Group SPARQL bindings by pleiades_id → list of {qid, label}.

    A pleiades_id mapping to >1 qid is an ambiguity the caller must reject.
    """
    out: dict[str, list[dict]] = {}
    for b in payload.get("results", {}).get("bindings", []) or []:
        pid = (b.get("pleiades") or {}).get("value")
        item_uri = (b.get("item") or {}).get("value")
        if not pid or not item_uri:
            continue
        qid = item_uri.rsplit("/", 1)[-1]
        if not qid.startswith("Q"):
            continue
        label = (b.get("itemLabel") or {}).get("value")
        # Deduplicate identical (qid) repeats that the label service can emit.
        bucket = out.setdefault(pid, [])
        if not any(m["qid"] == qid for m in bucket):
            bucket.append({"qid": qid, "label": label})
    return out


def _build_enrich_query(qids: list[str]) -> str:
    """One SPARQL query: fetch the current label + description for given QIDs.

    Used for #533 curated links — the QID is already chosen by editorial curation;
    this only fetches a fresh human label/description for display and confirms the
    item still exists. A QID absent from the result is reported (the item may have
    been merged/deleted on Wikidata) but the curated link is still written using
    the stored fallback label, because curation — not Wikidata's live state — is
    the source of trust.
    """
    values = " ".join(f"wd:{q}" for q in qids)
    return (
        "SELECT ?item ?itemLabel ?itemDescription WHERE { "
        f"VALUES ?item {{ {values} }} "
        'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } '
        "}"
    )


def _parse_enrich_results(payload: dict) -> dict[str, dict[str, Optional[str]]]:
    """Map QID → {label, description} from an enrichment query payload."""
    out: dict[str, dict[str, Optional[str]]] = {}
    for b in payload.get("results", {}).get("bindings", []) or []:
        item_uri = (b.get("item") or {}).get("value")
        if not item_uri:
            continue
        qid = item_uri.rsplit("/", 1)[-1]
        if not qid.startswith("Q"):
            continue
        out[qid] = {
            "label": (b.get("itemLabel") or {}).get("value"),
            "description": (b.get("itemDescription") or {}).get("value"),
        }
    return out


def _chunked(items: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


# ── Connector ─────────────────────────────────────────────────────────────────


class WikidataEntitiesConnector(SourceConnector):
    id = "wikidata-entities"
    display_name = "Wikidata Entity Links (places, periods, genres, scripts)"
    description = (
        "Links Glintstone entities to their Wikidata item. Places are matched "
        "EXACTLY via provenience Pleiades ID (property P1584, in bulk). Periods, "
        "genres, and scripts are matched via a curated, human-verified name→QID "
        "dictionary and enriched with a fresh Wikidata label/description. Stores "
        "only confident matches — never name-fuzzy guesses (accuracy over coverage)."
    )
    kind = "derived"
    runs_after = ["lookup-tables"]
    upstream_url = "https://query.wikidata.org/"
    license = "CC0-1.0"
    license_url = "https://creativecommons.org/publicdomain/zero/1.0/"
    citation = "Wikidata (https://www.wikidata.org/), CC0 1.0"
    contact_email = "eric.wittke@gmail.com"

    def __init__(
        self,
        *,
        request_interval_s: float = DEFAULT_REQUEST_INTERVAL_S,
        user_agent: str = DEFAULT_USER_AGENT,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        limit: Optional[int] = None,
        pleiades_ids: Optional[list[str]] = None,
    ) -> None:
        # `limit` caps how many distinct pleiades_ids are processed (subset runs);
        # `pleiades_ids` restricts to an explicit allow-list (targeted testing).
        self.request_interval_s = request_interval_s
        self.user_agent = user_agent
        self.chunk_size = chunk_size
        self.limit = limit
        self.pleiades_ids = pleiades_ids

    # --- selection ---

    def _distinct_pleiades_ids(self, ctx: RunContext) -> list[str]:
        """Distinct, non-empty pleiades_ids from provenience_canon.

        Subset controls come from the constructor (programmatic use) or from
        ctx.config (framework run via run_connector, which builds the connector
        with no args). One pleiades_id may back many provenience rows — we query
        the DISTINCT set so the bulk SPARQL stays small and the link table holds
        one row per place, not one per spelling.
        """
        limit = self.limit if self.limit is not None else ctx.config.get("limit")
        allow = (
            self.pleiades_ids
            if self.pleiades_ids is not None
            else ctx.config.get("pleiades_ids")
        )

        clauses = [
            "pleiades_id IS NOT NULL",
            "length(trim(pleiades_id)) > 0",
        ]
        params: list[Any] = []
        if allow:
            clauses.append("pleiades_id = ANY(%s)")
            params.append([str(x) for x in allow])
        sql = (
            "SELECT DISTINCT pleiades_id FROM provenience_canon "
            f"WHERE {' AND '.join(clauses)} "
            "ORDER BY pleiades_id"
        )
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = ctx.db.execute(sql, tuple(params)).fetchall()
        return [str(r["pleiades_id"]).strip() for r in rows]

    # --- lifecycle ---

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        pleiades_ids = self._distinct_pleiades_ids(ctx)
        ctx.info("wikidata.pleiades_selected", count=len(pleiades_ids))
        if not pleiades_ids:
            return

        matched = 0
        ambiguous = 0
        no_match = 0

        for chunk in _chunked(pleiades_ids, self.chunk_size):
            query = _build_pleiades_query(chunk)
            payload = _run_sparql(
                query,
                user_agent=self.user_agent,
                interval_s=self.request_interval_s,
                ctx=ctx,
            )
            if payload is None:
                # Whole chunk failed after retries — dead-letter every id in it
                # so a targeted rerun can pick them up. Never guess.
                ctx.dead_letter_many(
                    [
                        {
                            "category": "no_match",
                            "subcategory": "wikidata_unavailable",
                            "source_key": pid,
                            "payload": {"pleiades_id": pid},
                            "reason": "WDQS query failed after retries (429/5xx/timeout).",
                        }
                        for pid in chunk
                    ]
                )
                continue

            grouped = _parse_pleiades_results(payload)
            for pid in chunk:
                hits = grouped.get(pid, [])
                if not hits:
                    # Not in Wikidata yet — counted, not guessed, not dead-lettered
                    # (a missing match is expected, not an error).
                    no_match += 1
                    continue
                if len(hits) > 1:
                    # Ambiguous: one Pleiades ID resolving to several Wikidata
                    # items. Storing either would risk misinformation, so reject
                    # and dead-letter for human review.
                    ambiguous += 1
                    ctx.dead_letter(
                        category="no_match",
                        subcategory="ambiguous_wikidata_match",
                        source_key=pid,
                        payload={
                            "pleiades_id": pid,
                            "candidate_qids": [h["qid"] for h in hits],
                        },
                        reason=(
                            "Pleiades ID resolves to multiple Wikidata items; "
                            "no confident single match (accuracy over coverage)."
                        ),
                    )
                    continue

                hit = hits[0]
                matched += 1
                yield {
                    "entity_type": ENTITY_TYPE_PLACE,
                    "source_key": pid,
                    "wikidata_qid": hit["qid"],
                    "match_basis": MATCH_BASIS_PLEIADES,
                    "confidence": PLEIADES_CONFIDENCE,
                    "wikidata_label": hit.get("label"),
                }

        ctx.info(
            "wikidata.resolution_summary",
            selected=len(pleiades_ids),
            matched=matched,
            ambiguous=ambiguous,
            no_match=no_match,
        )

        # #533: curated period / genre / script links.
        yield from self._extract_curated(ctx)

    # --- #533 curated entity links -------------------------------------------

    def _live_vocab(self, ctx: RunContext) -> dict[str, list[str]]:
        """Read the ACTUAL canonical vocab present in prod for each entity type.

        We link against the names the corpus really uses (not a hardcoded list),
        so the connector stays correct as the vocab evolves. Tables are read
        defensively: a missing table (older schema) yields an empty list for that
        type rather than aborting the whole run.
        """
        vocab: dict[str, list[str]] = {
            ENTITY_TYPE_PERIOD: [],
            ENTITY_TYPE_GENRE: [],
            ENTITY_TYPE_SCRIPT: [],
        }
        sources = {
            ENTITY_TYPE_GENRE: "SELECT name FROM canonical_genres WHERE name IS NOT NULL",
            ENTITY_TYPE_SCRIPT: "SELECT name FROM canonical_languages WHERE name IS NOT NULL",
            # Periods are not a canonical table; distinct attested values live on
            # lexical_lemmas.period (free text). DISTINCT keeps the set small.
            ENTITY_TYPE_PERIOD: (
                "SELECT DISTINCT period AS name FROM lexical_lemmas "
                "WHERE period IS NOT NULL AND length(trim(period)) > 0"
            ),
        }
        for etype, sql in sources.items():
            try:
                rows = ctx.db.execute(sql).fetchall()
            except Exception as e:  # noqa: BLE001 - missing/renamed table tolerated
                # rollback so the failed statement doesn't poison the transaction
                # (psycopg rollback trap — we hold no uncommitted writes here).
                ctx.db.rollback()
                ctx.warn("wikidata.vocab_unavailable", entity_type=etype, error=str(e))
                continue
            vocab[etype] = [
                str(r["name"]).strip()
                for r in rows
                if str((r["name"] if isinstance(r, dict) else r[0]) or "").strip()
            ]
        return vocab

    def _extract_curated(self, ctx: RunContext) -> Iterator[dict]:
        """Match live canonical vocab against CURATED_LINKS; enrich; yield links.

        One name → at most one curated QID. Names absent from the curated
        dictionary are COUNTED and SKIPPED (never guessed). All matched QIDs are
        enriched in a single bulk SPARQL query for a fresh label/description; if
        enrichment is unavailable (offline / 429 after retries), the curated
        fallback label is used and the link is still written — curation, not
        Wikidata's live state, is the source of trust.
        """
        vocab = self._live_vocab(ctx)

        # Collect curated hits, deduplicating by (entity_type, normalized name).
        hits: list[dict] = []
        qids: set[str] = set()
        per_type_matched: dict[str, int] = {}
        per_type_skipped: dict[str, int] = {}
        for etype, names in vocab.items():
            table = CURATED_LINKS.get(etype, {})
            seen_keys: set[str] = set()
            matched_n = 0
            skipped_n = 0
            for name in names:
                key = _norm(name)
                if key in seen_keys:
                    continue
                entry = table.get(key)
                if entry is None:
                    skipped_n += 1
                    continue
                seen_keys.add(key)
                qid, expected_label = entry
                matched_n += 1
                qids.add(qid)
                hits.append(
                    {
                        "entity_type": etype,
                        # source_key is the Glintstone-side identifier; for these
                        # name-keyed vocabularies it is the canonical name itself.
                        "source_key": name,
                        "wikidata_qid": qid,
                        "expected_label": expected_label,
                    }
                )
            per_type_matched[etype] = matched_n
            per_type_skipped[etype] = skipped_n

        ctx.info(
            "wikidata.curated_selected",
            matched=per_type_matched,
            skipped=per_type_skipped,
        )
        if not hits:
            return

        # Bulk-fetch each matched QID's LIVE label — this is the verification
        # gate, not mere decoration.
        enrichment: dict[str, dict[str, Optional[str]]] = {}
        for chunk in _chunked(sorted(qids), self.chunk_size):
            payload = _run_sparql(
                _build_enrich_query(chunk),
                user_agent=self.user_agent,
                interval_s=self.request_interval_s,
                ctx=ctx,
            )
            if payload is None:
                ctx.warn("wikidata.enrich_unavailable", qids=len(chunk))
                continue
            enrichment.update(_parse_enrich_results(payload))

        confirmed = 0
        rejected = 0
        unverified = 0
        for h in hits:
            enr = enrichment.get(h["wikidata_qid"], {})
            live_label = enr.get("label")
            expected = h["expected_label"]

            if live_label is None:
                # Could not confirm (item missing, or enrichment unavailable this
                # run). Refuse to write an unconfirmed link; a later run with WDQS
                # reachable will confirm it. Counted, not written, not guessed.
                unverified += 1
                ctx.dead_letter(
                    category="no_match",
                    subcategory="wikidata_unconfirmed",
                    source_key=f"{h['entity_type']}:{h['source_key']}",
                    payload={
                        "wikidata_qid": h["wikidata_qid"],
                        "expected_label": expected,
                    },
                    reason=(
                        "Curated QID could not be confirmed against Wikidata this "
                        "run (item missing or WDQS unavailable); link withheld."
                    ),
                )
                continue

            if not _label_agrees(expected, live_label):
                # The QID points at a DIFFERENT concept than curated — a wrong
                # hand entry. Reject and dead-letter for human correction; NEVER
                # write a misattributed link.
                rejected += 1
                ctx.dead_letter(
                    category="other",
                    subcategory="curated_label_mismatch",
                    source_key=f"{h['entity_type']}:{h['source_key']}",
                    payload={
                        "wikidata_qid": h["wikidata_qid"],
                        "expected_label": expected,
                        "live_label": live_label,
                    },
                    reason=(
                        "Curated QID resolves to a different concept than expected "
                        f"(expected '{expected}', Wikidata says '{live_label}'). "
                        "Likely wrong QID — correct CURATED_LINKS and re-run."
                    ),
                )
                continue

            confirmed += 1
            yield {
                "entity_type": h["entity_type"],
                "source_key": h["source_key"],
                "wikidata_qid": h["wikidata_qid"],
                "match_basis": MATCH_BASIS_CURATED,
                "confidence": CURATED_CONFIDENCE,
                # Store the confirmed LIVE label (source of truth at write time).
                "wikidata_label": live_label,
            }

        ctx.info(
            "wikidata.curated_summary",
            confirmed=confirmed,
            rejected_mismatch=rejected,
            unverified=unverified,
        )

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        for r in rows:
            try:
                self._load_one(ctx, r, stats)
            except Exception as e:  # noqa: BLE001 - route, don't abort the run
                ctx.db.rollback()
                ctx.dead_letter(
                    category="other",
                    subcategory="load_failed",
                    source_key=r.get("source_key"),
                    payload={
                        k: r.get(k)
                        for k in ("entity_type", "source_key", "wikidata_qid")
                    },
                    reason=f"load failed: {e}",
                )
                stats.dead_lettered += 1
        return stats

    def _load_one(self, ctx: RunContext, r: dict, stats: LoadStats) -> None:
        """Idempotently upsert one entity↔Wikidata link.

        ON CONFLICT (entity_type, source_key, match_basis) refreshes the
        Q-number/label/run on re-run (Wikidata may have changed) without creating
        a duplicate. `inserted` is derived from the xmax system column so the run
        log distinguishes new links from refreshed ones.
        """
        row = ctx.db.execute(
            """
            INSERT INTO entity_wikidata_links
                (entity_type, source_key, wikidata_qid, match_basis,
                 confidence, wikidata_label, run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (entity_type, source_key, match_basis) DO UPDATE SET
                wikidata_qid   = EXCLUDED.wikidata_qid,
                confidence     = EXCLUDED.confidence,
                wikidata_label = EXCLUDED.wikidata_label,
                run_id         = EXCLUDED.run_id,
                updated_at     = now()
            RETURNING (xmax = 0) AS inserted
            """,
            (
                r["entity_type"],
                r["source_key"],
                r["wikidata_qid"],
                r["match_basis"],
                r.get("confidence", PLEIADES_CONFIDENCE),
                r.get("wikidata_label"),
                ctx.run_id,
            ),
        ).fetchone()
        inserted = row["inserted"] if isinstance(row, dict) else row[0]
        ctx.db.commit()
        if inserted:
            stats.inserted += 1
        else:
            stats.updated += 1

    def verify(self, ctx: RunContext) -> None:
        # Every stored link must point at a pleiades_id that actually exists in
        # provenience_canon (no orphan links), and the qid must be well-formed.
        # The CHECK constraint already enforces qid format at write time; this is
        # a defensive cross-table integrity spot-check.
        row = ctx.db.execute(
            """
            SELECT COUNT(*) AS n
            FROM entity_wikidata_links l
            WHERE l.match_basis = %s
              AND NOT EXISTS (
                  SELECT 1 FROM provenience_canon p
                  WHERE p.pleiades_id = l.source_key
              )
            """,
            (MATCH_BASIS_PLEIADES,),
        ).fetchone()
        orphans = row["n"] if isinstance(row, dict) else row[0]
        if orphans:
            raise AssertionError(
                f"{orphans} pleiades wikidata links reference an unknown pleiades_id"
            )
