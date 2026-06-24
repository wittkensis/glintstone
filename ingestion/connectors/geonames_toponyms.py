"""GeoNames toponym resolver — resolve provenience find-spots to GeoNames places.

Issue #166. Complements the Pleiades geocoder (ops/scripts/geocode_provenience.py,
issue #196) and the Wikidata linker (#164). Pleiades is an *ancient*-places
gazetteer and misses many sites; the backlog notes ~106 proveniences still
ungeocoded (including Nineveh under some spellings). GeoNames is a much larger
*modern* gazetteer (12M+ places) with strong coverage of modern tell names and
cities, so it can lift the map's site coverage.

DATA-AVAILABILITY VERDICT (audited 2026-06 before building):
  GeoNames publishes free per-country bulk dumps at
  https://download.geonames.org/export/dump/<CC>.zip (verified reachable: IQ
  ~2.8 MB, SY, TR all 200). Each is a tab-separated file with columns:
    geonameid, name, asciiname, alternatenames, latitude, longitude,
    feature_class, feature_code, country_code, ... (19 cols, no header).
  Mesopotamian / Near-Eastern proveniences live in a small set of modern
  countries, so we fetch only those dumps (IQ SY TR IR JO IL LB EG KW SA),
  cache them on disk, and do ALL matching as a local join. There is NEVER a
  per-row network request — the same good-citizen posture the Pleiades geocoder
  adopted after the CDLI IP-ban lesson.

ACCURACY OVER COVERAGE (the load-bearing rule for #166):
  A wrong place is bad scholarly data. We therefore match ONLY by EXACT folded
  name equality (diacritics stripped, Assyriological transliteration normalised),
  never by edit distance / fuzzy similarity. When a folded name resolves to:
    * exactly ONE GeoNames place → store it (confident).
    * MULTIPLE GeoNames places → dead-letter as ambiguous (never guess).
    * NO GeoNames place → silently skip (counted, not an error).
  We further bias toward archaeological/antiquity feature codes when one name
  has several candidates within one country (a TELL / RUIN / ANS beats a generic
  PPL), and otherwise treat >1 candidate as ambiguous.

  Match priority per provenience (first hit wins):
    1. curated alias  (human-verified, confidence 1.0)
    2. modern_name    (provenience.modern_name, confidence 0.85 / 0.95 site)
    3. ancient_name   (provenience.ancient_name, confidence 0.85 / 0.95 site)

SIDE EFFECT (coverage lift): besides writing provenience_geonames, the connector
backfills provenience_canon.latitude/longitude ONLY where they are currently
NULL — it never overwrites an existing (Pleiades) coordinate, so the two
gazetteers don't fight and the map simply gains the sites Pleiades missed.

macOS SSL note (CLAUDE.md): the bulk fetch shells out to curl via subprocess.
"""

from __future__ import annotations

import csv
import io
import re
import subprocess
import unicodedata
import zipfile
from pathlib import Path
from typing import Iterable, Iterator, Optional

from ingestion.base import LoadStats, RunContext, SourceConnector, SourceManifest

# --- source config ---------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = _REPO_ROOT / "source-data" / "cache" / "geonames"
GEONAMES_BASE = "https://download.geonames.org/export/dump"

# Countries that hold the overwhelming majority of cuneiform find-spots. Kept
# deliberately small so the cache is a few MB and the local index is tight —
# adding a country is a one-line change if a new corpus needs it.
DEFAULT_COUNTRIES = ["IQ", "SY", "TR", "IR", "JO", "IL", "LB", "EG", "KW", "SA"]

DEFAULT_USER_AGENT = (
    "Glintstone/0.1 (Assyriology toponym resolution; "
    "+https://app.glintstone.org; contact eric.wittke@gmail.com)"
)

# GeoNames feature codes that denote an archaeological / ancient site. A name
# that matches one of these is a stronger signal than a generic populated place,
# and is used to disambiguate when a name has multiple candidates in a country.
SITE_FEATURE_CODES = {"ANS", "RUIN", "TELL", "HSTS", "PPLH"}

