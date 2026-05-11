"""ORACC CDL lemmatization importer.

Reads corpusjson/P######.json files from ORACC projects and inserts
lemmatizations matched to existing text_lines and tokens.

Depends on: atf-parser (text_lines + tokens must exist)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Iterable, Iterator

from ingestion.base import LoadStats, RunContext, SourceConnector

ORACC_BASE = Path("source-data/sources/ORACC")

ORACC_PROJECTS = [
    "dcclt",
    "blms",
    "etcsri",
    "hbtin",
    "dccmt",
    "rinap",
    "saao",
    "riao",
    "ribo",
]

PROJECT_TO_RUN = {
    "dcclt": "oracc/dcclt",
    "blms": "oracc/blms",
    "etcsri": "oracc/etcsri",
    "hbtin": "oracc/hbtin",
    "dccmt": "oracc/dccmt",
    "rinap": "oracc/rinap",
    "saao": "oracc/saao",
    "riao": "oracc/riao",
    "ribo": "oracc/ribo",
}


def _parse_inst(inst: str) -> dict:
    result: dict[str, str] = {}
    if not inst:
        return result
    m = re.match(r"^%(\w+(?:-\w+)*):", inst)
    if m:
        result["lang"] = m.group(1)
        inst = inst[m.end() :]
    m = re.match(r"^([^=]+)=", inst)
    if m:
        result["form"] = m.group(1)
        rest = inst[m.end() :]
        m2 = re.match(r"^\[([^/]+)//([^\]]+)\](\w+)", rest)
        if m2:
            result["cf"], result["gw"], result["pos"] = (
                m2.group(1),
                m2.group(2),
                m2.group(3),
            )
    return result


def _parse_surface_from_label(label: str) -> str | None:
    label = label.strip().lower()
    if label.startswith("o"):
        return "obverse"
    if label.startswith("r"):
        return "reverse"
    if label.startswith("l"):
        return "left_edge"
    if "right" in label:
        return "right_edge"
    if label.startswith("top") or label.startswith("t."):
        return "top_edge"
    if "bottom" in label or "bot" in label:
        return "bottom_edge"
    if "seal" in label:
        return "seal"
    return None


def _walk_cdl(nodes, state: dict, out_lemmas: list) -> None:
    if not isinstance(nodes, list):
        return
    for node in nodes:
        if not isinstance(node, dict):
            continue
        ntype = node.get("node")
        if ntype == "d":
            if node.get("type") == "line-start":
                line_n = node.get("n")
                if line_n is not None:
                    state["line_number"] = str(line_n)
                surf = _parse_surface_from_label(node.get("label", ""))
                if surf:
                    state["surface"] = surf
            elif node.get("type") == "surface":
                surf = _parse_surface_from_label(node.get("subtype", ""))
                if surf:
                    state["surface"] = surf
                    state["line_number"] = None
        elif ntype == "l":
            ref = node.get("ref", "")
            parts = ref.split(".")
            position = None
            if len(parts) >= 3:
                try:
                    position = int(parts[-1], 16) - 1
                except ValueError:
                    pass
            inst_data = _parse_inst(node.get("inst", ""))
            f_data = node.get("f", {})
            lemma = {
                "line_number": state.get("line_number"),
                "surface": state.get("surface"),
                "position": position,
                "lang": f_data.get("lang") or inst_data.get("lang"),
                "form": f_data.get("form") or inst_data.get("form"),
                "cf": f_data.get("cf") or inst_data.get("cf"),
                "gw": f_data.get("gw") or inst_data.get("gw"),
                "pos": f_data.get("pos") or inst_data.get("pos"),
                "epos": f_data.get("epos"),
                "norm": f_data.get("norm"),
                "morph_raw": f_data.get("morph"),
                "signature": node.get("inst"),
                "base": f_data.get("base"),
                "sense": f_data.get("sense"),
            }
            if lemma["line_number"] is not None and lemma["position"] is not None:
                out_lemmas.append(lemma)
        if "cdl" in node:
            _walk_cdl(node["cdl"], state, out_lemmas)


def _find_corpus_dirs(project: str) -> list[Path]:
    base = ORACC_BASE / project / "json" / project
    dirs = []
    if not base.exists():
        return dirs
    for root, _, filenames in os.walk(base):
        if Path(root).name == "corpusjson":
            if any(f.endswith(".json") for f in filenames):
                dirs.append(Path(root))
    return sorted(dirs)


def _build_caches(db, project: str) -> tuple[dict, dict]:
    corpus_dirs = _find_corpus_dirs(project)
    if not corpus_dirs:
        return {}, {}
    p_numbers = set()
    for cdir in corpus_dirs:
        p_numbers.update(f.stem for f in cdir.glob("P*.json"))
    if not p_numbers:
        return {}, {}

    line_cache: dict = {}
    for row in db.execute(
        "SELECT tl.p_number, tl.line_number, s.surface_type, tl.id "
        "FROM text_lines tl LEFT JOIN surfaces s ON tl.surface_id = s.id "
        "WHERE tl.p_number = ANY(%s) AND tl.is_ruling = 0 AND tl.is_blank = 0",
        (list(p_numbers),),
    ).fetchall():
        if isinstance(row, dict):
            p_num, line_num, surface_type, line_id = (
                row["p_number"],
                row["line_number"],
                row["surface_type"],
                row["id"],
            )
        else:
            p_num, line_num, surface_type, line_id = row
        key = (p_num, line_num)
        line_cache.setdefault(key, {})[surface_type or "unknown"] = line_id

    all_line_ids = [
        lid for surf_map in line_cache.values() for lid in surf_map.values()
    ]
    token_cache: dict = {}
    if all_line_ids:
        for row in db.execute(
            "SELECT id, line_id, position FROM tokens WHERE line_id = ANY(%s)",
            (all_line_ids,),
        ).fetchall():
            if isinstance(row, dict):
                token_id, line_id, position = row["id"], row["line_id"], row["position"]
            else:
                token_id, line_id, position = row
            token_cache[(line_id, position)] = token_id
    return line_cache, token_cache


class OraccLemmatizationsConnector(SourceConnector):
    id = "oracc-lemmatizations"
    display_name = "ORACC CDL Lemmatizations"
    description = "Imports lemmatizations from ORACC corpusjson CDL files into the lemmatizations table."
    kind = "annotation"
    runs_after = ["atf-parser", "annotation-runs"]
    license = "CC-BY-SA-3.0"
    upstream_url = "https://oracc.museum.upenn.edu/"

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield one dict per ORACC project (contains corpus_dirs for that project)."""
        for project in ORACC_PROJECTS:
            corpus_dirs = _find_corpus_dirs(project)
            if not corpus_dirs:
                continue
            cdl_files = []
            for cdir in corpus_dirs:
                cdl_files.extend(sorted(cdir.glob("P*.json")))
            if cdl_files:
                yield {"project": project, "cdl_files": [str(p) for p in cdl_files]}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # Load annotation_run IDs
        annotation_run_ids: dict[str, int] = {}
        for proj, source_name in PROJECT_TO_RUN.items():
            row = ctx.db.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s", (source_name,)
            ).fetchone()
            if row:
                annotation_run_ids[proj] = (
                    row["id"] if isinstance(row, dict) else row[0]
                )

        total_lemmas = 0
        total_no_match = 0

        for batch in rows:
            project = batch["project"]
            cdl_files = [Path(p) for p in batch["cdl_files"]]
            ann_run_id = annotation_run_ids.get(project, 1)

            line_cache, token_cache = _build_caches(ctx.db, project)
            proj_lemmas = 0
            proj_no_line = 0
            proj_no_token = 0

            for i, cdl_file in enumerate(cdl_files):
                try:
                    with open(cdl_file, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    continue

                p_number = data.get("textid", "")
                if not p_number:
                    continue

                lemmas: list[dict] = []
                _walk_cdl(
                    data.get("cdl", []), {"line_number": None, "surface": None}, lemmas
                )

                with ctx.db.cursor() as cur:
                    for lemma in lemmas:
                        line_ids = line_cache.get((p_number, lemma["line_number"]))
                        if not line_ids:
                            proj_no_line += 1
                            continue
                        surface = lemma.get("surface")
                        line_id = (line_ids.get(surface) if surface else None) or next(
                            iter(line_ids.values()), None
                        )
                        if not line_id:
                            proj_no_line += 1
                            continue
                        token_id = token_cache.get((line_id, lemma["position"]))
                        if token_id is None:
                            proj_no_token += 1
                            continue
                        cur.execute(
                            "INSERT INTO lemmatizations "
                            "(token_id, citation_form, guide_word, sense, pos, epos, "
                            "norm, base, signature, morph_raw, annotation_run_id, confidence, language) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1.0, %s) "
                            "ON CONFLICT DO NOTHING",
                            (
                                token_id,
                                lemma.get("cf"),
                                lemma.get("gw"),
                                lemma.get("sense"),
                                lemma.get("pos"),
                                lemma.get("epos"),
                                lemma.get("norm"),
                                lemma.get("base"),
                                lemma.get("signature"),
                                lemma.get("morph_raw"),
                                ann_run_id,
                                lemma.get("lang"),
                            ),
                        )
                        proj_lemmas += 1

                if (i + 1) % 200 == 0:
                    ctx.db.commit()

            ctx.db.commit()
            total_lemmas += proj_lemmas
            total_no_match += proj_no_line + proj_no_token
            ctx.info(
                "oracc_lemmatizations.project_done",
                project=project,
                lemmas=proj_lemmas,
                no_line_match=proj_no_line,
                no_token_match=proj_no_token,
            )

        return LoadStats(inserted=total_lemmas, dead_lettered=total_no_match)

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM lemmatizations").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_lemmatizations.verify", count=n)
