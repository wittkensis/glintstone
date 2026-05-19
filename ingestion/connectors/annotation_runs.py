"""Annotation run seeder — registers canonical source records for downstream FKs.

Every import row carries an annotation_run_id FK. This connector creates the
13 canonical records so downstream connectors can reference them by source_name.
Must run before any connector that writes annotation_run_id values.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, RunContext, SourceConnector
from ingestion.loader import upsert_batch

# (source_name, source_type, method, corpus_scope, notes)
ANNOTATION_RUNS = [
    # ── Non-ORACC sources ────────────────────────────────────────────────────
    (
        "cdli-catalog",
        "import",
        "import",
        "353,283 artifacts",
        "CDLI bulk data dump (Aug 2022). cdli_cat.csv. CC0.",
    ),
    (
        "cdli-atf",
        "import",
        "import",
        "CDLI ATF transliterations",
        "CDLI bulk ATF dump (Aug 2022). cdliatf_unblocked.atf. CC0.",
    ),
    (
        "compvis",
        "import",
        "ML_model",
        "81 tablets, ~8,100 sign annotations",
        "Heidelberg CompVis sign detection annotations. CC BY 4.0.",
    ),
    (
        "ebl-annotations",
        "import",
        "import",
        "eBL sign annotation training data",
        "Electronic Babylonian Library annotation corpus. CC BY 4.0.",
    ),
    # ── ORACC top-level projects (original) ──────────────────────────────────
    (
        "oracc/blms",
        "import",
        "import",
        "Bilinguals in Late Mesopotamian Scholarship",
        "ORACC BLMS project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams",
        "import",
        "import",
        "Corpus of Ancient Mesopotamian Scholarship",
        "ORACC CAMS project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/dcclt",
        "import",
        "import",
        "Digital Corpus of Cuneiform Lexical Texts",
        "ORACC DCCLT project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/dccmt",
        "import",
        "import",
        "Digital Corpus of Cuneiform Mathematical Texts",
        "ORACC DCCMT project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/epsd2",
        "import",
        "import",
        "Electronic PSD 2",
        "ORACC ePSD2 Sumerian dictionary corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/etcsl",
        "import",
        "import",
        "Electronic Text Corpus of Sumerian Literature",
        "ORACC ETCSL project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/etcsri",
        "import",
        "import",
        "Electronic Text Corpus of Sumerian Royal Inscriptions",
        "ORACC ETCSRI project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/hbtin",
        "import",
        "import",
        "Hellenistic Babylonia: Texts, Iconography, Names",
        "ORACC HBTIN project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/amgg",
        "import",
        "import",
        "Ancient Mesopotamian Gods and Goddesses",
        "ORACC AMGG project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/riao",
        "import",
        "import",
        "Royal Inscriptions of Assyria Online",
        "ORACC RIAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/ribo",
        "import",
        "import",
        "Royal Inscriptions of Babylonia online",
        "ORACC RIBo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rime",
        "import",
        "import",
        "Royal Inscriptions of Mesopotamia Early Periods",
        "ORACC RIME project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rimanum",
        "import",
        "import",
        "Rīm-Anum: The House of Prisoners",
        "ORACC Rīm-Anum project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap",
        "import",
        "import",
        "Royal Inscriptions of the Neo-Assyrian Period",
        "ORACC RINAP project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao",
        "import",
        "import",
        "State Archives of Assyria Online",
        "ORACC SAAo project corpus. CC BY-SA 3.0.",
    ),
    # ── ORACC top-level projects (newly added) ───────────────────────────────
    (
        "oracc/adsd",
        "import",
        "import",
        "Astronomical Diaries Digital",
        "ORACC ADsD project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/akklove",
        "import",
        "import",
        "Akkadian Love Literature",
        "ORACC AkkLove project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/ario",
        "import",
        "import",
        "Achaemenid Royal Inscriptions online",
        "ORACC ARIo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/armep",
        "import",
        "import",
        "Ancient Records of Middle Eastern Polities",
        "ORACC ARMEP project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/asbp",
        "import",
        "import",
        "Ashurbanipal Library Project",
        "ORACC AsbP project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/atae",
        "import",
        "import",
        "Archival Texts of the Assyrian Empire",
        "ORACC ATAE project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/babcity",
        "import",
        "import",
        "Babylonian Texts Concerning the Urban Landscape",
        "ORACC BabCity project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/balt",
        "import",
        "import",
        "Babylonian Administrative and Legal Texts",
        "ORACC BALT project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/borsippa",
        "import",
        "import",
        "Archival Texts of the Priests of Borsippa",
        "ORACC Borsippa project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/btmao",
        "import",
        "import",
        "Babylonian Temples and Monumental Architecture online",
        "ORACC BTMAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/btto",
        "import",
        "import",
        "Babylonian Topographical Texts Online",
        "ORACC BTTo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/ckst",
        "import",
        "import",
        "Corpus of Kassite Sumerian Texts",
        "ORACC CKST project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cmawro",
        "import",
        "import",
        "Corpus of Mesopotamian Anti-witchcraft Rituals",
        "ORACC CMAwRo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/ctij",
        "import",
        "import",
        "Cuneiform Texts Mentioning Israelites, Judeans, and Others",
        "ORACC CTIJ project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/dsst",
        "import",
        "import",
        "Datenbank sumerischer Streitliteratur",
        "ORACC DSSt project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/ecut",
        "import",
        "import",
        "Electronic Corpus of Urartian Texts",
        "ORACC eCUT project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/edlex",
        "import",
        "import",
        "Early Dynastic Lexical Texts",
        "ORACC EDLEX project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/eisl",
        "import",
        "import",
        "Electronic ISL: First Millennium Emesal Liturgies",
        "ORACC eISL project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/glass",
        "import",
        "import",
        "Corpus of Glass Technological Texts",
        "ORACC Glass project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/lacost",
        "import",
        "import",
        "Law and Order: Cuneiform Online Sustainable Tool",
        "ORACC LaOCOST project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/nere",
        "import",
        "import",
        "Near Eastern Royal Epics",
        "ORACC NERE project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/nimrud",
        "import",
        "import",
        "Nimrud: Materialities of Assyrian Knowledge Production",
        "ORACC Nimrud project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/obel",
        "import",
        "import",
        "Old Babylonian Emesal Liturgies",
        "ORACC obel project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/obmc",
        "import",
        "import",
        "Old Babylonian Model Contracts",
        "ORACC OBMC project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/obta",
        "import",
        "import",
        "Old Babylonian Tabular Accounts",
        "ORACC OBTA project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/oimea",
        "import",
        "import",
        "Official Inscriptions of the Middle East in Antiquity",
        "ORACC OIMEA project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/pnao",
        "import",
        "import",
        "Prosopography of the Neo-Assyrian Empire online",
        "ORACC PNAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/suhu",
        "import",
        "import",
        "Inscriptions of Suhu online",
        "ORACC Suhu project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/tcma",
        "import",
        "import",
        "Archival Texts of the Middle Assyrian Period",
        "ORACC TCMA project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/tsae",
        "import",
        "import",
        "Textual Sources of the Assyrian Empire",
        "ORACC TSAE project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/urap",
        "import",
        "import",
        "Ur Regional Archaeology Project",
        "ORACC URAP project corpus. CC BY-SA 3.0.",
    ),
    # ── ORACC subprojects (CAMS) ─────────────────────────────────────────────
    (
        "oracc/cams/gkab",
        "import",
        "import",
        "CAMS Geography of Knowledge across the Babylonian World",
        "ORACC CAMS/GKAB subproject corpus (Frahm et al.). CC BY-SA 3.0.",
    ),
    (
        "oracc/cams/anzu",
        "import",
        "import",
        "CAMS/Anzu Epic",
        "ORACC CAMS/Anzu subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams/barutu",
        "import",
        "import",
        "CAMS/Barutu Divination Series",
        "ORACC CAMS/Barutu subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams/etana",
        "import",
        "import",
        "CAMS/Etana Epic",
        "ORACC CAMS/Etana subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams/ludlul",
        "import",
        "import",
        "CAMS/Ludlul bel nemeqi (Poem of the Righteous Sufferer)",
        "ORACC CAMS/Ludlul subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams/selbi",
        "import",
        "import",
        "CAMS/Seleucid Building Inscriptions",
        "ORACC CAMS/SelBI subproject corpus. CC BY-SA 3.0.",
    ),
    # ── ORACC subprojects (CMAWRO anti-witchcraft) ───────────────────────────
    (
        "oracc/cmawro/maqlu",
        "import",
        "import",
        "Maqlû Anti-witchcraft Series",
        "ORACC CMAwRo/Maqlu subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cmawro/cmawr1",
        "import",
        "import",
        "Corpus of Mesopotamian Anti-witchcraft Rituals vol. 1",
        "ORACC CMAwRo 1 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cmawro/cmawr2",
        "import",
        "import",
        "Corpus of Mesopotamian Anti-witchcraft Rituals vol. 2",
        "ORACC CMAwRo 2 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cmawro/cmawr3",
        "import",
        "import",
        "Corpus of Mesopotamian Anti-witchcraft Rituals vol. 3",
        "ORACC CMAwRo 3 subproject corpus. CC BY-SA 3.0.",
    ),
    # ── ORACC subprojects (ASBP Ashurbanipal Library) ────────────────────────
    (
        "oracc/asbp/ninmed",
        "import",
        "import",
        "Nineveh Medical Encyclopaedia",
        "ORACC AsbP/NinMed subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/asbp/rlasb",
        "import",
        "import",
        "Reading the Library of Ashurbanipal",
        "ORACC AsbP/RLAsb subproject corpus. CC BY-SA 3.0.",
    ),
    # ── ORACC subprojects (RINAP by king) ────────────────────────────────────
    (
        "oracc/rinap/rinap1",
        "import",
        "import",
        "RINAP 1: Tiglath-pileser III and Shalmaneser V",
        "ORACC RINAP 1 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap/rinap2",
        "import",
        "import",
        "RINAP 2: Sargon II",
        "ORACC RINAP 2 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap/rinap3",
        "import",
        "import",
        "RINAP 3: Sennacherib",
        "ORACC RINAP 3 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap/rinap4",
        "import",
        "import",
        "RINAP 4: Esarhaddon",
        "ORACC RINAP 4 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap/rinap5",
        "import",
        "import",
        "RINAP 5: Ashurbanipal and Successors",
        "ORACC RINAP 5 subproject corpus. CC BY-SA 3.0.",
    ),
    # ── ORACC subprojects (SAA volumes) ──────────────────────────────────────
    (
        "oracc/saao/saa01",
        "import",
        "import",
        "SAA 1: Correspondence of Sargon II, Part I",
        "ORACC SAAo/SAA01 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa02",
        "import",
        "import",
        "SAA 2: Neo-Assyrian Treaties and Loyalty Oaths",
        "ORACC SAAo/SAA02 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa03",
        "import",
        "import",
        "SAA 3: Court Poetry and Literary Miscellanea",
        "ORACC SAAo/SAA03 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa04",
        "import",
        "import",
        "SAA 4: Queries to the Sungod",
        "ORACC SAAo/SAA04 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa05",
        "import",
        "import",
        "SAA 5: Correspondence of Sargon II, Part II",
        "ORACC SAAo/SAA05 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa06",
        "import",
        "import",
        "SAA 6: Legal Transactions of the Royal Court, Part I",
        "ORACC SAAo/SAA06 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa07",
        "import",
        "import",
        "SAA 7: Imperial Administrative Records, Part I",
        "ORACC SAAo/SAA07 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa08",
        "import",
        "import",
        "SAA 8: Astrological Reports to Assyrian Kings",
        "ORACC SAAo/SAA08 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa09",
        "import",
        "import",
        "SAA 9: Assyrian Prophecies",
        "ORACC SAAo/SAA09 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa10",
        "import",
        "import",
        "SAA 10: Letters from Assyrian and Babylonian Scholars",
        "ORACC SAAo/SAA10 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa11",
        "import",
        "import",
        "SAA 11: Imperial Administrative Records, Part II",
        "ORACC SAAo/SAA11 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa12",
        "import",
        "import",
        "SAA 12: Grants, Decrees and Gifts",
        "ORACC SAAo/SAA12 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa13",
        "import",
        "import",
        "SAA 13: Letters from Assyrian and Babylonian Priests",
        "ORACC SAAo/SAA13 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa14",
        "import",
        "import",
        "SAA 14: Legal Transactions of the Royal Court, Part II",
        "ORACC SAAo/SAA14 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa15",
        "import",
        "import",
        "SAA 15: Correspondence of Sargon II, Part III",
        "ORACC SAAo/SAA15 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa16",
        "import",
        "import",
        "SAA 16: Political Correspondence of Esarhaddon",
        "ORACC SAAo/SAA16 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa17",
        "import",
        "import",
        "SAA 17: Neo-Babylonian Correspondence of Sargon and Sennacherib",
        "ORACC SAAo/SAA17 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa18",
        "import",
        "import",
        "SAA 18: Babylonian Correspondence of Esarhaddon",
        "ORACC SAAo/SAA18 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa19",
        "import",
        "import",
        "SAA 19: Correspondence of Tiglath-Pileser III and Sargon II from Calah",
        "ORACC SAAo/SAA19 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa20",
        "import",
        "import",
        "SAA 20: Assyrian Royal Rituals and Cultic Texts",
        "ORACC SAAo/SAA20 subproject corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao/saa21",
        "import",
        "import",
        "SAA 21: Correspondence of Assurbanipal, Part I",
        "ORACC SAAo/SAA21 subproject corpus. CC BY-SA 3.0.",
    ),
]


class AnnotationRunsConnector(SourceConnector):
    id = "annotation-runs"
    display_name = "Annotation Runs (Source Registry)"
    description = "Seeds canonical annotation_run records so downstream connectors can reference them by source_name."
    kind = "lookup"
    runs_after = ["lookup-tables"]

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        for source_name, source_type, method, corpus_scope, notes in ANNOTATION_RUNS:
            yield {
                "source_name": source_name,
                "source_type": source_type,
                "method": method,
                "corpus_scope": corpus_scope,
                "notes": notes,
            }

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="annotation_runs",
            rows=rows,
            unique_key=["source_name"],
            policy=ConflictPolicy.SKIP,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM annotation_runs").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        expected = len(ANNOTATION_RUNS)
        if n < expected:
            raise AssertionError(f"annotation_runs has {n} rows; expected ≥ {expected}")
        ctx.info("annotation_runs.verify", count=n, expected=expected)
