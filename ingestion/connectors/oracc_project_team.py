"""ORACC project-team scholar source (#1612).

The existing ORACC-credits path (``oracc_credits.py`` + ``core/credits_parser.py``)
is exhausted: it parses the per-*text* ``credits`` prose field in each ORACC
``catalogue.json``, but that field only cites the small, repeated set of
project directors / lemmatizers who worked on a given edition — not a
project's full contributor roster.

DATA-AVAILABILITY VERDICT (re-verified live, 2026-09, against real ORACC HTTP
responses before building — mirrors the wikidata_entities.py audit style):

  Most ORACC projects publish an "About the Project" page (linked from the
  project homepage, URL slug varies: ``AbouttheProject``, ``About``,
  ``AboutDCCLT``, ``AboutOBMC``, ...). That page is internally organized into
  named sections, each introduced by ``<a id="h_...">...<h2|h3>Heading</h2|h3>``
  markup. Some sections carry a personal-name roster — "Project Team",
  "Contributors", "<X> Editorial Board", "<X> Team (Authors)", etc. — as a list
  of ``<li>``/``<p>`` entries, one person per entry, usually (not always)
  wrapped in an ``<a href="...">Name</a>`` linking to the scholar's own page.

  IMPORTANT CORRECTION to the pre-crash research note this connector was
  scoped from: there is NOT one universal ``h_projectteam`` anchor with a
  single markup dialect. Live sampling of 48 top-level ORACC projects found:
    - only 13/48 project homepages link an About page whose "Project Team"
      *anchor* is directly non-empty;
    - several projects (ario, oimea, riao, ribo, suhu) render an EMPTY
      "Project Team" heading and put the real roster in the NEXT section
      under a project-specific heading ("OIMEA Editorial Board", "RIBo
      Contributors", ...);
    - roughly half the sampled projects (aemw, akklove, balt, blms, cams,
      ckst, cmawro, ctij, edlex, etcsl, etcsri, glass, iraq, lacost, obta,
      rimanum, rime, tcma, urap, and others) have no discoverable About-page
      link from their homepage at all within this connector's scope.

  Given that, this connector does NOT special-case a single anchor id.
  Instead it walks EVERY ``<a id="h_...">`` section on a project's About page
  and treats any section whose HEADING TEXT matches a roster-shaped keyword
  (team / board / editor / staff / personnel / contributors / advisors /
  collaborators) — excluding administrative headings (sponsors, objectives,
  funding, etc.) — as a personal-name roster, then extracts one entry per
  ``<li>``/``<p>`` in that section. This is more general (and more honest
  about real ORACC markup) than the single-anchor design and is what
  actually recovers the roster on ario/oimea/riao/ribo/suhu/ecut-style pages.

  A conservative name-plausibility gate (title-cased 2-6 word span, no digits,
  no institution keywords, no sentence stopwords) rejects image-caption prose
  ("From left to right, ...") and lead-in sentences ("The core LMU Munich
  ... team presently comprises:") that live in the same section, at the cost
  of occasionally dropping a genuine but oddly-formatted entry — acceptable
  under CLAUDE.md's accuracy-over-coverage mandate.

Wikidata was investigated as an alternative scholar source and is a dead end:
no ORACC-identifier property exists on Wikidata, SAA/SAAS/RINAP series aren't
modeled there, and name-only matching is ambiguous ("Andreas Fuchs" resolves
to 20+ distinct Wikidata items). Not built here.

Scholar linking / creation:
  Each roster entry is matched against ``scholars.normalized_name`` using the
  SAME ``core.credits_parser.normalize_name`` surname_initials key the credits
  pipeline already relies on, restricted to GLOBALLY UNIQUE keys (an ambiguous
  existing match is refused, never guessed — mirrors ``oracc_credits.py``).
  A name with no existing match is a genuinely new scholar: the connector
  inserts one, keyed by an idempotent ``NOT EXISTS`` check on
  ``normalized_name`` (CLAUDE.md's psycopg-rollback-trap rule: ``NOT EXISTS``,
  not try/except UniqueViolation — ``scholars.name`` itself has no unique
  index to ON-CONFLICT against, a pre-existing gap outside this connector's
  file ownership).

Good-citizen HTTP policy (mirrors wikidata_entities.py):
  - one request per (project homepage, About page) pair — no per-text fan-out
  - throttled with a polite floor between requests
  - descriptive User-Agent with contact, per Wikimedia-style politeness norms
  - bounded exponential backoff on 429/5xx/timeout; a project that fails after
    retries is skipped (counted), never guessed
  - shells out to curl (macOS SSL workaround, CLAUDE.md)
"""

