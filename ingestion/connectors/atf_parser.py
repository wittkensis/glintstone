"""CDLI ATF corpus parser.

Single pass over cdliatf_unblocked.atf populates:
  surfaces, text_lines, tokens, translations, composites, artifact_composites

Depends on: annotation-runs, cdli-catalog
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector, SourceManifest

DEFAULT_ATF = Path("source-data/sources/CDLI/metadata/cdliatf_unblocked.atf")
BATCH_SIZE = 500

SURFACE_MAP = {
    "obverse": "obverse",
    "reverse": "reverse",
    "left": "left_edge",
    "right": "right_edge",
    "top": "top_edge",
    "bottom": "bottom_edge",
    "seal": "seal",
    "o": "obverse",
    "r": "reverse",
    "edge": "face",
    "face": "face",
    "column": "column",
    "tablet": "tablet",
    "object": "object",
    "envelope": "envelope",
    "prism": "prism",
    "cylinder": "cylinder",
    "brick": "brick",
    "cone": "cone",
    "bulla": "bulla",
    "tag": None,
}

RE_HEADER = re.compile(r"^&(P\d+)\s*=\s*(.+)$")
RE_LANG = re.compile(r"^#atf:\s*lang\s+(\S+)")
RE_SURFACE = re.compile(r"^@(\w+)(?:\s+(.*))?$")
RE_COLUMN = re.compile(r"^@column\s+(\d+)", re.IGNORECASE)
RE_LINE = re.compile(r"^(\d+(?:\'|\.(?:[a-z](?:\d+)?))?\.)\s+(.+)$")
RE_RULING = re.compile(r"^\$\s*(single|double|triple)\s+ruling", re.IGNORECASE)
RE_BLANK = re.compile(r"^\$\s*(beginning|rest|reverse|surface)\s+broken", re.IGNORECASE)
RE_COMPOSITE = re.compile(r"^>>(Q\d+)\s*(.*)$")
RE_TRANSLATION = re.compile(r"^#tr\.(\w+):\s+(.+)$")


def _parse_atf_file(atf_path: Path) -> Iterator[dict]:
    tablet = None
    current_surface_type = None
    current_column = 0
    line_counter = 0

    with open(atf_path, encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue

            m = RE_HEADER.match(line)
            if m:
                if tablet:
                    yield tablet
                tablet = {
                    "p_number": m.group(1),
                    "lang": "und",
                    "surfaces": {},
                    "lines": [],
                    "translations": [],
                    "composites": [],
                }
                current_surface_type = None
                current_column = 0
                line_counter = 0
                continue

            if tablet is None:
                continue

            m = RE_LANG.match(line)
            if m:
                tablet["lang"] = m.group(1)
                continue

            m = RE_SURFACE.match(line)
            if m:
                marker = m.group(1).lower()
                if marker == "column":
                    col_m = RE_COLUMN.match(line)
                    current_column = (
                        int(col_m.group(1)) if col_m else current_column + 1
                    )
                    continue
                db_surface = SURFACE_MAP.get(marker)
                if db_surface is not None:
                    current_surface_type = db_surface
                    current_column = 0
                    tablet["surfaces"][db_surface] = True
                elif db_surface is None and marker in SURFACE_MAP:
                    current_surface_type = None
                continue

            m = RE_COMPOSITE.match(line)
            if m:
                q_number = "Q" + m.group(1)[1:].zfill(6)
                tablet["composites"].append((q_number, m.group(2).strip()))
                continue

            m = RE_TRANSLATION.match(line)
            if m:
                tablet["translations"].append((m.group(1), m.group(2), line_counter))
                continue

            if RE_RULING.match(line):
                line_counter += 1
                tablet["lines"].append(
                    (
                        current_surface_type,
                        current_column,
                        line_counter,
                        line.strip(),
                        1,
                        0,
                    )
                )
                continue

            if RE_BLANK.match(line) or line.startswith("$ "):
                line_counter += 1
                tablet["lines"].append(
                    (
                        current_surface_type,
                        current_column,
                        line_counter,
                        line.strip(),
                        0,
                        1,
                    )
                )
                continue

            m = RE_LINE.match(line)
            if m:
                label = m.group(1)
                content = m.group(2)
                line_no = label.rstrip(".")
                line_counter += 1
                tablet["lines"].append(
                    (current_surface_type, current_column, line_no, content, 0, 0)
                )

    if tablet:
        yield tablet


def _flush_tablets(
    conn, tablets: list, ann_run_atf, ann_run_cdli, known_p: set, stats: dict
) -> None:
    with conn.cursor() as cur:
        for tablet in tablets:
            p_number = tablet["p_number"]
            if p_number not in known_p:
                stats["skipped_unknown"] += 1
                continue

            surface_id_map: dict[str, int] = {}
            for surface_type in tablet["surfaces"]:
                cur.execute(
                    "INSERT INTO surfaces (p_number, surface_type) VALUES (%s, %s) "
                    "ON CONFLICT (p_number, surface_type) DO NOTHING RETURNING id",
                    (p_number, surface_type),
                )
                row = cur.fetchone()
                if row:
                    surface_id_map[surface_type] = (
                        row[0] if not isinstance(row, dict) else row["id"]
                    )
                    stats["surfaces"] += 1
                else:
                    row = cur.execute(
                        "SELECT id FROM surfaces WHERE p_number = %s AND surface_type = %s",
                        (p_number, surface_type),
                    ).fetchone()
                    if row:
                        surface_id_map[surface_type] = (
                            row[0] if not isinstance(row, dict) else row["id"]
                        )

            for (
                surface_type,
                column_num,
                line_no,
                raw_atf,
                is_ruling,
                is_blank,
            ) in tablet["lines"]:
                surface_id = surface_id_map.get(surface_type) if surface_type else None
                cur.execute(
                    "INSERT INTO text_lines "
                    "(p_number, surface_id, column_number, line_number, raw_atf, is_ruling, is_blank, source) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, 'cdli') "
                    "ON CONFLICT (p_number, surface_id, column_number, line_number, source) DO NOTHING RETURNING id",
                    (
                        p_number,
                        surface_id,
                        column_num,
                        line_no,
                        raw_atf,
                        is_ruling,
                        is_blank,
                    ),
                )
                row = cur.fetchone()
                if row:
                    line_id = row[0] if not isinstance(row, dict) else row["id"]
                    stats["lines"] += 1
                    if not is_ruling and not is_blank:
                        tokens = [p for p in raw_atf.split() if p and p != ","]
                        for pos, token_text in enumerate(tokens):
                            cur.execute(
                                "INSERT INTO tokens (line_id, position, gdl_json, lang) "
                                "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                                (
                                    line_id,
                                    pos,
                                    json.dumps({"frag": token_text}),
                                    tablet["lang"],
                                ),
                            )
                            stats["tokens"] += 1

            for tr_lang, tr_text, _ in tablet["translations"]:
                cur.execute(
                    "INSERT INTO translations (p_number, line_id, translation, language, source, annotation_run_id) "
                    "VALUES (%s, %s, %s, %s, 'cdli', %s) ON CONFLICT DO NOTHING",
                    (p_number, None, tr_text, tr_lang, ann_run_cdli),
                )
                stats["translations"] += 1

            for q_number, label in tablet["composites"]:
                cur.execute(
                    "INSERT INTO composites (q_number, exemplar_count) VALUES (%s, 0) "
                    "ON CONFLICT (q_number) DO UPDATE SET exemplar_count = composites.exemplar_count + 1",
                    (q_number,),
                )
                cur.execute(
                    "INSERT INTO artifact_composites (p_number, q_number) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (p_number, q_number),
                )
                stats["composite_links"] += 1

            stats["tablets"] += 1

    conn.commit()


class AtfParserConnector(SourceConnector):
    id = "atf-parser"
    display_name = "CDLI ATF Corpus Parser"
    description = "Parses cdliatf_unblocked.atf into surfaces, text_lines, tokens, translations, and composites."
    kind = "corpus"
    runs_after = ["annotation-runs", "cdli-catalog"]
    license = "CC0"
    upstream_url = "https://cdli.mpiwg-berlin.mpg.de/"

    def __init__(self, atf_path: Path | None = None) -> None:
        self.atf_path = Path(atf_path) if atf_path else DEFAULT_ATF

    def discover(self, ctx: RunContext) -> SourceManifest:
        if not self.atf_path.exists():
            return SourceManifest()
        import hashlib

        h = hashlib.sha256()
        with open(self.atf_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return SourceManifest(checksum=h.hexdigest()[:32], raw_path=str(self.atf_path))

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        if not self.atf_path.exists():
            ctx.warn("atf_parser.source_missing", path=str(self.atf_path))
            return
        ctx.info("atf_parser.extract_start", path=str(self.atf_path))
        yield from _parse_atf_file(self.atf_path)

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        ann_run_atf = ann_run_cdli = None
        for source_name, attr in (
            ("cdli-atf", "ann_run_atf"),
            ("cdli-catalog", "ann_run_cdli"),
        ):
            row = ctx.db.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s", (source_name,)
            ).fetchone()
            if row:
                val = row["id"] if isinstance(row, dict) else row[0]
                if attr == "ann_run_atf":
                    ann_run_atf = val
                else:
                    ann_run_cdli = val

        known_p = {
            (r["p_number"] if isinstance(r, dict) else r[0])
            for r in ctx.db.execute("SELECT p_number FROM artifacts").fetchall()
        }
        ctx.info("atf_parser.known_artifacts", count=len(known_p))

        raw_stats = {
            "tablets": 0,
            "surfaces": 0,
            "lines": 0,
            "tokens": 0,
            "translations": 0,
            "composite_links": 0,
            "skipped_unknown": 0,
        }
        batch = []
        for tablet in rows:
            batch.append(tablet)
            if len(batch) >= BATCH_SIZE:
                _flush_tablets(
                    ctx.db, batch, ann_run_atf, ann_run_cdli, known_p, raw_stats
                )
                batch = []
                ctx.info(
                    "atf_parser.progress",
                    tablets=raw_stats["tablets"],
                    lines=raw_stats["lines"],
                    tokens=raw_stats["tokens"],
                )
        if batch:
            _flush_tablets(ctx.db, batch, ann_run_atf, ann_run_cdli, known_p, raw_stats)

        ctx.info("atf_parser.done", **raw_stats)
        return LoadStats(inserted=raw_stats["tablets"])

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM text_lines").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("atf_parser.verify", text_lines=n)
