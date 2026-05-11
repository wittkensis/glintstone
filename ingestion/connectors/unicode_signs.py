"""Unicode cuneiform sign metadata importer.

Enriches existing lexical_signs with Unicode code points and official names.
Creates new rows for Unicode signs not already in the database.

Source: source-data/sources/ePSD2/unicode/cuneiform-signs.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector, SourceManifest

DEFAULT_UNICODE_FILE = Path("source-data/sources/ePSD2/unicode/cuneiform-signs.json")

SOURCE_NAME = "unicode-standard"
SOURCE_CITATION = "The Unicode Standard, Unicode Consortium"
SOURCE_URL = "https://www.unicode.org/charts/PDF/U12000.pdf"


def _parse_sign_name(unicode_name: str) -> str | None:
    m = re.match(r"^CUNEIFORM SIGN (.+)$", unicode_name)
    if not m:
        return None
    raw = m.group(1)
    raw = re.sub(r"\s+TIMES\s+", "×", raw)
    raw = re.sub(r"\s+OVER\s+", "&", raw)
    raw = re.sub(r"\s+OPPOSING\s+", ".OPPOSING.", raw)
    return raw


class UnicodeSignsConnector(SourceConnector):
    id = "unicode-signs"
    display_name = "Unicode Cuneiform Sign Metadata"
    description = "Enriches lexical_signs with Unicode code points and official Unicode character names."
    kind = "lexicon"
    runs_after = ["epsd2"]
    upstream_url = "https://www.unicode.org/"
    license = "Unicode License Agreement"

    def __init__(self, unicode_path: Path | None = None) -> None:
        self.unicode_path = Path(unicode_path) if unicode_path else DEFAULT_UNICODE_FILE

    def discover(self, ctx: RunContext) -> SourceManifest:
        if not self.unicode_path.exists():
            return SourceManifest()
        import hashlib

        h = hashlib.sha256()
        with open(self.unicode_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return SourceManifest(checksum=h.hexdigest()[:32])

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        if not self.unicode_path.exists():
            ctx.warn("unicode_signs.source_missing", path=str(self.unicode_path))
            return
        with open(self.unicode_path, encoding="utf-8") as f:
            data = json.load(f)
        for sign in data.get("signs", []):
            yield {
                "character": sign["character"],
                "codepoint": sign["codePoint"],
                "name": sign["name"],
            }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()

        # Index existing signs by unicode_char
        by_unicode: dict[str, dict] = {}
        for row in ctx.db.execute(
            "SELECT id, sign_name, unicode_char, source_contributions "
            "FROM lexical_signs WHERE unicode_char IS NOT NULL"
        ).fetchall():
            if isinstance(row, dict):
                sid, name, uc, contributions = (
                    row["id"],
                    row["sign_name"],
                    row["unicode_char"],
                    row["source_contributions"],
                )
            else:
                sid, name, uc, contributions = row
            if uc not in by_unicode:
                by_unicode[uc] = {
                    "id": sid,
                    "name": name,
                    "contributions": contributions or {},
                }

        for record in rows:
            char = record["character"]
            codepoint = record["codepoint"]
            name = record["name"]

            if char in by_unicode:
                target = by_unicode[char]
                contributions = dict(target["contributions"])
                contributions["unicode_codepoint"] = SOURCE_NAME
                contributions["unicode_name"] = SOURCE_NAME
                ctx.db.execute(
                    "UPDATE lexical_signs SET unicode_codepoint = %s, unicode_name = %s, "
                    "source_contributions = %s, updated_at = NOW() WHERE id = %s",
                    (codepoint, name, json.dumps(contributions), target["id"]),
                )
                stats.updated += 1
            else:
                parsed_name = _parse_sign_name(name)
                if not parsed_name:
                    stats.skipped += 1
                    continue
                contributions = {
                    "unicode_char": SOURCE_NAME,
                    "unicode_codepoint": SOURCE_NAME,
                    "unicode_name": SOURCE_NAME,
                }
                ctx.db.execute(
                    "INSERT INTO lexical_signs "
                    "(sign_name, unicode_char, unicode_codepoint, unicode_name, "
                    "source, source_citation, source_url, source_contributions) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (sign_name, source) DO NOTHING",
                    (
                        parsed_name,
                        char,
                        codepoint,
                        name,
                        SOURCE_NAME,
                        SOURCE_CITATION,
                        SOURCE_URL,
                        json.dumps(contributions),
                    ),
                )
                stats.inserted += 1

        ctx.db.commit()
        return stats

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM lexical_signs WHERE unicode_char IS NOT NULL"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("unicode_signs.verify", with_unicode_char=n)
