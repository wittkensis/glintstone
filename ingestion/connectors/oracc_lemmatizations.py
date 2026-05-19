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
from ingestion.dead_letters import DeadLetterCategory

ORACC_BASE = Path("source-data/sources/ORACC")

DEAD_LETTER_FLUSH_EVERY = 5000

ORACC_PROJECTS = [
    # --- previously integrated ---
    "dcclt",
    "blms",
    "etcsri",
    "hbtin",
    "dccmt",
    "rinap",
    "saao",
    "riao",
    "ribo",
    # --- newly added top-level ---
    "adsd",
    "akklove",
    "ario",
    "armep",
    "asbp",
    "atae",
    "babcity",
    "balt",
    "borsippa",
    "btmao",
    "btto",
    "ckst",
    "cmawro",
    "ctij",
    "dsst",
    "ecut",
    "edlex",
    "eisl",
    "glass",
    "lacost",
    "nere",
    "nimrud",
    "obel",
    "obmc",
    "obta",
    "oimea",
    "pnao",
    "suhu",
    "tcma",
    "tsae",
    "urap",
    # --- ADSD subprojects ---
    "adsd/adart1",
    "adsd/adart2",
    "adsd/adart3",
    "adsd/adart5",
    "adsd/adart6",
    # --- ASBP subprojects ---
    "asbp/ninmed",
    "asbp/rlasb",
    # --- ATAE subprojects ---
    "atae/assur",
    "atae/burmarina",
    "atae/durkatlimmu",
    "atae/durszarrukin",
    "atae/guzana",
    "atae/huzirina",
    "atae/imgurenlil",
    "atae/kalhu",
    "atae/kunalia",
    "atae/mallanate",
    "atae/marqasu",
    "atae/nineveh",
    "atae/samal",
    "atae/szibaniba",
    "atae/tilbarsip",
    "atae/tuszhan",
    # --- CAMS subprojects ---
    "cams/akno",
    "cams/anzu",
    "cams/barutu",
    "cams/etana",
    "cams/gkab",
    "cams/ludlul",
    "cams/selbi",
    # --- CMAWRO subprojects ---
    "cmawro/cmawr1",
    "cmawro/cmawr2",
    "cmawro/cmawr3",
    "cmawro/maqlu",
    # --- DCCLT subprojects ---
    "dcclt/ebla",
    "dcclt/jena",
    "dcclt/nineveh",
    "dcclt/signlists",
    # --- RIBO subprojects ---
    "ribo/babylon2",
    "ribo/babylon3",
    "ribo/babylon4",
    "ribo/babylon5",
    "ribo/babylon6",
    "ribo/babylon7",
    "ribo/babylon8",
    "ribo/babylon10",
    # --- RINAP subprojects ---
    "rinap/rinap1",
    "rinap/rinap2",
    "rinap/rinap3",
    "rinap/rinap4",
    "rinap/rinap5",
    # --- SAAO subprojects ---
    "saao/aebp",
    "saao/knpp",
    "saao/saa01",
    "saao/saa02",
    "saao/saa03",
    "saao/saa04",
    "saao/saa05",
    "saao/saa06",
    "saao/saa07",
    "saao/saa08",
    "saao/saa09",
    "saao/saa10",
    "saao/saa11",
    "saao/saa12",
    "saao/saa13",
    "saao/saa14",
    "saao/saa15",
    "saao/saa16",
    "saao/saa17",
    "saao/saa18",
    "saao/saa19",
    "saao/saa20",
    "saao/saa21",
    "saao/saas2",
    # --- other subprojects ---
    "aemw/amarna",
]


