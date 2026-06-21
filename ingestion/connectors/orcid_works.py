"""ORCID works importer — enriches scholar publications from ORCID public records.

For every scholar in the `scholars` table that carries a non-null `orcid`, this
connector fetches that researcher's works from ORCID's public API
(``https://pub.orcid.org/v3.0/{orcid}/works``, CC0, no auth needed) and links
each work to the scholar via the existing publications + publication_authors
tables. It does NOT create the scholars; it enriches the ~421 that already have
an ORCID (sourced via the OpenAlex backfill in the scholar pipeline).

Design (connector anatomy):
  - extract()   yields one record per (scholar, work) pair, after fetching each
                scholar's works summaries over HTTP with polite rate limiting.
  - transform() identity passthrough (extract already emits target-shaped rows).
  - load()      idempotent UPSERT into publications keyed on DOI, then links the
                scholar in publication_authors (role=author). Works without a DOI
                are deduped conservatively on (normalized title, year) per scholar,
                or skipped — accuracy over coverage (scholar-attribution rule).

Good-citizen policy (the CDLI IP-ban lesson):
  - ~421 scholars ⇒ ~421 API calls. A polite delay (default ~1.1s) is enforced
    between requests via a process-wide throttle.
  - A descriptive User-Agent identifies us and gives ORCID a contact.
  - 429 / 5xx responses trigger bounded exponential backoff with retries; a
    final failure routes the scholar to the dead-letter queue rather than
    aborting the run.
  - Runs are idempotent, so a partial run resumes cleanly with no duplicates.

macOS SSL note (CLAUDE.md): we shell out to ``curl`` via subprocess. urllib /
requests have intermittent SSL failures on macOS against some HTTPS endpoints,
and curl is also what the production VPS uses — this connector is meant to run
on the VPS where it can reach external hosts.
"""

from __future__ import annotations

import json
import re
import subprocess
import threading
import time
import unicodedata
from typing import Any, Iterable, Iterator, Optional

from ingestion.base import LoadStats, RunContext, SourceConnector

ORCID_API_BASE = "https://pub.orcid.org/v3.0"

# Polite floor between ORCID requests. ORCID's public API tolerates ~24 req/s
# burst, but we deliberately stay well under 1 req/s-ish to be a good citizen
# against a free public scholarly service.
DEFAULT_REQUEST_INTERVAL_S = 1.1
DEFAULT_USER_AGENT = (
    "Glintstone/0.1 (academic publication enrichment; "
    "+https://app.glintstone.org; contact eric.wittke@gmail.com)"
)

# Bounded retry policy for 429 / 5xx.
MAX_RETRIES = 4
BACKOFF_BASE_S = 2.0
BACKOFF_CAP_S = 30.0

# ORCID work-type → our publications.publication_type enum. ORCID's vocabulary
# is broad; anything unmapped falls back to "other" so we never violate the
# enum CHECK constraint.
_TYPE_MAP = {
    "journal-article": "journal_article",
    "book": "monograph",
    "book-chapter": "chapter",
    "edited-book": "edited_volume",
    "dissertation": "dissertation",
    "dissertation-thesis": "thesis",
    "supervised-student-publication": "other",
    "conference-paper": "conference_paper",
    "conference-abstract": "conference_paper",
    "conference-poster": "conference_paper",
    "report": "report",
    "working-paper": "report",
    "preprint": "other",
    "data-set": "other",
    "research-technique": "other",
    "other": "other",
}


# ── HTTP fetch (curl, throttled) ──────────────────────────────────────────────

_lock = threading.Lock()
_next_allowed_at: float = 0.0


def _throttle(interval_s: float) -> None:
    """Block until the process-wide 'next allowed' timestamp.

    Stores an absolute next-allowed monotonic timestamp so concurrent callers
    can never shrink each other's promised wait. Single-threaded here, but the
    lock keeps it correct if the connector is ever parallelized.
    """
    global _next_allowed_at
    with _lock:
        now = time.monotonic()
        if now < _next_allowed_at:
            time.sleep(_next_allowed_at - now)
            now = time.monotonic()
        _next_allowed_at = now + interval_s


class _FetchError(Exception):
    """curl-level failure (network/timeout/no response). Retryable upstream."""


