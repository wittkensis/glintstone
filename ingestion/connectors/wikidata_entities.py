"""Wikidata entity linker — attaches Wikidata Q-numbers to Glintstone entities.

Issue #164. This connector enriches the SSOT by linking Glintstone entities to
their Wikidata item (Q-number), so search, entity profiles, and the future map
can surface external context (coordinates, sitelinks, images, "instance of").

DATA-AVAILABILITY VERDICT (audited 2026-06 against prod before building):
  The ONLY high-confidence, ID-based match path that exists today is places via
  their Pleiades ID:

      provenience_canon.pleiades_id ─(Wikidata property P1584 "Pleiades ID")→ Q

  A Pleiades ID is a stable gazetteer identifier for an ancient place; Wikidata
  stores it under property P1584. Mapping an identifier to an identifier is
  EXACT. Prod carries 151 distinct pleiades_ids; a single bulk SPARQL query
  resolves 106 of them, of which 101 are unambiguous (one Q-number) and 5 are
  ambiguous (>1 Q-number). The other 45 places are simply not in Wikidata yet.

  named_entities (deities / persons / other places) is EMPTY in prod, so there is
  nothing to match there. Even if it were populated, matching deities/people by
  NAME is ambiguous and is deliberately NOT attempted here — accuracy over
  coverage. A wrong Q-number is misinformation in a scholarly tool.

  => Scope of this connector: places via Pleiades ID, unambiguous matches only.

Connector anatomy:
  - extract()  reads the distinct pleiades_ids from provenience_canon, resolves
               them to Q-numbers in ONE bulk SPARQL query (not per-row), and
               yields one record per *unambiguously* matched pleiades_id.
               pleiades_ids that resolve to >1 Q-number are dead-lettered
               (ambiguous); pleiades_ids with no Wikidata item are silently
               omitted (counted in the run log, never guessed).
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


def _chunked(items: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


# ── Connector ─────────────────────────────────────────────────────────────────


class WikidataEntitiesConnector(SourceConnector):
    id = "wikidata-entities"
    display_name = "Wikidata Entity Links (place ↔ Q-number via Pleiades ID)"
    description = (
        "Links Glintstone places to their Wikidata item by resolving each "
        "provenience Pleiades ID through Wikidata property P1584, in bulk. "
        "Stores only unambiguous, ID-based matches (accuracy over coverage)."
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
