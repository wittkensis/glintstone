"""ORACC CDL ATF -> text_lines / tokens importer (Fix A, issue #273).

The CDLI ATF parser (`atf-parser`) only populates text_lines/tokens for tablets
that appear in the flat `cdliatf_unblocked.atf` file. ~15.9K tablets have ORACC
corpusjson on disk but ZERO rows in text_lines, which is why the
`oracc-lemmatizations` connector dead-letters millions of lemmas with
`no_line_match` — it tries to match (p_number, line_number) against text_lines
that were never created.

This connector closes that gap: it walks each ORACC corpusjson CDL tree and
reconstructs text_lines + tokens (source='oracc') directly from the L-nodes and
line-start d-nodes, so the lemmatization match step finally has lines/tokens to
hit. It reuses the CDL-walking primitives from oracc_lemmatizations
(`_find_corpus_dirs`, `_parse_surface_from_label`, `ORACC_PROJECTS`,
`_project_base`) rather than re-deriving them.

Idempotency: text_lines insert uses ON CONFLICT on
(p_number, surface_id, column_number, line_number, source); tokens insert uses
ON CONFLICT (line_id, position) — the constraint added by migration 051. Both
are DO NOTHING, so re-running (e.g. after Fix C catalogs the remaining 6,204
tablets) only fills gaps and never duplicates.

Scope (Fix A): only p_numbers that are already in `artifacts` are written. The
6,204 not-yet-cataloged p_numbers are silently skipped with a counter — they are
expected to be missing until Fix C (#238) runs, so they are NOT dead-lettered.

Depends on: cdli-catalog (for the artifacts guard) + annotation-runs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector
from ingestion.dead_letters import DeadLetterCategory
from ingestion.connectors.oracc_lemmatizations import (
    ORACC_PROJECTS,
    _find_corpus_dirs,
    _parse_surface_from_label,
)

BATCH_SIZE = 200
DEAD_LETTER_FLUSH_EVERY = 5000

# ORACC frag strings carry GDL-internal control markers (e.g. "a-na\t", "TA@v\m")
# that are NOT part of the ATF surface text — they encode sign modifiers/flags
# the renderer uses, not characters a scholar reads. Strip them when building
# raw_atf so the stored line is clean ATF. The clean per-token form lives in
# f.form and is stored separately on tokens.raw_form.
_FRAG_MARKER_RE = re.compile(r"\\[a-z]")


def _clean_frag(frag: str) -> str:
    """Strip GDL control markers from an L-node frag for raw_atf reconstruction."""
    return _FRAG_MARKER_RE.sub("", frag).strip()


def _parse_tablet(data: dict) -> dict | None:
    """Walk one corpusjson CDL tree into {p_number, surfaces, lines}.

    A `line` is one displayed text line: {surface, line_number, raw_atf, tokens}.
    `tokens` is an ordered list of {position, gdl_json, lang, raw_form}.

    line_number keeps ORACC's native string verbatim (e.g. "1'", "2") so the
    prime notation matches what oracc-lemmatizations later looks up. Returns
    None if the file carries no usable transliteration.
    """
    p_number = data.get("textid", "")
    if not p_number:
        return None

    surfaces: set[str] = set()
    # lines keyed by (surface, line_number) so repeated line-start markers for
    # the same display line (rare, but ORACC can re-open a line) accumulate
    # tokens instead of producing a duplicate row that would just ON CONFLICT.
    lines: dict[tuple[str | None, str], dict] = {}
    order: list[tuple[str | None, str]] = []

    state: dict = {"surface": None, "line_number": None}

    def walk(nodes) -> None:
        if not isinstance(nodes, list):
            return
        for node in nodes:
            if not isinstance(node, dict):
                continue
            ntype = node.get("node")
            if ntype == "d":
                dtype = node.get("type")
                if dtype == "surface":
                    surf = _parse_surface_from_label(node.get("subtype", "")) or (
                        _parse_surface_from_label(node.get("label", ""))
                    )
                    state["surface"] = surf
                    if surf:
                        surfaces.add(surf)
                    state["line_number"] = None
                elif dtype == "line-start":
                    line_n = node.get("n")
                    state["line_number"] = str(line_n) if line_n is not None else None
                    # line-start carries a surface hint in its label ("o 1");
                    # fall back to it if no surface d-node was seen yet.
                    if state["surface"] is None:
                        surf = _parse_surface_from_label(node.get("label", ""))
                        if surf:
                            state["surface"] = surf
                            surfaces.add(surf)
            elif ntype == "l":
                line_number = state.get("line_number")
                if line_number is None:
                    # An L-node with no preceding line-start has no place to
                    # land; skip rather than invent a line number.
                    continue
                f_data = node.get("f", {})
                ref = node.get("ref", "")
                parts = ref.split(".")
                position = None
                if len(parts) >= 3:
                    try:
                        position = int(parts[-1], 16) - 1
                    except ValueError:
                        position = None
                if position is None:
                    continue
                key = (state.get("surface"), line_number)
                bucket = lines.get(key)
                if bucket is None:
                    bucket = {
                        "surface": state.get("surface"),
                        "line_number": line_number,
                        "tokens": [],
                    }
                    lines[key] = bucket
                    order.append(key)
                bucket["tokens"].append(
                    {
                        "position": position,
                        "frag": node.get("frag", "") or "",
                        "gdl": f_data.get("gdl"),
                        "lang": f_data.get("lang"),
                        "form": f_data.get("form"),
                    }
                )
            if "cdl" in node:
                walk(node["cdl"])

    walk(data.get("cdl", []))

    if not order:
        return None

    out_lines = []
    for key in order:
        bucket = lines[key]
        toks = bucket["tokens"]
        # Reconstruct raw_atf: dedupe positions (ORACC occasionally repeats an
        # L-node ref), order by position, join cleaned frags with a space (ATF
        # words are space-separated).
        by_pos: dict[int, dict] = {}
        for t in toks:
            by_pos.setdefault(t["position"], t)
        ordered_toks = [by_pos[p] for p in sorted(by_pos)]
        raw_atf = " ".join(
            _clean_frag(t["frag"]) for t in ordered_toks if _clean_frag(t["frag"])
        )
        out_lines.append(
            {
                "surface": bucket["surface"],
                "line_number": bucket["line_number"],
                "raw_atf": raw_atf,
                "tokens": ordered_toks,
            }
        )

    return {"p_number": p_number, "surfaces": sorted(surfaces), "lines": out_lines}


class OraccAtfConnector(SourceConnector):
    id = "oracc-atf"
    display_name = "ORACC CDL ATF -> text_lines"
    description = (
        "Parses ORACC corpusjson CDL data into surfaces, text_lines, and tokens "
        "(source='oracc') for tablets with no CDLI ATF."
    )
    kind = "corpus"
    # Must run AFTER the catalog (the artifacts guard) and annotation-runs, and
    # after atf-parser so CDLI-sourced lines exist first; it must run BEFORE
    # oracc-lemmatizations so the lemma match step has these lines/tokens to hit.
    # The before-relationship is expressed on oracc-lemmatizations' own
    # runs_after (see that connector); here we only declare our upstreams.
    runs_after = ["annotation-runs", "cdli-catalog", "atf-parser"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        projects = ctx.config.get("projects") or ORACC_PROJECTS
        for project in projects:
            corpus_dirs = _find_corpus_dirs(project)
            if not corpus_dirs:
                continue
            cdl_files = []
            for cdir in corpus_dirs:
                cdl_files.extend(sorted(cdir.glob("P*.json")))
            if cdl_files:
                yield {"project": project, "cdl_files": [str(p) for p in cdl_files]}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        known_p = {
            (r["p_number"] if isinstance(r, dict) else r[0])
            for r in ctx.db.execute("SELECT p_number FROM artifacts").fetchall()
        }
        ctx.info("oracc_atf.known_artifacts", count=len(known_p))

        stats = {
            "tablets": 0,
            "lines": 0,
            "tokens": 0,
            "skipped_not_in_artifacts": 0,
            "skipped_no_data": 0,
        }
        dl_buffer: list[dict] = []

        def flush_dl() -> None:
            nonlocal dl_buffer
            if dl_buffer:
                ctx.dead_letter_many(dl_buffer)
                dl_buffer = []

        for batch in rows:
            project = batch["project"]
            cdl_files = [Path(p) for p in batch["cdl_files"]]
            pending: list[dict] = []

            for cdl_file in cdl_files:
                try:
                    with open(cdl_file, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, ValueError, OSError):
                    dl_buffer.append(
                        {
                            "category": DeadLetterCategory.VALIDATION_FAILED.value,
                            "subcategory": "malformed_cdl",
                            "source_key": f"{project}/{cdl_file.stem}",
                            "payload": {"project": project, "file": str(cdl_file)},
                            "reason": "corpusjson failed to parse as JSON",
                        }
                    )
                    continue

                p_number = data.get("textid", "")
                if not p_number:
                    dl_buffer.append(
                        {
                            "category": DeadLetterCategory.VALIDATION_FAILED.value,
                            "subcategory": "missing_p_number",
                            "source_key": f"{project}/{cdl_file.stem}",
                            "payload": {"project": project, "file": str(cdl_file)},
                            "reason": "corpusjson has no textid",
                        }
                    )
                    continue

                # Fix A scope: only tablets already in artifacts. The remaining
                # bucket waits for Fix C (#238) and is silently skipped, NOT
                # dead-lettered (it is expected, not an error).
                if p_number not in known_p:
                    stats["skipped_not_in_artifacts"] += 1
                    continue

                tablet = _parse_tablet(data)
                if tablet is None:
                    stats["skipped_no_data"] += 1
                    continue
                pending.append(tablet)

                if len(pending) >= BATCH_SIZE:
                    self._flush(ctx, pending, stats)
                    pending = []
                if len(dl_buffer) >= DEAD_LETTER_FLUSH_EVERY:
                    flush_dl()

            if pending:
                self._flush(ctx, pending, stats)
            flush_dl()
            ctx.info(
                "oracc_atf.project_done",
                project=project,
                tablets=stats["tablets"],
                lines=stats["lines"],
                tokens=stats["tokens"],
            )

        flush_dl()
        ctx.info("oracc_atf.done", **stats)
        return LoadStats(
            inserted=stats["lines"],
            skipped=stats["skipped_not_in_artifacts"] + stats["skipped_no_data"],
        )

    def _flush(self, ctx: RunContext, tablets: list[dict], stats: dict) -> None:
        with ctx.db.cursor() as cur:
            for tablet in tablets:
                p_number = tablet["p_number"]
                surface_id_map = self._ensure_surfaces(
                    cur, p_number, tablet["surfaces"]
                )

                for line in tablet["lines"]:
                    surface_id = (
                        surface_id_map.get(line["surface"]) if line["surface"] else None
                    )
                    cur.execute(
                        "INSERT INTO text_lines "
                        "(p_number, surface_id, column_number, line_number, raw_atf, "
                        "is_ruling, is_blank, source) "
                        "VALUES (%s, %s, 0, %s, %s, 0, 0, 'oracc') "
                        "ON CONFLICT (p_number, surface_id, column_number, line_number, source) "
                        "DO NOTHING RETURNING id",
                        (p_number, surface_id, line["line_number"], line["raw_atf"]),
                    )
                    row = cur.fetchone()
                    if row is None:
                        # Line already exists (re-run / CDLI dup) — fetch its id
                        # so tokens still land idempotently.
                        row = cur.execute(
                            "SELECT id FROM text_lines WHERE p_number = %s "
                            "AND surface_id IS NOT DISTINCT FROM %s "
                            "AND column_number = 0 AND line_number = %s "
                            "AND source = 'oracc'",
                            (p_number, surface_id, line["line_number"]),
                        ).fetchone()
                        if row is None:
                            continue
                    else:
                        stats["lines"] += 1
                    line_id = row["id"] if isinstance(row, dict) else row[0]

                    for tok in line["tokens"]:
                        cur.execute(
                            "INSERT INTO tokens (line_id, position, gdl_json, lang, raw_form) "
                            "VALUES (%s, %s, %s, %s, %s) "
                            "ON CONFLICT (line_id, position) DO NOTHING",
                            (
                                line_id,
                                tok["position"],
                                json.dumps(tok["gdl"], ensure_ascii=False)
                                if tok["gdl"] is not None
                                else None,
                                tok["lang"],
                                tok["form"],
                            ),
                        )
                        if cur.rowcount:
                            stats["tokens"] += 1
                stats["tablets"] += 1
        ctx.db.commit()

    @staticmethod
    def _ensure_surfaces(
        cur, p_number: str, surface_types: list[str]
    ) -> dict[str, int]:
        surface_id_map: dict[str, int] = {}
        for surface_type in surface_types:
            cur.execute(
                "INSERT INTO surfaces (p_number, surface_type) VALUES (%s, %s) "
                "ON CONFLICT (p_number, surface_type) DO NOTHING RETURNING id",
                (p_number, surface_type),
            )
            row = cur.fetchone()
            if row is None:
                row = cur.execute(
                    "SELECT id FROM surfaces WHERE p_number = %s AND surface_type = %s",
                    (p_number, surface_type),
                ).fetchone()
            if row:
                surface_id_map[surface_type] = (
                    row["id"] if isinstance(row, dict) else row[0]
                )
        return surface_id_map

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM text_lines WHERE source = 'oracc'"
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_atf.verify", oracc_text_lines=n)