# Confidence scoring (sub-1.0 because exact NAME equality is weaker than an
# id-to-id map; cf. Pleiades id match = 1.0).
CONF_ALIAS = 1.0  # human-verified curated alias
CONF_SITE = 0.95  # exact folded name == an archaeological-site feature code
CONF_NAME = 0.85  # exact folded name == a generic populated place

MATCH_ALIAS = "alias"
MATCH_MODERN = "modern-name"
MATCH_ANCIENT = "ancient-name"

# Curated, human-verified aliases for high-value sites whose canonical
# provenience name matches no GeoNames name directly. Keyed by folded
# ancient_name → folded GeoNames name KNOWN to resolve. Explicit and auditable;
# preferred over loosening the matcher (which would risk false positives).
CURATED_ALIASES: dict[str, str] = {
    # Šubat-Enlil = Tell Leilan
    "subatenlil": "tellleilan",
    # Dur-Šarrukin = Khorsabad
    "dursharrukin": "khorsabad",
    # Kalhu = Nimrud
    "kalhu": "nimrud",
    # Akkad/Agade unknown — deliberately NOT aliased (location uncertain).
}


# --- name normalisation (shared doctrine with geocode_provenience.fold) -----


def fold(s: Optional[str]) -> str:
    """ASCII-fold + lowercase a place name for exact (non-fuzzy) matching.

    Strips diacritics (Bābili → babili), normalises Assyriological
    transliteration (š→sh, ṣ→s, ṭ→t, ḫ→h), drops non-alphanumerics. Returns ""
    for unusable input. Identical doctrine to ops/scripts/geocode_provenience.py
    so the two gazetteers fold names the same way.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = s.replace("š", "sh").replace("ṣ", "s").replace("ṭ", "t").replace("ḫ", "h")
    s = s.replace("ʾ", "").replace("ʿ", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


# Provenience placeholder names that are NOT real sites and must never be
# geocoded — "uncertain" alone covers ~200 rows in prod. Geocoding these would
# pin unrelated tablets to an arbitrary same-named place: bad scholarly data.
_PLACEHOLDER_PREFIXES = ("uncertain", "unknown")
_PLACEHOLDER_EXACT = {"uncertain", "unknown", "n/a", "none", "?", "-", ""}


def _is_placeholder(name: Optional[str]) -> bool:
    """True when a provenience name is a 'not a real place' placeholder."""
    if not name:
        return True
    low = name.strip().lower()
    return low in _PLACEHOLDER_EXACT or low.startswith(_PLACEHOLDER_PREFIXES)


def _modern_candidates(modern_name: Optional[str]) -> list[str]:
    """Folded match keys from a modern_name field (skips 'uncertain', splits commas)."""
    if _is_placeholder(modern_name):
        return []
    assert modern_name is not None  # _is_placeholder guards None/empty
    out: list[str] = []
    for part in [modern_name, modern_name.split(",")[0]]:
        f = fold(part)
        if f and f not in out:
            out.append(f)
    return out


# --- bulk fetch (one network call per country dump, cached) ----------------


def _download(url: str, dest: Path, *, user_agent: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["curl", "-sSL", "-A", user_agent, "--max-time", "180", "-o", str(dest), url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"GeoNames download failed for {url}: {result.stderr}")


def ensure_dumps(
    countries: list[str], *, user_agent: str, refresh: bool = False
) -> list[Path]:
    paths: list[Path] = []
    for cc in countries:
        dest = CACHE_DIR / f"{cc}.zip"
        if refresh or not dest.exists():
            _download(f"{GEONAMES_BASE}/{cc}.zip", dest, user_agent=user_agent)
        paths.append(dest)
    return paths


# --- local index -----------------------------------------------------------

# GeoNames dump column order (19 cols, tab-separated, no header).
_COL_GEONAMEID = 0
_COL_NAME = 1
_COL_ASCIINAME = 2
_COL_ALTNAMES = 3
_COL_LAT = 4
_COL_LON = 5
_COL_FEATURE_CODE = 7
_COL_COUNTRY = 8


def build_index(dump_paths: list[Path]) -> dict[str, list[dict]]:
    """folded name → list of candidate places.

    Each candidate: {geonames_id, name, lat, lon, feature_code, country}. A name
    that appears on several places yields several candidates — the caller decides
    confident-vs-ambiguous. We index the ascii name, the unicode name, and each
    alternate name, all folded, so an exact-folded lookup is O(1).
    """
    index: dict[str, list[dict]] = {}

    def add(key: str, cand: dict) -> None:
        if not key:
            return
        bucket = index.setdefault(key, [])
        # Dedup by geonames_id within a key (one place, many spellings).
        if not any(c["geonames_id"] == cand["geonames_id"] for c in bucket):
            bucket.append(cand)

    for path in dump_paths:
        with zipfile.ZipFile(path) as zf:
            inner = path.stem + ".txt"  # e.g. IQ.zip → IQ.txt
            names = zf.namelist()
            target = (
                inner
                if inner in names
                else next(
                    (
                        n
                        for n in names
                        if n.endswith(".txt") and not n.startswith("readme")
                    ),
                    None,
                )
            )
            if target is None:
                continue
            with zf.open(target) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8")
                reader = csv.reader(text, delimiter="\t", quoting=csv.QUOTE_NONE)
                for row in reader:
                    if len(row) < 9:
                        continue
                    try:
                        lat = float(row[_COL_LAT])
                        lon = float(row[_COL_LON])
                    except (ValueError, IndexError):
                        continue
                    gid = row[_COL_GEONAMEID].strip()
                    if not gid.isdigit():
                        continue
                    cand = {
                        "geonames_id": gid,
                        "name": row[_COL_ASCIINAME] or row[_COL_NAME],
                        "lat": lat,
                        "lon": lon,
                        "feature_code": row[_COL_FEATURE_CODE],
                        "country": row[_COL_COUNTRY],
                    }
                    add(fold(row[_COL_NAME]), cand)
                    add(fold(row[_COL_ASCIINAME]), cand)
                    for alt in (row[_COL_ALTNAMES] or "").split(","):
                        add(fold(alt), cand)
    return index


def _resolve(candidates: list[dict]) -> tuple[Optional[dict], Optional[str], float]:
    """Pick the confident match from a name's candidates, or report ambiguity.

    Returns (chosen | None, reason_if_unresolved | None, confidence).
    - 1 candidate → that one.
    - >1 candidate but exactly one is an archaeological-site feature code → it
      (sites are unambiguous targets for a find-spot).
    - otherwise >1 candidate → ambiguous (no confident pick; never guess).
    """
    if not candidates:
        return None, "no_match", 0.0
    if len(candidates) == 1:
        c = candidates[0]
        conf = CONF_SITE if c["feature_code"] in SITE_FEATURE_CODES else CONF_NAME
        return c, None, conf
    sites = [c for c in candidates if c["feature_code"] in SITE_FEATURE_CODES]
    if len(sites) == 1:
        return sites[0], None, CONF_SITE
    return None, "ambiguous", 0.0


# --- connector -------------------------------------------------------------


class GeonamesToponymsConnector(SourceConnector):
    id = "geonames-toponyms"
    display_name = "GeoNames Toponym Resolver (provenience → GeoNames place)"
    description = (
        "Resolves canonical provenience find-spots to GeoNames places by EXACT "
        "folded-name equality against cached GeoNames country dumps. Stores only "
        "confident, unambiguous matches (accuracy over coverage); backfills "
        "provenience_canon coordinates only where NULL. Complements Pleiades."
    )
    kind = "derived"
    runs_after = ["lookup-tables"]
    upstream_url = "https://www.geonames.org/"
    license = "CC-BY-4.0"
    license_url = "https://creativecommons.org/licenses/by/4.0/"
    citation = "GeoNames (https://www.geonames.org/), CC BY 4.0"
    contact_email = "eric.wittke@gmail.com"

    def __init__(
        self,
        *,
        countries: Optional[list[str]] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        refresh: bool = False,
    ) -> None:
        self.countries = countries or DEFAULT_COUNTRIES
        self.user_agent = user_agent
        self.refresh = refresh
        self._index: dict[str, list[dict]] = {}

    # --- lifecycle ---

    def discover(self, ctx: RunContext) -> SourceManifest:
        # Always-run: GeoNames dumps refresh frequently and the resolver is cheap
        # and idempotent. (No cheap upstream checksum without downloading.)
        return SourceManifest()

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        countries = ctx.config.get("countries") or self.countries
        refresh = bool(ctx.config.get("refresh", self.refresh))
        ctx.info("geonames.fetch_dumps", countries=countries, refresh=refresh)
        dumps = ensure_dumps(countries, user_agent=self.user_agent, refresh=refresh)
        self._index = build_index(dumps)
        ctx.info("geonames.index_built", entries=len(self._index))

        rows = ctx.db.execute(
            """
            SELECT DISTINCT ancient_name, modern_name
            FROM provenience_canon
            WHERE ancient_name IS NOT NULL
              AND length(trim(ancient_name)) > 0
            ORDER BY ancient_name
            """
        ).fetchall()

        matched = ambiguous = no_match = skipped_placeholder = 0
        for r in rows:
            ancient = r["ancient_name"] if isinstance(r, dict) else r[0]
            modern = r["modern_name"] if isinstance(r, dict) else r[1]
            # "uncertain" / "unknown" are not real sites — never geocode them.
            if _is_placeholder(ancient):
                skipped_placeholder += 1
                continue
            af = fold(ancient)

            # Build (key, match_basis) candidates in priority order.
            attempts: list[tuple[str, str]] = []
            if af in CURATED_ALIASES:
                attempts.append((CURATED_ALIASES[af], MATCH_ALIAS))
            for k in _modern_candidates(modern):
                attempts.append((k, MATCH_MODERN))
            if af:
                attempts.append((af, MATCH_ANCIENT))

            chosen = None
            chosen_basis = None
            chosen_conf = 0.0
            ambiguous_for_name = False
            for key, basis in attempts:
                cands = self._index.get(key)
                if not cands:
                    continue
                pick, reason, conf = _resolve(cands)
                if pick is not None:
                    chosen, chosen_basis, chosen_conf = (
                        pick,
                        basis,
                        (CONF_ALIAS if basis == MATCH_ALIAS else conf),
                    )
                    break
                if reason == "ambiguous":
                    ambiguous_for_name = True
                    # keep trying lower-priority keys; only dead-letter if none resolves

            if chosen is None:
                if ambiguous_for_name:
                    ambiguous += 1
                    # Idempotent dead-letter: only write if this site isn't
                    # already an open dead letter, so re-runs don't grow the DLQ
                    # with duplicate ambiguity reports (which would trip the #175
                    # alert every run for a stable, already-known ambiguity).
                    if not self._already_open(ctx, ancient):
                        ctx.dead_letter(
                            category="no_match",
                            subcategory="ambiguous_geonames_match",
                            source_key=ancient,
                            payload={"ancient_name": ancient, "modern_name": modern},
                            reason=(
                                "Provenience name resolves to multiple GeoNames "
                                "places with no single archaeological-site "
                                "disambiguator; no confident match (accuracy over "
                                "coverage)."
                            ),
                        )
                else:
                    no_match += 1
                continue

            matched += 1
            yield {
                "ancient_name": ancient,
                "geonames_id": chosen["geonames_id"],
                "geonames_name": chosen["name"],
                "latitude": chosen["lat"],
                "longitude": chosen["lon"],
                "feature_code": chosen["feature_code"] or None,
                "country_code": chosen["country"] or None,
                "match_basis": chosen_basis,
                "confidence": round(chosen_conf, 2),
            }

        ctx.info(
            "geonames.resolution_summary",
            considered=len(rows),
            matched=matched,
            ambiguous=ambiguous,
            no_match=no_match,
            skipped_placeholder=skipped_placeholder,
        )

    @staticmethod
    def _already_open(ctx: RunContext, ancient_name: str) -> bool:
        """True if an open ambiguous dead letter already exists for this site."""
        row = ctx.db.execute(
            """
            SELECT 1 FROM import_dead_letters
            WHERE connector_id = %s
              AND subcategory = 'ambiguous_geonames_match'
              AND source_key = %s
              AND resolution_status = 'open'
            LIMIT 1
            """,
            (ctx.connector_id, ancient_name),
        ).fetchone()
        return row is not None

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
                    source_key=r.get("ancient_name"),
                    payload={
                        k: r.get(k)
                        for k in ("ancient_name", "geonames_id", "match_basis")
                    },
                    reason=f"load failed: {e}",
                )
                stats.dead_lettered += 1
        return stats

    def _load_one(self, ctx: RunContext, r: dict, stats: LoadStats) -> None:
        """Idempotent upsert into provenience_geonames + conservative coord backfill."""
        row = ctx.db.execute(
            """
            INSERT INTO provenience_geonames
                (ancient_name, geonames_id, geonames_name, latitude, longitude,
                 feature_code, country_code, match_basis, confidence, run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ancient_name, match_basis) DO UPDATE SET
                geonames_id   = EXCLUDED.geonames_id,
                geonames_name = EXCLUDED.geonames_name,
                latitude      = EXCLUDED.latitude,
                longitude     = EXCLUDED.longitude,
                feature_code  = EXCLUDED.feature_code,
                country_code  = EXCLUDED.country_code,
                confidence    = EXCLUDED.confidence,
                run_id        = EXCLUDED.run_id,
                updated_at    = now()
            RETURNING (xmax = 0) AS inserted
            """,
            (
                r["ancient_name"],
                r["geonames_id"],
                r.get("geonames_name"),
                r["latitude"],
                r["longitude"],
                r.get("feature_code"),
                r.get("country_code"),
                r["match_basis"],
                r["confidence"],
                ctx.run_id,
            ),
        ).fetchone()
        inserted = row["inserted"] if isinstance(row, dict) else row[0]

        # Coverage lift: backfill provenience_canon coords ONLY where NULL — never
        # overwrite an existing (e.g. Pleiades) coordinate. One ancient_name may
        # back several raw_provenience rows; update them all.
        ctx.db.execute(
            """
            UPDATE provenience_canon
            SET latitude = %s, longitude = %s
            WHERE ancient_name = %s
              AND latitude IS NULL AND longitude IS NULL
            """,
            (r["latitude"], r["longitude"], r["ancient_name"]),
        )
        ctx.db.commit()
        if inserted:
            stats.inserted += 1
        else:
            stats.updated += 1

    def verify(self, ctx: RunContext) -> None:
        # Every stored match must point at an ancient_name that exists in
        # provenience_canon (no orphans), and coordinates must be in range (the
        # CHECK constraint already enforces range at write time; this is a
        # cross-table integrity spot-check).
        row = ctx.db.execute(
            """
            SELECT COUNT(*) AS n
            FROM provenience_geonames g
            WHERE NOT EXISTS (
                SELECT 1 FROM provenience_canon p
                WHERE p.ancient_name = g.ancient_name
            )
            """
        ).fetchone()
        orphans = row["n"] if isinstance(row, dict) else row[0]
        if orphans:
            raise AssertionError(
                f"{orphans} provenience_geonames rows reference an unknown ancient_name"
            )
