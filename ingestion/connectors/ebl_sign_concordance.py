"""eBL sign concordance importer.

Merges ABZ numbers and Unicode characters from the eBL sign mapping file
into existing lexical_signs rows. Creates new rows for signs not already present.

Source: source-data/sources/ebl-annotations/cuneiform_ocr_data/sign_mappings/ebl.txt
Format: SIGN_NAME ABZ_NUMBER UNICODE_CHAR (space-delimited)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector, SourceManifest

DEFAULT_EBL_FILE = Path(
    "source-data/sources/ebl-annotations/cuneiform_ocr_data/sign_mappings/ebl.txt"
)

SOURCE_NAME = "ebl-sign-list"
SOURCE_CITATION = "Electronic Babylonian Library (eBL), LMU Munich"
SOURCE_URL = "https://www.ebl.lmu.de/"


class EblSignConcordanceConnector(SourceConnector):
    id = "ebl-sign-concordance"
    display_name = "eBL Sign Concordance"
    description = "Merges ABZ numbers and Unicode chars from eBL into lexical_signs."
    kind = "lexicon"
    runs_after = ["ogsl-signs"]
    upstream_url = "https://www.ebl.lmu.de/"
    license = "CC-BY-4.0"
    citation = "Electronic Babylonian Library (eBL), LMU Munich"

    def __init__(self, ebl_path: Path | None = None) -> None:
        self.ebl_path = Path(ebl_path) if ebl_path else DEFAULT_EBL_FILE

    def discover(self, ctx: RunContext) -> SourceManifest:
        if not self.ebl_path.exists():
            return SourceManifest()
        import hashlib

        h = hashlib.sha256()
        with open(self.ebl_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return SourceManifest(checksum=h.hexdigest()[:32])

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        if not self.ebl_path.exists():
            ctx.warn("ebl_sign.source_missing", path=str(self.ebl_path))
            return
        with open(self.ebl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 3:
                    continue
                sign_name = parts[0]
                abz_raw = parts[1]
                unicode_char = parts[2] if parts[2] != "None" else None
                abz_number = None
                if abz_raw.startswith("ABZ") and not abz_raw.startswith("NoABZ"):
                    abz_number = abz_raw[3:]
                yield {
                    "sign_name": sign_name,
                    "abz_number": abz_number,
                    "unicode_char": unicode_char,
                }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()

        # Load existing signs indexed by name
        existing: dict[str, list[dict]] = {}
        for row in ctx.db.execute(
            "SELECT id, sign_name, sign_number, unicode_char, source, source_contributions "
            "FROM lexical_signs"
        ).fetchall():
            if isinstance(row, dict):
                sid, name, num, uc, src, contributions = (
                    row["id"],
                    row["sign_name"],
                    row["sign_number"],
                    row["unicode_char"],
                    row["source"],
                    row["source_contributions"],
                )
            else:
                sid, name, num, uc, src, contributions = row
            existing.setdefault(name, []).append(
                {
                    "id": sid,
                    "sign_number": num,
                    "unicode_char": uc,
                    "source": src,
                    "contributions": contributions or {},
                }
            )

        for record in rows:
            name = record["sign_name"]
            abz = record["abz_number"]
            uc = record["unicode_char"]

            if name in existing:
                target = existing[name][0]
                updates: list[tuple[str, object]] = []
                contributions = dict(target["contributions"])
                if abz and not target["sign_number"]:
                    updates.append(("sign_number", abz))
                    contributions["sign_number"] = SOURCE_NAME
                if uc and not target["unicode_char"]:
                    updates.append(("unicode_char", uc))
                    contributions["unicode_char"] = SOURCE_NAME
                if updates:
                    set_clauses = ", ".join(f"{col} = %s" for col, _ in updates)
                    set_clauses += ", source_contributions = %s, updated_at = NOW()"
                    values = [v for _, v in updates] + [
                        json.dumps(contributions),
                        target["id"],
                    ]
                    ctx.db.execute(
                        f"UPDATE lexical_signs SET {set_clauses} WHERE id = %s", values
                    )
                    stats.updated += 1
                else:
                    stats.skipped += 1
            else:
                contributions = {}
                if abz:
                    contributions["sign_number"] = SOURCE_NAME
                if uc:
                    contributions["unicode_char"] = SOURCE_NAME
                ctx.db.execute(
                    "INSERT INTO lexical_signs "
                    "(sign_name, sign_number, unicode_char, source, source_citation, "
                    "source_url, source_contributions) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (sign_name, source) DO NOTHING",
                    (
                        name,
                        abz,
                        uc,
                        SOURCE_NAME,
                        SOURCE_CITATION,
                        SOURCE_URL,
                        json.dumps(contributions),
                    ),
                )
                stats.inserted += 1

        ctx.db.commit()
        return stats