def _project_base(project: str) -> Path:
    """Resolve an ORACC project slug (including 'parent/child') to its JSON directory."""
    parts = project.split("/")
    return ORACC_BASE.joinpath(*parts) / "json" / project


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
    base = _project_base(project)
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
        # Load annotation_run IDs — source_name is always "oracc/{project}"
        annotation_run_ids: dict[str, int] = {}
        for proj in ORACC_PROJECTS:
            row = ctx.db.execute(
                "SELECT id FROM annotation_runs WHERE source_name = %s",
                (f"oracc/{proj}",),
            ).fetchone()
            if row:
                annotation_run_ids[proj] = (
                    row["id"] if isinstance(row, dict) else row[0]
                )

        total_lemmas = 0

        for batch in rows:
            project = batch["project"]
            cdl_files = [Path(p) for p in batch["cdl_files"]]
            ann_run_id = annotation_run_ids.get(project, 1)

            line_cache, token_cache = _build_caches(ctx.db, project)
            proj_lemmas = 0
            proj_no_line = 0
            proj_no_token = 0
            dl_buffer: list[dict] = []

            def flush_dead_letters() -> None:
                nonlocal dl_buffer
                if not dl_buffer:
                    return
                ctx.dead_letter_many(dl_buffer)
                dl_buffer = []

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
                        line_id = None
                        if line_ids:
                            surface = lemma.get("surface")
                            line_id = (
                                line_ids.get(surface) if surface else None
                            ) or next(iter(line_ids.values()), None)
                        if not line_id:
                            proj_no_line += 1
                            dl_buffer.append(
                                _lemma_dead_letter(
                                    project, p_number, lemma, "no_line_match"
                                )
                            )
                            continue
                        token_id = token_cache.get((line_id, lemma["position"]))
                        if token_id is None:
                            proj_no_token += 1
                            dl_buffer.append(
                                _lemma_dead_letter(
                                    project, p_number, lemma, "no_token_match"
                                )
                            )
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
                if len(dl_buffer) >= DEAD_LETTER_FLUSH_EVERY:
                    flush_dead_letters()

            ctx.db.commit()
            flush_dead_letters()
            total_lemmas += proj_lemmas
            ctx.info(
                "oracc_lemmatizations.project_done",
                project=project,
                lemmas=proj_lemmas,
                no_line_match=proj_no_line,
                no_token_match=proj_no_token,
            )

        # dead_lettered count is tracked by ctx.dead_letter_many() on
        # ctx.stats already; the runner merges this LoadStats into ctx.stats,
        # so we return only `inserted` here to avoid double-counting.
        return LoadStats(inserted=total_lemmas)

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM lemmatizations").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        ctx.info("oracc_lemmatizations.verify", count=n)


_DEAD_LETTER_REASON = {
    "no_line_match": "no matching text_line for (p_number, line_number)",
    "no_token_match": "text_line found but no token at the given position",
}


def _lemma_dead_letter(
    project: str, p_number: str, lemma: dict, subcategory: str
) -> dict:
    """Build a dead-letter payload for an unmatched ORACC lemma.

    Preserves enough of the source record to triage or replay once the missing
    text_line / token shows up. source_key is unique within a run so triage
    queries can group by tablet.
    """
    line_number = lemma.get("line_number")
    position = lemma.get("position")
    return {
        "category": DeadLetterCategory.NO_MATCH.value,
        "subcategory": subcategory,
        "source_key": f"{project}/{p_number}/{line_number}/{position}",
        "payload": {
            "project": project,
            "p_number": p_number,
            "line_number": line_number,
            "surface": lemma.get("surface"),
            "position": position,
            "lang": lemma.get("lang"),
            "form": lemma.get("form"),
            "cf": lemma.get("cf"),
            "gw": lemma.get("gw"),
            "pos": lemma.get("pos"),
            "epos": lemma.get("epos"),
            "norm": lemma.get("norm"),
            "base": lemma.get("base"),
            "sense": lemma.get("sense"),
            "morph_raw": lemma.get("morph_raw"),
            "signature": lemma.get("signature"),
        },
        "reason": _DEAD_LETTER_REASON[subcategory],
    }