from __future__ import annotations

import re
import subprocess
import threading
import time
from collections.abc import Iterable, Iterator
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

from core.credits_parser import normalize_name
from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_ORIGIN = "https://oracc.museum.upenn.edu"

# Top-level ORACC project slugs. Subprojects (e.g. "saao/saa01", "rinap/rinap1")
# deliberately excluded here: their "About the Project" roster lives on the
# PARENT project's page (verified live: rinap/rinap1's homepage carries no
# About link of its own), so per-subproject fetches would just re-request the
# same page or 404. Kept as a plain list (not imported from oracc_credits.py)
# so this connector has no import-time coupling to another connector's file.
ORACC_TOP_PROJECTS = [
    "adsd", "aemw", "akklove", "amgg", "ario", "armep", "asbp", "atae",
    "babcity", "balt", "blms", "borsippa", "btmao", "btto", "cams", "ckst",
    "cmawro", "ctij", "dcclt", "dccmt", "dsst", "ecut", "edlex", "eisl",
    "epsd2", "etcsl", "etcsri", "glass", "hbtin", "iraq", "lacost", "nere",
    "nimrud", "obel", "obmc", "obta", "oimea", "pnao", "riao", "ribo",
    "rimanum", "rime", "rinap", "saao", "suhu", "tcma", "tsae", "urap",
]

DEFAULT_REQUEST_INTERVAL_S = 1.0
DEFAULT_USER_AGENT = (
    "Glintstone/0.1 (Assyriology scholar-team research; "
    "+https://app.glintstone.org; contact eric.wittke@gmail.com)"
)
MAX_RETRIES = 3
BACKOFF_BASE_S = 2.0
BACKOFF_CAP_S = 30.0
REQUEST_TIMEOUT_S = 25.0

ROLE_LABEL_MAX_LEN = 200


# ── HTTP fetch (curl, throttled) ──────────────────────────────────────────

_lock = threading.Lock()
_next_allowed_at: float = 0.0


def _throttle(interval_s: float) -> None:
    global _next_allowed_at
    with _lock:
        now = time.monotonic()
        if now < _next_allowed_at:
            time.sleep(_next_allowed_at - now)
            now = time.monotonic()
        _next_allowed_at = now + interval_s


class _FetchError(Exception):
    """curl-level failure (network/timeout/no response). Retryable upstream."""


