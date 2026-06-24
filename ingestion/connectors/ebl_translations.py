"""eBL English-translation connector — pull literary translations from eBL.

Issue #165. The electronic Babylonian Library (eBL, LMU Munich) carries modern,
line-by-line English translations of Babylonian/Assyrian literary compositions
(Enūma eliš, Atraḫasīs, the Catalogue of Texts and Authors, …). No connector
pulled them; this adds English-translation coverage for the literary corpus.

DATA-AVAILABILITY VERDICT (audited 2026-06 against the LIVE eBL API):
  The eBL *read* API is publicly reachable WITHOUT authentication (the Auth0
  requirement noted in gs-expert-integrations/sources.md is for the web UI and
  for write/private scopes, not for reading the published corpus). Verified:
    GET /api/texts                          → 200, the text catalogue.
    GET /api/texts/L/1/2                     → 200, a text + its chapters.
    GET /api/texts/L/1/2/chapters/<stage>/<name> → 200, the chapter's lines,
        each with a `translation` string like
          "#tr.en: When on high no word was used for heaven,\n#tr.ar: …"
  So we walk: catalogue → each text → each chapter → each line, and extract the
  `#tr.en:` segment. Lines with no English translation are skipped (counted).

  MAPPING TO OUR ARTIFACTS — the honest answer (data-gate caveat):
  eBL corpus translations are COMPOSITE-text translations (a reconstructed
  literary line attested across many manuscripts), NOT per-CDLI-tablet
  (p_number) translations. eBL manuscripts expose museum numbers, not CDLI
  p_numbers, in the corpus payload. We therefore store the eBL identity
  faithfully (text + chapter + line) in `ebl_translations` rather than inventing
  a p_number attribution. Linking an eBL text to a Glintstone `composite` /
  artifact is a separate, evidence-based step (out of scope here; a wrong link
  is bad scholarly data).

GOOD-CITIZEN POLICY (the CDLI IP-ban lesson):
  * One HTTP request per text and one per chapter, throttled (a polite floor
    between calls), with bounded exponential backoff + Retry-After on 429/5xx.
  * A descriptive User-Agent with a contact.
  * Idempotent (ON CONFLICT) so a partial run resumes cleanly.
  * A chapter that fails after retries is dead-lettered (never aborts the run).

macOS SSL note (CLAUDE.md): all fetches shell out to curl via subprocess.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
import urllib.parse
from typing import Any, Iterable, Iterator, Optional

from ingestion.base import LoadStats, RunContext, SourceConnector, SourceManifest

EBL_API_BASE = "https://www.ebl.lmu.de/api"

DEFAULT_USER_AGENT = (
    "Glintstone/0.1 (Assyriology literary-translation ingest; "
    "+https://app.glintstone.org; contact eric.wittke@gmail.com)"
)

# Polite floor between eBL requests (seconds). The corpus is a few hundred
# chapters, so this keeps the whole run well within courteous bounds.
DEFAULT_REQUEST_INTERVAL_S = 1.0

MAX_RETRIES = 4
BACKOFF_BASE_S = 2.0
BACKOFF_CAP_S = 60.0


# --- throttled fetch (curl) ------------------------------------------------

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
    """curl-level failure (network/timeout). Retryable."""


def _curl_json(
    url: str, *, user_agent: str, timeout_s: float = 90.0
) -> tuple[int, bytes]:
    """GET a URL, returning (http_status, body). Body returned even on 4xx/5xx."""
    sep = "\x1e"
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
    except FileNotFoundError as e:  # pragma: no cover
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


def _fetch_json(
    url: str, *, user_agent: str, interval_s: float, ctx: RunContext
) -> Optional[Any]:
    """Fetch + parse JSON with backoff on 429/5xx/timeout. None on final failure."""
    for attempt in range(MAX_RETRIES + 1):
        _throttle(interval_s)
        try:
            status, body = _curl_json(url, user_agent=user_agent)
        except _FetchError as e:
            if attempt < MAX_RETRIES:
                _backoff(attempt)
                continue
            ctx.warn("ebl.fetch_error", url=url, error=str(e))
            return None
        if status == 200:
            try:
                return json.loads(body)
            except (json.JSONDecodeError, ValueError) as e:
                ctx.warn("ebl.bad_json", url=url, error=str(e))
                return None
        if status == 429 or 500 <= status < 600:
            if attempt < MAX_RETRIES:
                ctx.info("ebl.retry", url=url, status=status, attempt=attempt + 1)
                _backoff(attempt)
                continue
            ctx.warn("ebl.exhausted", url=url, status=status)
            return None
        # Other 4xx — retrying won't help (404 chapter, etc.).
        ctx.warn("ebl.http_error", url=url, status=status)
        return None
    return None


# --- translation parsing ---------------------------------------------------


def extract_en(translation: Optional[str]) -> Optional[str]:
    """Pull the English segment from an eBL translation string.

    Format: "#tr.en: <english>\n#tr.ar: <arabic>\n…". There may be 0..n
    `#tr.<lang>:` segments; a segment may wrap across following lines until the
    next `#tr.` marker. Returns the English text, or None if absent/empty.
    """
    if not translation:
        return None
    lines = translation.split("\n")
    en_parts: list[str] = []
    capturing = False
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("#tr.en:"):
            capturing = True
            en_parts.append(stripped[len("#tr.en:") :].strip())
        elif stripped.startswith("#tr."):
            capturing = False  # a different-language segment begins
        elif capturing:
            en_parts.append(stripped)
    text = " ".join(p for p in en_parts if p).strip()
    return text or None


def _line_number_str(number: Any) -> Optional[str]:
    """eBL line `number` is sometimes a plain string ('1') and sometimes a dict
    ({'number': 1, 'hasPrime': false, ...}). Normalise to a display string."""
    if number is None:
        return None
    if isinstance(number, str):
        return number.strip() or None
    if isinstance(number, dict):
        base = number.get("number")
        if base is None:
            return None
        s = str(base)
        if number.get("hasPrime"):
            s += "'"
        for key in ("prefixModifier", "suffixModifier"):
            mod = number.get(key)
            if mod:
                s = f"{s}{mod}" if key == "suffixModifier" else f"{mod}{s}"
        return s
    return str(number)


def _reconstruction_str(line: dict) -> Optional[str]:
    """Best-effort plain reconstruction text for context (informational)."""
    variants = line.get("variants")
    if not variants:
        return None
    recon = variants[0].get("reconstruction")
    if isinstance(recon, str):
        return recon
    if isinstance(recon, list):
        # token list — join cleanValues
        parts = [
            str(t.get("value")) for t in recon if isinstance(t, dict) and t.get("value")
        ]
        return " ".join(parts) or None
    return None


# --- connector -------------------------------------------------------------


class EblTranslationsConnector(SourceConnector):
    id = "ebl-translations"
    display_name = "eBL English Translations (literary corpus)"
    description = (
        "Pulls line-level English translations of Babylonian/Assyrian literary "
        "compositions from the eBL corpus API into ebl_translations. Composite-"
        "text level (text/chapter/line), not per-CDLI-tablet. Good API citizen."
    )
    kind = "corpus"
    runs_after = ["lookup-tables"]
    upstream_url = "https://www.ebl.lmu.de/"
    license = "CC-BY-SA-4.0"
    license_url = "https://creativecommons.org/licenses/by-sa/4.0/"
    citation = "Electronic Babylonian Library (eBL), LMU Munich"
    contact_email = "eric.wittke@gmail.com"

    def __init__(
        self,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        request_interval_s: float = DEFAULT_REQUEST_INTERVAL_S,
        limit_texts: Optional[int] = None,
    ) -> None:
        self.user_agent = user_agent
        self.request_interval_s = request_interval_s
        self.limit_texts = limit_texts

    def discover(self, ctx: RunContext) -> SourceManifest:
        # Always-run: the eBL corpus is edited continuously and the connector is
        # idempotent, so we re-pull and upsert. No cheap upstream checksum.
        return SourceManifest()

    def _get(self, path: str, ctx: RunContext) -> Optional[Any]:
        return _fetch_json(
            f"{EBL_API_BASE}/{path}",
            user_agent=self.user_agent,
            interval_s=self.request_interval_s,
            ctx=ctx,
        )

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        limit = ctx.config.get("limit_texts", self.limit_texts)

        catalogue = self._get("texts", ctx)
        if not isinstance(catalogue, list):
            ctx.warn("ebl.catalogue_unavailable")
            return
        if limit:
            catalogue = catalogue[: int(limit)]
        ctx.info("ebl.texts_selected", count=len(catalogue))

        texts_done = chapters_done = lines_emitted = chapters_failed = 0

        for entry in catalogue:
            genre = entry.get("genre")
            category = entry.get("category")
            index = entry.get("index")
            text_name = entry.get("name")
            if genre is None or category is None or index is None:
                continue

            text = self._get(f"texts/{genre}/{category}/{index}", ctx)
            if not isinstance(text, dict):
                continue
            texts_done += 1
            chapters = text.get("chapters") or []

            for ch in chapters:
                stage = ch.get("stage")
                name = ch.get("name")
                if stage is None or name is None:
                    continue
                stage_q = urllib.parse.quote(str(stage), safe="")
                name_q = urllib.parse.quote(str(name), safe="")
                chapter = self._get(
                    f"texts/{genre}/{category}/{index}/chapters/{stage_q}/{name_q}",
                    ctx,
                )
                if not isinstance(chapter, dict) or "lines" not in chapter:
                    chapters_failed += 1
                    ctx.dead_letter(
                        category="no_match",
                        subcategory="chapter_unavailable",
                        source_key=f"{genre}/{category}/{index}/{stage}/{name}",
                        payload={
                            "genre": genre,
                            "category": category,
                            "index": index,
                            "stage": stage,
                            "name": name,
                        },
                        reason="eBL chapter fetch failed or returned no lines after retries.",
                    )
                    continue
                chapters_done += 1

                for line in chapter.get("lines") or []:
                    en = extract_en(line.get("translation"))
                    if not en:
                        continue
                    line_no = _line_number_str(line.get("number"))
                    if not line_no:
                        continue
                    lines_emitted += 1
                    yield {
                        "text_genre": str(genre),
                        "text_category": int(category),
                        "text_index": int(index),
                        "text_name": text_name,
                        "chapter_stage": str(stage),
                        "chapter_name": str(name),
                        "line_number": line_no,
                        "translation_en": en,
                        "reconstruction": _reconstruction_str(line),
                    }

        ctx.info(
            "ebl.extract_summary",
            texts=texts_done,
            chapters=chapters_done,
            chapters_failed=chapters_failed,
            lines=lines_emitted,
        )

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        for r in rows:
            try:
                self._load_one(ctx, r, stats)
            except Exception as e:  # noqa: BLE001 — route, don't abort the run
                ctx.db.rollback()
                ctx.dead_letter(
                    category="other",
                    subcategory="load_failed",
                    source_key=f"{r.get('text_genre')}/{r.get('text_category')}/"
                    f"{r.get('text_index')}/{r.get('chapter_name')}/{r.get('line_number')}",
                    payload={
                        k: r.get(k)
                        for k in (
                            "text_genre",
                            "text_category",
                            "text_index",
                            "chapter_stage",
                            "chapter_name",
                            "line_number",
                        )
                    },
                    reason=f"load failed: {e}",
                )
                stats.dead_lettered += 1
        return stats

    def _load_one(self, ctx: RunContext, r: dict, stats: LoadStats) -> None:
        row = ctx.db.execute(
            """
            INSERT INTO ebl_translations
                (text_genre, text_category, text_index, text_name,
                 chapter_stage, chapter_name, line_number,
                 translation_en, reconstruction, run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (text_genre, text_category, text_index,
                         chapter_stage, chapter_name, line_number)
            DO UPDATE SET
                text_name      = EXCLUDED.text_name,
                translation_en = EXCLUDED.translation_en,
                reconstruction = EXCLUDED.reconstruction,
                run_id         = EXCLUDED.run_id,
                updated_at     = now()
            RETURNING (xmax = 0) AS inserted
            """,
            (
                r["text_genre"],
                r["text_category"],
                r["text_index"],
                r.get("text_name"),
                r["chapter_stage"],
                r["chapter_name"],
                r["line_number"],
                r["translation_en"],
                r.get("reconstruction"),
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
        # Spot-check: no stored row may have an empty English translation (the
        # NOT NULL column plus this guard against whitespace-only writes).
        row = ctx.db.execute(
            """
            SELECT COUNT(*) AS n FROM ebl_translations
            WHERE length(trim(translation_en)) = 0
            """
        ).fetchone()
        empties = row["n"] if isinstance(row, dict) else row[0]
        if empties:
            raise AssertionError(
                f"{empties} ebl_translations rows have empty English text"
            )
