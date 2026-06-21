"""One-time, idempotent geocoder for provenience_canon.

Fills ``latitude`` / ``longitude`` on provenience_canon rows by joining each
canonical find-spot to the public Pleiades gazetteer
(https://pleiades.stoa.org). Run once after migration 049 lands.

DESIGN — be a good citizen (we were just IP-banned by CDLI for per-row
hammering, so this script does the opposite):

  * ONE bulk fetch of the Pleiades CSV dumps (places + names, ~10 MB total),
    cached on disk under source-data/cache/pleiades/. Subsequent runs reuse
    the cache. There is NEVER a per-row network request.
  * All matching is a local join against the cached dumps.

MATCHING — provenience_canon.pleiades_id is empty on every environment (the
ingestion seed never populated it), so we cannot join on the id. Instead we
match by NAME, in priority order, against an index built from the Pleiades
dumps (place title, attested name, transliterated name — all ASCII-folded):

  1. modern_name  (e.g. "Babylon", "Kirkuk", "Ashdod")   — strongest signal
  2. ancient_name (e.g. "Bābili", "Arrapha", "Asdūdu")    — transliterated

When a row matches, we also backfill pleiades_id (it was NULL) so a future run
can join on the id directly and so downstream code can deep-link to Pleiades.

IDEMPOTENT: only rows with NULL latitude AND NULL longitude are updated; safe
to re-run. ``--dry-run`` reports coverage without writing.

macOS SSL note (CLAUDE.md): urllib can fail on some HTTPS endpoints, so the
bulk fetch shells out to ``curl`` via subprocess.

Usage:
    python -m ops.scripts.geocode_provenience --dry-run   # report only
    python -m ops.scripts.geocode_provenience             # write coordinates
    python -m ops.scripts.geocode_provenience --refresh   # re-download dumps
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.database import connect_one_shot  # noqa: E402

CACHE_DIR = _REPO_ROOT / "source-data" / "cache" / "pleiades"
PLACES_URL = (
    "https://atlantides.org/downloads/pleiades/dumps/pleiades-places-latest.csv.gz"
)
NAMES_URL = (
    "https://atlantides.org/downloads/pleiades/dumps/pleiades-names-latest.csv.gz"
)


# --- bulk fetch (one network call per dump, cached) -----------------------


def _download(url: str, dest: Path) -> None:
    """Fetch one gzipped CSV via curl (macOS SSL workaround per CLAUDE.md)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {url}")
    result = subprocess.run(
        ["curl", "-sSL", "--max-time", "180", "-o", str(dest), url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"Pleiades download failed for {url}: {result.stderr}")


def ensure_dumps(refresh: bool = False) -> tuple[Path, Path]:
    places = CACHE_DIR / "pleiades-places-latest.csv.gz"
    names = CACHE_DIR / "pleiades-names-latest.csv.gz"
    if refresh or not places.exists():
        _download(PLACES_URL, places)
    if refresh or not names.exists():
        _download(NAMES_URL, names)
    return places, names


# --- name normalization ---------------------------------------------------


def fold(s: str | None) -> str:
    """ASCII-fold + lowercase a place name for fuzzy-exact matching.

    Strips diacritics (Bābili -> babili), drops non-alphanumerics, collapses
    whitespace. Returns "" for empty/unusable input.
    """
    if not s:
        return ""
    # Decompose accents, drop combining marks.
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Special characters common in Assyriological transliteration.
    s = s.replace("š", "sh").replace("ṣ", "s").replace("ṭ", "t").replace("ḫ", "h")
    s = s.replace("ʾ", "").replace("ʿ", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def _bare_pid(pid: str) -> str:
    """Normalize a Pleiades id to its bare numeric form.

    The places dump exposes ``id`` as ``48210385`` while the names dump exposes
    ``pid`` as ``/places/48210385``. We store the bare numeric id so a future
    join on provenience_canon.pleiades_id and a Pleiades deep-link
    (https://pleiades.stoa.org/places/<id>) are both unambiguous.
    """
    return pid.rsplit("/", 1)[-1].strip()


# Curated aliases for high-value sites the fuzzy name match misses, because
# the canonical provenience name (ancient or its excavation "Tell X" modern
# name) differs from every spelling in the Pleiades dumps. Each value is a
# folded key KNOWN to resolve in the Pleiades index (verified against the
# bulk dump). Keyed by the folded ancient_name. This is explicit and
# auditable — preferred over loosening the fuzzy matcher, which would risk
# false positives (e.g. an unrelated "Kish" island in the Persian Gulf).
CURATED_ALIASES: dict[str, str] = {
    "akhetaten": "amarna",
    "dursharrukin": "dursharrukin",  # also matches via ancient name; explicit
    "esnunna": "eshnunna",
    "karkemish": "carchemish",
    "kutha": "cutha",
    "subatenlil": "tellleilan",  # Šubat-Enlil = Tell Leilan = Shekhna
    # "kish" folds to the Persian-Gulf island of Kish (Pleiades 29630);
    # the Mesopotamian Kiš / Tall al-Uḥaimir (894028) lives under "kis".
    "kish": "kis",
}


def _modern_candidates(modern_name: str | None) -> list[str]:
    """Yield folded match keys from a modern_name field.

    modern_name is often "Babylon" but sometimes "Abydos, Egypt" or "Tell
    Açana" or "uncertain". We skip useless values and split on commas so the
    place part ("Abydos") can match even with a trailing country.
    """
    if not modern_name:
        return []
    low = modern_name.strip().lower()
    if low in {"uncertain", "unknown", ""} or low.startswith("uncertain"):
        return []
    out: list[str] = []
    # Whole string, and the first comma-delimited part.
    for part in [modern_name, modern_name.split(",")[0]]:
        f = fold(part)
        if f and f not in out:
            out.append(f)
    return out


# --- Pleiades index -------------------------------------------------------


def build_index(places: Path, names: Path) -> dict[str, tuple[str, float, float]]:
    """folded name -> (pleiades_id, lat, lon).

    Built from place titles (places dump) and attested/transliterated names
    (names dump). First writer wins so a place's own title outranks an
    incidental attested spelling that collides. Only entries with usable
    reprLat/reprLong are kept.
    """
    index: dict[str, tuple[str, float, float]] = {}

    def add(key: str, pid: str, lat: str, lon: str) -> None:
        if not key or not pid or not lat or not lon:
            return
        try:
            latf, lonf = float(lat), float(lon)
        except ValueError:
            return
        index.setdefault(key, (pid, latf, lonf))

    # Places first (authoritative titles). id is the bare Pleiades place id.
    # setdefault means these win over any colliding incidental attested name.
    with gzip.open(places, "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pid = _bare_pid(row.get("id") or "")
            add(
                fold(row.get("title")),
                pid,
                row.get("reprLat", ""),
                row.get("reprLong", ""),
            )

    # Names: pid (place id, as /places/NNN), nameAttested, nameTransliterated.
    with gzip.open(names, "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pid = _bare_pid(row.get("pid") or "")
            lat = row.get("reprLat", "")
            lon = row.get("reprLong", "")
            for field in ("nameAttested", "nameTransliterated", "title"):
                add(fold(row.get(field)), pid, lat, lon)

    return index


# --- main -----------------------------------------------------------------


def run(dry_run: bool, refresh: bool) -> int:
    print("Pleiades bulk dumps (one fetch, cached — no per-row requests):")
    places, names = ensure_dumps(refresh=refresh)
    print("Building local name index...")
    index = build_index(places, names)
    print(f"  index entries: {len(index)}")

    conn = connect_one_shot()
    try:
        rows = conn.execute(
            """
            SELECT raw_provenience, ancient_name, modern_name, pleiades_id
            FROM provenience_canon
            WHERE latitude IS NULL AND longitude IS NULL
            """
        ).fetchall()

        site_row = conn.execute(
            "SELECT COUNT(DISTINCT ancient_name) AS n FROM provenience_canon"
        ).fetchone()
        total_distinct_sites = site_row["n"] if site_row else 0

        matched = 0
        matched_sites: set[str] = set()
        for r in rows:
            af = fold(r["ancient_name"])
            keys: list[str] = []
            # Curated alias for this ancient name wins first (avoids the wrong
            # same-name place, e.g. Persian-Gulf "Kish"), then modern_name,
            # then the ancient name itself.
            if af in CURATED_ALIASES:
                keys.append(CURATED_ALIASES[af])
            keys += _modern_candidates(r["modern_name"])
            if af:
                keys.append(af)

            hit = next((index[k] for k in keys if k in index), None)
            if not hit:
                continue
            pid, lat, lon = hit
            matched += 1
            matched_sites.add(r["ancient_name"])
            if not dry_run:
                conn.execute(
                    """
                    UPDATE provenience_canon
                    SET latitude = %s,
                        longitude = %s,
                        pleiades_id = COALESCE(NULLIF(pleiades_id, ''), %s)
                    WHERE raw_provenience = %s
                      AND latitude IS NULL AND longitude IS NULL
                    """,
                    (lat, lon, pid, r["raw_provenience"]),
                )

        if not dry_run:
            conn.commit()

        considered = len(rows)
        pct_rows = (matched / considered * 100) if considered else 0.0
        pct_sites = (
            len(matched_sites) / total_distinct_sites * 100
            if total_distinct_sites
            else 0.0
        )
        verb = "WOULD geocode" if dry_run else "Geocoded"
        print()
        print(f"{verb}: {matched}/{considered} empty rows ({pct_rows:.1f}%)")
        print(
            f"Distinct sites located: {len(matched_sites)}/{total_distinct_sites} "
            f"({pct_sites:.1f}%)"
        )
        if dry_run:
            print("(dry run — nothing written)")
    finally:
        conn.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--dry-run", action="store_true", help="report coverage, write nothing"
    )
    p.add_argument("--refresh", action="store_true", help="re-download Pleiades dumps")
    args = p.parse_args()
    return run(dry_run=args.dry_run, refresh=args.refresh)


if __name__ == "__main__":
    sys.exit(main())