def _curl_json(
    url: str, *, user_agent: str, timeout_s: float = 30.0
) -> tuple[int, bytes]:
    """Fetch ``url`` with curl, returning (http_status, body).

    Returns the body even on 4xx/5xx so the caller decides retry vs dead-letter.
    Raises _FetchError only on curl-level failures.
    """
    sep = "\x1e"  # ASCII record separator — won't appear in ORCID JSON
    write_out = f"{sep}__META__{sep}%{{http_code}}"
    cmd = [
        "curl",
        "-s",
        "-S",
        "-L",
        "-A",
        user_agent,
        "-H",
        "Accept: application/json",
        "--max-time",
        str(int(timeout_s)),
        "-w",
        write_out,
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, check=False)
    except FileNotFoundError as e:  # pragma: no cover - curl always present on VPS
        raise _FetchError(f"curl not on PATH: {e}") from e

    if result.returncode != 0:
        raise _FetchError(
            f"curl exited {result.returncode} for {url}: "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )

    stdout = result.stdout
    marker = f"{sep}__META__{sep}".encode()
    idx = stdout.rfind(marker)
    if idx < 0:
        raise _FetchError(f"curl output missing metadata trailer for {url}")
    body = stdout[:idx]
    status = int(stdout[idx + len(marker) :].decode("utf-8", errors="replace") or "0")
    return status, body


def _fetch_works(
    orcid: str, *, user_agent: str, interval_s: float, ctx: RunContext
) -> Optional[dict]:
    """Fetch the works summary for one ORCID, with backoff on 429/5xx.

    Returns the parsed JSON dict, or None if the record is unavailable after
    retries (caller dead-letters). 404 → None immediately (no retry — the ORCID
    is wrong or the record is private/deactivated).
    """
    url = f"{ORCID_API_BASE}/{orcid}/works"
    for attempt in range(MAX_RETRIES + 1):
        _throttle(interval_s)
        try:
            status, body = _curl_json(url, user_agent=user_agent)
        except _FetchError as e:
            if attempt < MAX_RETRIES:
                _backoff(attempt)
                continue
            ctx.warn("orcid.fetch_error", orcid=orcid, error=str(e))
            return None

        if status == 200:
            try:
                return json.loads(body)
            except (json.JSONDecodeError, ValueError) as e:
                ctx.warn("orcid.bad_json", orcid=orcid, error=str(e))
                return None
        if status == 404:
            ctx.info("orcid.not_found", orcid=orcid)
            return None
        if status == 429 or 500 <= status < 600:
            if attempt < MAX_RETRIES:
                ctx.info("orcid.retry", orcid=orcid, status=status, attempt=attempt + 1)
                _backoff(attempt)
                continue
            ctx.warn("orcid.exhausted", orcid=orcid, status=status)
            return None
        # Other 4xx (e.g. 400 malformed orcid) — no point retrying.
        ctx.warn("orcid.http_error", orcid=orcid, status=status)
        return None
    return None


def _backoff(attempt: int) -> None:
    time.sleep(min(BACKOFF_BASE_S * (2**attempt), BACKOFF_CAP_S))


# ── Parsing ───────────────────────────────────────────────────────────────────


def _text(node: Any) -> Optional[str]:
    """ORCID wraps most scalars as {"value": ...}. Pull the value safely."""
    if isinstance(node, dict):
        v = node.get("value")
        return v.strip() if isinstance(v, str) and v.strip() else None
    if isinstance(node, str):
        return node.strip() or None
    return None


def _normalize_doi(raw: str) -> str:
    """Normalize a DOI to a bare lowercase '10.x/...' form for stable keying."""
    d = raw.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip()


def _normalize_title(raw: str) -> str:
    """Aggressive title normalization for no-DOI dedup: NFC, lowercase, strip
    punctuation, collapse whitespace. Conservative on purpose — a near-match
    collapses to the same key so we don't create near-duplicate pubs."""
    t = unicodedata.normalize("NFC", raw).lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_works(orcid: str, payload: dict) -> list[dict]:
    """Parse an ORCID /works response into normalized work records.

    Each returned dict carries: doi (normalized or None), title, year, type,
    journal, url, plus the source orcid. Works with no title are skipped
    entirely (we can neither display nor dedup them safely).
    """
    out: list[dict] = []
    for group in payload.get("group", []) or []:
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        # ORCID groups together summaries it considers the same work (matched on
        # external ids). Take the first summary as canonical for title/type/year,
        # but scan ALL summaries in the group for a DOI (different sources may
        # supply the identifier).
        primary = summaries[0]
        title = None
        title_node = (primary.get("title") or {}).get("title")
        title = _text(title_node)
        if not title:
            continue

        doi = None
        for summ in summaries:
            ext = (summ.get("external-ids") or {}).get("external-id") or []
            for eid in ext:
                if (eid.get("external-id-type") or "").lower() == "doi":
                    val = _text(eid.get("external-id-value")) or eid.get(
                        "external-id-value"
                    )
                    if isinstance(val, str) and val.strip():
                        doi = _normalize_doi(val)
                        break
            if doi:
                break

        year = None
        pub_date = primary.get("publication-date") or {}
        y = _text((pub_date.get("year") or {})) if pub_date else None
        if y and y.isdigit():
            year = int(y)

        work_type = (primary.get("type") or "other").lower()
        pub_type = _TYPE_MAP.get(work_type, "other")

        journal = _text(primary.get("journal-title"))
        url = _text(primary.get("url"))

        out.append(
            {
                "orcid": orcid,
                "doi": doi or None,
                "title": title,
                "year": year,
                "publication_type": pub_type,
                "journal": journal,
                "url": url,
            }
        )
    return out


