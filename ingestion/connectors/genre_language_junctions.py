"""Genre and language junction table populator.

Reads raw genre/language strings from artifacts, decomposes compound values,
and inserts normalized rows into artifact_genres / artifact_languages.

Depends on: lookup-tables (canonical_genres/canonical_languages), cdli-catalog
"""

from __future__ import annotations

import re
from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

from ingestion.connectors.lookup_tables import GENRE_NORMALIZE

LANG_NORMALIZE: dict[str, str] = {
    "Sumerian": "Sumerian",
    "Akkadian": "Akkadian",
    "Babylonian": "Akkadian",
    "Eblaite": "Eblaite",
    "Ugaritic": "Ugaritic",
    "Aramaic": "Aramaic",
    "Hebrew": "Hebrew",
    "Phoenician": "Phoenician",
    "Sabaean": "Sabaean",
    "Qatabanian": "Qatabanian",
    "Arabic": "Arabic",
    "Mandaic": "Mandaic",
    "Syriac": "Syriac",
    "Hittite": "Hittite",
    "Luwian": "Luwian",
    "Hattic": "Hattic",
    "Elamite": "Elamite",
    "Persian": "Persian",
    "Egyptian": "Egyptian",
    "Greek": "Greek",
    "Hurrian": "Hurrian",
    "Urartian": "Urartian",
}

LANG_SKIP = {
    "undetermined",
    "uncertain",
    "unclear",
    "no linguistic content",
    "uninscribed",
    "clay",
}

_TABLE_KEYS = {
    "artifact_genres": ["p_number", "genre_id"],
    "artifact_languages": ["p_number", "language_id"],
}


def _decompose_genre(raw_genre: str, genre_ids: dict[str, int]) -> list[tuple]:
    """Return list of (p_number placeholder, genre_id, confidence, is_primary)."""
    parts = [p.strip() for p in raw_genre.split(";") if p.strip()]
    results = []
    seen: set[str] = set()
    for i, part in enumerate(parts):
        uncertain = part.rstrip().endswith("?")
        clean = re.sub(r"\s*\?+\s*$", "", part).strip()
        if clean.lower() in ("uncertain", ""):
            continue
        conf = 0.7 if uncertain else 1.0
        canonical = GENRE_NORMALIZE.get(clean.lower())
        if not canonical:
            canonical = clean.title() if clean.islower() else clean
        gid = genre_ids.get(canonical)
        if gid is None or canonical in seen:
            continue
        results.append((gid, conf, len(results) == 0))
        seen.add(canonical)
        if clean.lower() == "royal/votive" and "Votive" not in seen:
            vid = genre_ids.get("Votive")
            if vid:
                results.append((vid, conf, False))
                seen.add("Votive")
    return results


def _decompose_language(raw_lang: str, lang_ids: dict[str, int]) -> list[tuple]:
    normalized = raw_lang.replace(",", ";").replace(
        "Elamite Egyptian", "Elamite; Egyptian"
    )
    parts = [p.strip().rstrip(",") for p in normalized.split(";") if p.strip()]
    results = []
    seen: set[str] = set()
    for part in parts:
        uncertain = part.rstrip().endswith("?")
        clean = re.sub(r"\s*\?+\s*$", "", part).strip()
        is_pseudo = "(pseudo)" in clean.lower()
        clean = re.sub(r"\s*\(pseudo\)", "", clean, flags=re.IGNORECASE).strip()
        if clean.lower() in LANG_SKIP:
            continue
        conf = 0.5 if is_pseudo else (0.7 if uncertain else 1.0)
        canonical = LANG_NORMALIZE.get(clean) or LANG_NORMALIZE.get(clean.title())
        if not canonical or canonical in seen:
            continue
        lid = lang_ids.get(canonical)
        if lid is None:
            continue
        results.append((lid, conf, len(results) == 0))
        seen.add(canonical)
    return results


class GenreLanguageJunctionsConnector(SourceConnector):
    id = "genre-language-junctions"
    display_name = "Artifact Genre/Language Junctions"
    description = "Populates artifact_genres and artifact_languages from artifacts.genre/language columns."
    kind = "derived"
    runs_after = ["lookup-tables", "cdli-catalog"]

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        genre_ids = {
            (row["name"] if isinstance(row, dict) else row[1]): (
                row["id"] if isinstance(row, dict) else row[0]
            )
            for row in ctx.db.execute(
                "SELECT id, name FROM canonical_genres"
            ).fetchall()
        }
        lang_ids = {
            (row["name"] if isinstance(row, dict) else row[1]): (
                row["id"] if isinstance(row, dict) else row[0]
            )
            for row in ctx.db.execute(
                "SELECT id, name FROM canonical_languages"
            ).fetchall()
        }

        if not genre_ids or not lang_ids:
            ctx.warn("genre_language_junctions.canonical_tables_empty")
            return

        for row in ctx.db.execute(
            "SELECT p_number, genre, language FROM artifacts ORDER BY p_number"
        ):
            if isinstance(row, dict):
                p_number, raw_genre, raw_language = (
                    row["p_number"],
                    row["genre"],
                    row["language"],
                )
            else:
                p_number, raw_genre, raw_language = row

            if raw_genre:
                for gid, conf, is_primary in _decompose_genre(raw_genre, genre_ids):
                    yield {
                        "_target": "artifact_genres",
                        "p_number": p_number,
                        "genre_id": gid,
                        "confidence": conf,
                        "is_primary": is_primary,
                    }
            if raw_language:
                for lid, conf, is_primary in _decompose_language(
                    raw_language, lang_ids
                ):
                    yield {
                        "_target": "artifact_languages",
                        "p_number": p_number,
                        "language_id": lid,
                        "confidence": conf,
                        "is_primary": is_primary,
                    }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        by_target: dict[str, list[dict]] = {}
        for row in rows:
            target = row.pop("_target")
            by_target.setdefault(target, []).append(row)

        total = LoadStats()
        for table, batch in by_target.items():
            stats = upsert_batch(
                ctx.db,
                table=table,
                rows=batch,
                unique_key=_TABLE_KEYS[table],
                policy=ConflictPolicy.SKIP,
                batch_size=500,
            )
            ctx.info(f"junctions.loaded.{table}", inserted=stats.inserted)
            total = total.merge(stats)
        return total

    def verify(self, ctx: RunContext) -> None:
        for table in ("artifact_genres", "artifact_languages"):
            row = ctx.db.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
            n = row["n"] if isinstance(row, dict) else row[0]
            ctx.info(f"junctions.verify.{table}", count=n)