def _curl_get(url: str, *, user_agent: str, timeout_s: float) -> tuple[int, str]:
    sep = "\x1e"
    write_out = f"{sep}__META__{sep}%{{http_code}}"
    cmd = [
        "curl", "-s", "-S", "-L",
        "-A", user_agent,
        "--max-time", str(int(timeout_s)),
        "-w", write_out,
        url,
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
    body = stdout[:idx].decode("utf-8", errors="replace")
    status = int(stdout[idx + len(marker):].decode("utf-8", errors="replace") or "0")
    return status, body


def _backoff(attempt: int) -> None:
    time.sleep(min(BACKOFF_BASE_S * (2**attempt), BACKOFF_CAP_S))


def _fetch(
    url: str, *, user_agent: str, interval_s: float, ctx: RunContext
) -> str | None:
    """GET one URL with throttling + bounded backoff. None on final failure."""
    for attempt in range(MAX_RETRIES + 1):
        _throttle(interval_s)
        try:
            status, body = _curl_get(
                url, user_agent=user_agent, timeout_s=REQUEST_TIMEOUT_S
            )
        except _FetchError as e:
            if attempt < MAX_RETRIES:
                _backoff(attempt)
                continue
            ctx.warn("oracc_project_team.fetch_error", url=url, error=str(e))
            return None
        if status == 200:
            return body
        if status == 404:
            return None
        if status == 429 or 500 <= status < 600:
            if attempt < MAX_RETRIES:
                _backoff(attempt)
                continue
            ctx.warn("oracc_project_team.exhausted", url=url, status=status)
            return None
        ctx.warn("oracc_project_team.http_error", url=url, status=status)
        return None
    return None


# ── About-page discovery ────────────────────────────────────────────────


class _LinkScraper(HTMLParser):
    """Collects every href on a page, in document order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def _find_about_candidates(home_html: str, base_url: str) -> list[str]:
    scraper = _LinkScraper()
    scraper.feed(home_html)
    cands = [h for h in scraper.hrefs if "about" in h.lower()]
    # Absolute-ize relative hrefs against the project homepage.
    return [urljoin(base_url, h) for h in cands]


# ── About-page section parsing ──────────────────────────────────────────

ROSTER_HEADING_RE = re.compile(
    r"\b(team|board|editor|staff|personnel|contributors?|advisors?|collaborators?)\b",
    re.IGNORECASE,
)
EXCLUDE_HEADING_RE = re.compile(
    r"\b(sponsors?|objectives?|duration|scope|funding|acknowledg|dissemination|"
    r"citing|abbreviations|downloads?|privacy|cookies)\b",
    re.IGNORECASE,
)
_PARTICLES = {
    "von", "van", "de", "der", "den", "del", "della", "di", "da", "du",
    "le", "la", "el", "al", "bin", "ibn", "ter", "ten", "abdul", "abdulillah",
}
_INSTITUTION_HINTS = re.compile(
    r"\b(project|university|institute|museum|college|programme|program|"
    r"foundation|corpus|board|team|committee|initiative|department|"
    r"database|archive|library|consortium|network|association|society|"
    r"trust|volunteers|section|portal)\b",
    re.IGNORECASE,
)
_SENTENCE_STOPWORDS = {
    "the", "core", "comprises", "presently", "from", "to", "left", "right",
    "and", "based", "at", "is", "was", "are", "for", "with", "in", "of",
}


class _AboutPageParser(HTMLParser):
    """Splits an ORACC About-page into ``<a id="h_...">``-delimited sections
    and captures the top-level ``<li>``/``<p>`` entries within each section
    (text + first-anchor href/text), so the caller can filter by heading and
    extract names without depending on a single markup dialect.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: list[dict[str, Any]] = []
        self._pending_anchor = False
        self._in_heading = False
        self._heading_buf: list[str] = []
        self._current_section: dict[str, Any] | None = None
        self._entry_tag: str | None = None
        self._entry_depth = 0
        self._entry_text: list[str] = []
        self._entry_href: str | None = None
        self._entry_first_a_text: list[str] = []
        self._capturing_a_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag == "a" and (attrs_d.get("id") or "").startswith("h_"):
            self._pending_anchor = True
            return
        if tag in ("h2", "h3", "h4") and self._pending_anchor:
            self._in_heading = True
            self._heading_buf = []
            self._pending_anchor = False
            return
        if self._entry_tag is not None:
            if tag == self._entry_tag:
                self._entry_depth += 1
            if tag == "a" and self._entry_href is None:
                self._entry_href = attrs_d.get("href")
                self._capturing_a_text = True
            return
        if tag in ("li", "p") and self._current_section is not None:
            self._entry_tag = tag
            self._entry_depth = 1
            self._entry_text = []
            self._entry_href = None
            self._entry_first_a_text = []
            self._capturing_a_text = False

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h2", "h3", "h4") and self._in_heading:
            self._in_heading = False
            heading = re.sub(r"\s+", " ", "".join(self._heading_buf)).strip()
            self._current_section = {"heading": heading, "entries": []}
            self.sections.append(self._current_section)
            return
        if self._entry_tag is not None:
            if tag == "a":
                self._capturing_a_text = False
                return
            if tag == self._entry_tag:
                self._entry_depth -= 1
                if self._entry_depth == 0:
                    text = re.sub(r"\s+", " ", "".join(self._entry_text)).strip()
                    anchor_text = re.sub(
                        r"\s+", " ", "".join(self._entry_first_a_text)
                    ).strip()
                    if text and self._current_section is not None:
                        self._current_section["entries"].append(
                            {
                                "text": text,
                                "href": self._entry_href,
                                "anchor_text": anchor_text,
                            }
                        )
                    self._entry_tag = None
                return

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_buf.append(data)
            return
        if self._entry_tag is not None:
            self._entry_text.append(data)
            if self._capturing_a_text:
                self._entry_first_a_text.append(data)


def _clean_bracket_url(text: str) -> str:
    # Strip ORACC's "externallinktext" bracket-URL suffix ("Name [http://...]").
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", text).strip()


def _plausible_name(name: str) -> bool:
    if not name:
        return False
    words = name.split()
    if len(words) < 2 or len(words) > 6:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    if re.search(r"[.:;]", name):
        return False
    if _INSTITUTION_HINTS.search(name):
        return False
    lowered = {w.lower().strip(".,") for w in words}
    if lowered & _SENTENCE_STOPWORDS:
        return False
    for w in words:
        bare = w.strip(".,")
        if not bare:
            return False
        if bare.lower() in _PARTICLES:
            continue
        if not bare[0].isupper():
            return False
    return True


def extract_roster(html: str) -> list[dict[str, Any]]:
    """Returns [{heading, name, href}] for plausible roster entries on one
    About page. Pure function, no I/O — unit-testable in isolation.
    """
    parser = _AboutPageParser()
    parser.feed(html)
    out: list[dict[str, Any]] = []
    for section in parser.sections:
        heading = section["heading"]
        if not heading or EXCLUDE_HEADING_RE.search(heading):
            continue
        if not ROSTER_HEADING_RE.search(heading):
            continue
        for entry in section["entries"]:
            if entry["anchor_text"]:
                name = _clean_bracket_url(entry["anchor_text"])
            else:
                name = _clean_bracket_url(entry["text"])
                name = re.split(r"\s*\(", name)[0].strip()
                name = name.split(",")[0].strip()
            name = name.rstrip("†").strip()  # dagger = deceased marker
            if _plausible_name(name):
                out.append(
                    {
                        "heading": heading[:ROLE_LABEL_MAX_LEN],
                        "name": name,
                        "href": entry["href"],
                    }
                )
    return out


# ── Connector ──────────────────────────────────────────────────────────


class OraccProjectTeamConnector(SourceConnector):
    id = "oracc-project-team"
    display_name = "ORACC Project Team Pages"
    description = (
        "Scrapes ORACC 'About the Project' pages for project-team / "
        "editorial-board / contributor rosters, matching or creating "
        "scholars beyond what per-text credits prose ever names."
    )
    kind = "catalog"
    runs_after = ["scholars"]
    upstream_url = "https://oracc.museum.upenn.edu/"
    license = "CC-BY-SA-3.0"
    contact_email = "eric.wittke@gmail.com"

    def __init__(
        self,
        *,
        request_interval_s: float = DEFAULT_REQUEST_INTERVAL_S,
        user_agent: str = DEFAULT_USER_AGENT,
        projects: list[str] | None = None,
        limit: int | None = None,
    ) -> None:
        # `projects` restricts to an explicit slug allow-list (targeted
        # testing / resuming a partial run); `limit` caps how many top-level
        # projects are checked (subset runs).
        self.request_interval_s = request_interval_s
        self.user_agent = user_agent
        self.projects = projects
        self.limit = limit

    def _project_slugs(self, ctx: RunContext) -> list[str]:
        projects = self.projects if self.projects is not None else ctx.config.get(
            "projects"
        )
        limit = self.limit if self.limit is not None else ctx.config.get("limit")
        slugs = list(projects) if projects else list(ORACC_TOP_PROJECTS)
        if limit:
            slugs = slugs[: int(limit)]
        return slugs

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        slugs = self._project_slugs(ctx)
        ctx.info("oracc_project_team.projects_selected", count=len(slugs))

        no_about = 0
        no_roster = 0
        fetch_failed = 0
        rows_yielded = 0

        for slug in slugs:
            home_url = f"{ORACC_ORIGIN}/{slug}/"
            home_html = _fetch(
                home_url,
                user_agent=self.user_agent,
                interval_s=self.request_interval_s,
                ctx=ctx,
            )
            if home_html is None:
                fetch_failed += 1
                continue

            candidates = _find_about_candidates(home_html, home_url)
            roster: list[dict[str, Any]] = []
            about_url_used = ""
            for about_url in candidates[:3]:
                about_html = _fetch(
                    about_url,
                    user_agent=self.user_agent,
                    interval_s=self.request_interval_s,
                    ctx=ctx,
                )
                if about_html is None:
                    continue
                roster = extract_roster(about_html)
                if roster:
                    about_url_used = about_url
                    break

            if not candidates:
                no_about += 1
                continue
            if not roster:
                no_roster += 1
                continue

            for entry in roster:
                rows_yielded += 1
                yield {
                    "oracc_project": slug,
                    "person_name": entry["name"],
                    "role": entry["heading"],
                    "profile_url": entry["href"],
                    "source_url": about_url_used,
                }

        ctx.info(
            "oracc_project_team.discovery_summary",
            projects_checked=len(slugs),
            rows_yielded=rows_yielded,
            no_about_link=no_about,
            about_no_roster=no_roster,
            fetch_failed=fetch_failed,
        )

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        unique_index, ambiguous = self._scholar_index(ctx)
        created_this_run: dict[str, int] = {}

        for r in rows:
            self._load_one(ctx, r, stats, unique_index, ambiguous, created_this_run)
        return stats

    def _scholar_index(self, ctx: RunContext) -> tuple[dict[str, int], set[str]]:
        """normalized_name -> scholar id for GLOBALLY UNIQUE keys, plus the
        set of normalized_names that are ambiguous (>1 existing scholar) and
        must therefore be refused rather than guessed. Mirrors
        oracc_credits.OraccCreditsConnector._scholar_index.
        """
        rows = ctx.db.execute(
            "SELECT normalized_name, id FROM scholars "
            "WHERE normalized_name IS NOT NULL AND normalized_name <> ''"
        ).fetchall()

        def _v(row: object, key: str, idx: int) -> object:
            return row[key] if isinstance(row, dict) else row[idx]  # type: ignore[index]

        counts: dict[str, int] = {}
        for row in rows:
            nn = str(_v(row, "normalized_name", 0))
            counts[nn] = counts.get(nn, 0) + 1

        index: dict[str, int] = {}
        ambiguous: set[str] = set()
        for row in rows:
            nn = str(_v(row, "normalized_name", 0))
            if counts[nn] == 1:
                index[nn] = int(_v(row, "id", 1))  # type: ignore[call-overload]
            else:
                ambiguous.add(nn)
        return index, ambiguous

    def _resolve_scholar_id(
        self,
        ctx: RunContext,
        person_name: str,
        unique_index: dict[str, int],
        ambiguous: set[str],
        created_this_run: dict[str, int],
    ) -> tuple[int | None, str]:
        """Returns (scholar_id, normalized_name). scholar_id is None only
        when the name could not be parsed or is ambiguous (caller dead-letters).
        """
        nn = normalize_name(person_name)
        if not nn:
            return None, nn
        if nn in unique_index:
            return unique_index[nn], nn
        if nn in created_this_run:
            return created_this_run[nn], nn
        if nn in ambiguous:
            return None, nn

        # Genuinely new scholar. Idempotent NOT-EXISTS insert (CLAUDE.md:
        # scholars.name carries no unique index to ON CONFLICT against, so we
        # gate on normalized_name explicitly rather than relying on a
        # constraint that doesn't exist).
        row = ctx.db.execute(
            """
            INSERT INTO scholars (name, normalized_name, author_type)
            SELECT %s, %s, 'person'
            WHERE NOT EXISTS (
                SELECT 1 FROM scholars WHERE normalized_name = %s
            )
            RETURNING id
            """,
            (person_name, nn, nn),
        ).fetchone()
        ctx.db.commit()
        if row is not None:
            new_id = row["id"] if isinstance(row, dict) else row[0]
            created_this_run[nn] = int(new_id)
            return int(new_id), nn

        # Someone else (or an earlier row in this same run under a slightly
        # different raw spelling) already created it — look it up.
        row = ctx.db.execute(
            "SELECT id FROM scholars WHERE normalized_name = %s", (nn,)
        ).fetchone()
        if row is None:
            return None, nn
        existing_id = int(row["id"] if isinstance(row, dict) else row[0])
        created_this_run[nn] = existing_id
        return existing_id, nn

    def _load_one(
        self,
        ctx: RunContext,
        r: dict,
        stats: LoadStats,
        unique_index: dict[str, int],
        ambiguous: set[str],
        created_this_run: dict[str, int],
    ) -> None:
        person_name = r["person_name"]
        try:
            scholar_id, nn = self._resolve_scholar_id(
                ctx, person_name, unique_index, ambiguous, created_this_run
            )
        except Exception as e:  # noqa: BLE001 - route, don't abort the run
            ctx.db.rollback()
            ctx.dead_letter(
                category="other",
                subcategory="scholar_resolution_failed",
                source_key=person_name,
                payload=r,
                reason=f"scholar resolution failed: {e}",
            )
            stats.dead_lettered += 1
            return

        if scholar_id is None:
            reason = (
                "name did not parse into a surname + given-name form"
                if not nn
                else "normalized_name is ambiguous across >1 existing scholar; "
                "refusing to guess"
            )
            ctx.dead_letter(
                category="no_match",
                subcategory="ambiguous_or_unparseable_name",
                source_key=person_name,
                payload=r,
                reason=reason,
            )
            stats.dead_lettered += 1
            return

        try:
            row = ctx.db.execute(
                """
                INSERT INTO project_contributors
                    (oracc_project, scholar_id, person_name, role,
                     profile_url, source_url, run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (oracc_project, scholar_id, role) DO UPDATE SET
                    person_name = EXCLUDED.person_name,
                    profile_url = EXCLUDED.profile_url,
                    source_url  = EXCLUDED.source_url,
                    run_id      = EXCLUDED.run_id,
                    updated_at  = now()
                RETURNING (xmax = 0) AS inserted
                """,
                (
                    r["oracc_project"],
                    scholar_id,
                    person_name,
                    r["role"],
                    r.get("profile_url"),
                    r.get("source_url"),
                    ctx.run_id,
                ),
            ).fetchone()
            ctx.db.commit()
        except Exception as e:  # noqa: BLE001 - route, don't abort the run
            ctx.db.rollback()
            ctx.dead_letter(
                category="other",
                subcategory="load_failed",
                source_key=person_name,
                payload=r,
                reason=f"load failed: {e}",
            )
            stats.dead_lettered += 1
            return

        inserted = row["inserted"] if isinstance(row, dict) else row[0]
        if inserted:
            stats.inserted += 1
        else:
            stats.updated += 1

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM project_contributors"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        scholars_row = ctx.db.execute(
            "SELECT COUNT(DISTINCT scholar_id) AS n FROM project_contributors"
        ).fetchone()
        scholars_n = (
            scholars_row["n"] if isinstance(scholars_row, dict) else scholars_row[0]
        )
        ctx.info(
            "oracc_project_team.verify",
            rows=n,
            distinct_scholars=scholars_n,
        )