# ── Connector ─────────────────────────────────────────────────────────────────


class OrcidWorksConnector(SourceConnector):
    id = "orcid-works"
    display_name = "ORCID Works (scholar publication enrichment)"
    description = (
        "Pulls each ORCID-bearing scholar's works from ORCID's public API and "
        "links them as publications (idempotent, DOI-keyed)."
    )
    kind = "catalog"
    runs_after = ["scholars"]
    upstream_url = "https://pub.orcid.org/"
    license = "CC0-1.0"
    license_url = "https://creativecommons.org/publicdomain/zero/1.0/"
    citation = "ORCID public API (https://info.orcid.org/)"
    contact_email = "eric.wittke@gmail.com"

    def __init__(
        self,
        *,
        request_interval_s: float = DEFAULT_REQUEST_INTERVAL_S,
        user_agent: str = DEFAULT_USER_AGENT,
        limit: Optional[int] = None,
        orcids: Optional[list[str]] = None,
    ) -> None:
        # `limit` caps how many scholars are processed (subset runs); `orcids`
        # restricts to an explicit allow-list (targeted reruns / testing).
        self.request_interval_s = request_interval_s
        self.user_agent = user_agent
        self.limit = limit
        self.orcids = orcids

    # --- scholar selection ---

    def _scholars_with_orcid(self, ctx: RunContext) -> list[dict]:
        clauses = ["orcid IS NOT NULL", "trim(orcid) <> ''"]
        params: list[Any] = []
        if self.orcids:
            clauses.append("orcid = ANY(%s)")
            params.append(self.orcids)
        sql = (
            "SELECT id, name, orcid FROM scholars "
            f"WHERE {' AND '.join(clauses)} "
            "ORDER BY id"
        )
        if self.limit:
            sql += f" LIMIT {int(self.limit)}"
        rows = ctx.db.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    # --- lifecycle ---

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        scholars = self._scholars_with_orcid(ctx)
        ctx.info("orcid.scholars_selected", count=len(scholars))
        for sch in scholars:
            orcid = sch["orcid"].strip()
            payload = _fetch_works(
                orcid,
                user_agent=self.user_agent,
                interval_s=self.request_interval_s,
                ctx=ctx,
            )
            if payload is None:
                ctx.dead_letter(
                    category="no_match",
                    subcategory="orcid_unavailable",
                    source_key=orcid,
                    payload={"scholar_id": sch["id"], "orcid": orcid},
                    reason="ORCID works record unavailable after retries (404/429/5xx/parse).",
                )
                continue
            works = parse_works(orcid, payload)
            ctx.info(
                "orcid.fetched", orcid=orcid, scholar_id=sch["id"], works=len(works)
            )
            for w in works:
                w["scholar_id"] = sch["id"]
                w["scholar_name"] = sch["name"]
                yield w

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        for w in rows:
            try:
                self._load_one(ctx, w, stats)
            except Exception as e:  # noqa: BLE001 - route, don't abort the run
                # Roll back only this row's partial work, then dead-letter it.
                ctx.db.rollback()
                ctx.dead_letter(
                    category="other",
                    subcategory="load_failed",
                    source_key=w.get("doi") or w.get("title"),
                    payload={
                        k: w.get(k) for k in ("scholar_id", "doi", "title", "year")
                    },
                    reason=f"load failed: {e}",
                )
                stats.dead_lettered += 1
        return stats

    def _load_one(self, ctx: RunContext, w: dict, stats: LoadStats) -> None:
        """Idempotently upsert one work and link the scholar.

        Resolution order for the publication id:
          1. DOI present → ON CONFLICT (doi) upsert, returns the canonical id.
          2. No DOI → conservative match on (normalized title, year) restricted
             to publications already linked to THIS scholar. If none, insert a
             new pub keyed by a deterministic orcid bibtex_key so reruns don't
             duplicate. If the title is empty we skip (shouldn't happen — parse
             drops titleless works).
        """
        scholar_id = w["scholar_id"]
        title = w["title"]
        year = w.get("year")
        doi = w.get("doi")

        if doi:
            pub_id, inserted = self._upsert_by_doi(ctx, w)
        else:
            pub_id, inserted = self._upsert_no_doi(ctx, w, scholar_id, title, year)

        if pub_id is None:
            stats.skipped += 1
            return
        if inserted:
            stats.inserted += 1
        else:
            stats.skipped += 1  # existing pub, no new pub row created

        self._link_author(ctx, pub_id, scholar_id)
        ctx.db.commit()

    def _upsert_by_doi(self, ctx: RunContext, w: dict) -> tuple[Optional[int], bool]:
        """ON CONFLICT (doi) upsert. Existing rows are left untouched (we do not
        overwrite richer CDLI/OpenAlex metadata with ORCID summaries — accuracy
        over coverage). Returns (publication_id, was_inserted)."""
        bibtex_key = f"orcid:{w['doi']}"
        row = ctx.db.execute(
            """
            INSERT INTO publications
                (doi, bibtex_key, title, publication_type, year, url, authors)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (doi) DO UPDATE SET doi = EXCLUDED.doi
            RETURNING id, (xmax = 0) AS inserted
            """,
            (
                w["doi"],
                bibtex_key,
                w["title"],
                w["publication_type"],
                w.get("year"),
                w.get("url"),
                w.get("scholar_name") or "",
            ),
        ).fetchone()
        pub_id = row["id"] if isinstance(row, dict) else row[0]
        inserted = row["inserted"] if isinstance(row, dict) else row[1]
        return pub_id, bool(inserted)

    def _upsert_no_doi(
        self,
        ctx: RunContext,
        w: dict,
        scholar_id: int,
        title: str,
        year: Optional[int],
    ) -> tuple[Optional[int], bool]:
        """No DOI → conservative dedup. Match an EXISTING publication this
        scholar is already linked to whose normalized title (and year, when both
        sides have one) coincide. If found, reuse it (no insert). Otherwise
        insert a new pub with a deterministic orcid bibtex_key so a rerun finds
        the same row via ON CONFLICT (bibtex_key)."""
        norm = _normalize_title(title)
        if not norm:
            return None, False

        # Look only among pubs already attributed to this scholar — narrow, so
        # we never collide two different scholars' same-titled works, and never
        # grab an unrelated corpus pub. accuracy over coverage.
        candidates = ctx.db.execute(
            """
            SELECT p.id, p.title, p.year
            FROM publications p
            JOIN publication_authors pa ON pa.publication_id = p.id
            WHERE pa.scholar_id = %s
            """,
            (scholar_id,),
        ).fetchall()
        for c in candidates:
            c = dict(c)
            if _normalize_title(c["title"] or "") != norm:
                continue
            # If both carry a year and they disagree, treat as a different work.
            if year is not None and c["year"] is not None and c["year"] != year:
                continue
            return c["id"], False

        # Deterministic key so reruns are idempotent even without a DOI.
        digest = _normalize_title(title)[:120].replace(" ", "_")
        bibtex_key = f"orcid:{scholar_id}:{year or 'na'}:{digest}"
        row = ctx.db.execute(
            """
            INSERT INTO publications
                (bibtex_key, title, publication_type, year, url, authors)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (bibtex_key) DO UPDATE SET bibtex_key = EXCLUDED.bibtex_key
            RETURNING id, (xmax = 0) AS inserted
            """,
            (
                bibtex_key,
                title,
                w["publication_type"],
                year,
                w.get("url"),
                w.get("scholar_name") or "",
            ),
        ).fetchone()
        pub_id = row["id"] if isinstance(row, dict) else row[0]
        inserted = row["inserted"] if isinstance(row, dict) else row[1]
        return pub_id, bool(inserted)

    def _link_author(self, ctx: RunContext, pub_id: int, scholar_id: int) -> None:
        """Link scholar↔publication as author. ON CONFLICT on the existing
        (publication_id, scholar_id, role) unique constraint → idempotent."""
        ctx.db.execute(
            """
            INSERT INTO publication_authors (publication_id, scholar_id, role)
            VALUES (%s, %s, 'author')
            ON CONFLICT (publication_id, scholar_id, role) DO NOTHING
            """,
            (pub_id, scholar_id),
        )

    def verify(self, ctx: RunContext) -> None:
        # Sanity: every ORCID-sourced publication must be linked to at least one
        # scholar (no orphan pubs created by this connector).
        row = ctx.db.execute(
            """
            SELECT COUNT(*) AS n
            FROM publications p
            WHERE p.bibtex_key LIKE 'orcid:%%'
              AND NOT EXISTS (
                  SELECT 1 FROM publication_authors pa
                  WHERE pa.publication_id = p.id
              )
            """
        ).fetchone()
        orphans = row["n"] if isinstance(row, dict) else row[0]
        if orphans:
            raise AssertionError(
                f"{orphans} ORCID-sourced publications have no author link"
            )
