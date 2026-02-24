#!/usr/bin/env python3
"""
Step 1: Seed normalization lookup tables from CDLI source data.

Reads distinct values from cdli_cat.csv and populates:
  - period_canon      (+ group_name, sort_order for filter grouping)
  - language_map
  - genre_canon
  - provenience_canon  (+ region, subregion, sort_order for filter grouping)
  - surface_canon

All inserts are ON CONFLICT DO NOTHING — safe to re-run.
Grouping columns updated via separate UPDATE pass (idempotent).

Usage:
    python 01_seed_lookup_tables.py [--dry-run]
"""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg

from core.config import get_settings

CDLI_CSV = Path(__file__).resolve().parents[1] / "sources/CDLI/metadata/cdli_cat.csv"


# ─────────────────────────────────────────────────────────
# LANGUAGE MAP  (CDLI label → ORACC ISO code + family)
# ─────────────────────────────────────────────────────────
LANGUAGE_MAP = [
    # cdli_name, oracc_code, full_name, family
    ("Sumerian", "sux", "Sumerian", "sumerian"),
    ("Sumerian ?", "sux", "Sumerian (uncertain)", "sumerian"),
    ("Akkadian", "akk", "Akkadian", "semitic"),
    ("Akkadian ?", "akk", "Akkadian (uncertain)", "semitic"),
    ("Akkadian (pseudo)", "akk", "Pseudo-Akkadian", "semitic"),
    ("Akkadian, Aramaic", "akk", "Akkadian and Aramaic", "semitic"),
    ("Akkadian, Aramaic?", "akk", "Akkadian and Aramaic (uncertain)", "semitic"),
    ("Eblaite", "xeb", "Eblaite", "semitic"),
    ("Ugaritic", "uga", "Ugaritic", "semitic"),
    ("Aramaic", "arc", "Aramaic", "semitic"),
    ("Aramaic ?", "arc", "Aramaic (uncertain)", "semitic"),
    ("Hebrew", "hbo", "Hebrew", "semitic"),
    ("Hebrew ?", "hbo", "Hebrew (uncertain)", "semitic"),
    ("Phoenician", "phn", "Phoenician", "semitic"),
    ("Sabaean", "xsa", "Sabaean", "semitic"),
    ("Qatabanian", "xqt", "Qatabanian", "semitic"),
    ("Arabic", "arb", "Arabic", "semitic"),
    ("Mandaic", "mid", "Mandaic", "semitic"),
    ("Syriac", "syc", "Syriac", "semitic"),
    ("Hittite", "hit", "Hittite", "hittite"),
    ("Hittite ?", "hit", "Hittite (uncertain)", "hittite"),
    ("Luwian", "xlu", "Luwian", "hittite"),
    ("Hattic", "xht", "Hattic", "other"),
    ("Elamite", "elx", "Elamite", "elamite"),
    ("Elamite Egyptian", "elx", "Elamite/Egyptian", "elamite"),
    ("Persian", "peo", "Old Persian", "other"),
    ("Persian,", "peo", "Old Persian", "other"),
    ("Persian, Babylonian", "peo", "Old Persian and Babylonian", "other"),
    ("Persian, Elamite", "peo", "Old Persian and Elamite", "other"),
    (
        "Persian, Elamite, Babylonian",
        "peo",
        "Old Persian, Elamite, and Babylonian",
        "other",
    ),
    ("Egyptian", "egy", "Egyptian", "other"),
    ("Egyptian ?", "egy", "Egyptian (uncertain)", "other"),
    ("Greek", "grc", "Greek", "other"),
    ("Hurrian", "hur", "Hurrian", "hurrian"),
    ("Hurrian ?", "hur", "Hurrian (uncertain)", "hurrian"),
    ("Urartian", "xur", "Urartian", "other"),
    ("Sumerian, Akkadian", "sux", "Sumerian and Akkadian", "sumerian"),
    ("undetermined", "und", "Undetermined", "other"),
    ("undetermined (pseudo)", "und", "Pseudo-inscription", "other"),
    ("no linguistic content", "none", "No linguistic content", "other"),
    ("uncertain", "und", "Uncertain", "other"),
    ("unclear", "und", "Unclear", "other"),
    ("uninscribed", "none", "Uninscribed", "other"),
    ("clay", "none", "Clay (no text)", "other"),
]

# ─────────────────────────────────────────────────────────
# SURFACE CANON  (ATF markers → canonical names)
# ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────
# CANONICAL GENRES  (deduplicated atomic genre names for junction table)
# ─────────────────────────────────────────────────────────
CANONICAL_GENRES = [
    "Administrative",
    "Astronomical",
    "Fake (Modern)",
    "Historical",
    "Legal",
    "Letter",
    "Lexical",
    "Literary",
    "Mathematical",
    "Medical",
    "Omen",
    "Other",
    "Prayer/Incantation",
    "Private/Votive",
    "Ritual",
    "Royal/Monumental",
    "School",
    "Scientific",
    "Votive",
]

# Map raw genre parts (lowercased) to canonical names
GENRE_NORMALIZE: dict[str, str] = {
    "administrative": "Administrative",
    "administative": "Administrative",  # typo in source
    "administrative record": "Administrative",
    "astronomical": "Astronomical",
    "astronomical, omen": "Astronomical",  # primary = Astronomical
    "fake (modern)": "Fake (Modern)",
    "historical": "Historical",
    "legal": "Legal",
    "letter": "Letter",
    "lexical": "Lexical",
    "literary": "Literary",
    "mathematical": "Mathematical",
    "medical": "Medical",
    "omen": "Omen",
    "omens": "Omen",
    "other": "Other",
    "other (see subgenre)": "Other",
    "pottery (seal)": "Other",
    "prayer/hymn": "Prayer/Incantation",
    "prayer/incantation": "Prayer/Incantation",
    "private/votive": "Private/Votive",
    "ritual": "Ritual",
    "royal/monumental": "Royal/Monumental",
    "royal/votive": "Royal/Monumental",  # primary; Votive added as secondary
    "royal inscription": "Royal/Monumental",
    "school": "School",
    "scientific": "Scientific",
    "votive": "Votive",
}

# ─────────────────────────────────────────────────────────
# CANONICAL LANGUAGES  (atomic language names for junction table)
# ─────────────────────────────────────────────────────────
CANONICAL_LANGUAGES = [
    # (name, oracc_code, family)
    ("Sumerian", "sux", "sumerian"),
    ("Akkadian", "akk", "semitic"),
    ("Eblaite", "xeb", "semitic"),
    ("Ugaritic", "uga", "semitic"),
    ("Aramaic", "arc", "semitic"),
    ("Hebrew", "hbo", "semitic"),
    ("Phoenician", "phn", "semitic"),
    ("Sabaean", "xsa", "semitic"),
    ("Qatabanian", "xqt", "semitic"),
    ("Arabic", "arb", "semitic"),
    ("Mandaic", "mid", "semitic"),
    ("Syriac", "syc", "semitic"),
    ("Hittite", "hit", "hittite"),
    ("Luwian", "xlu", "hittite"),
    ("Hattic", "xht", "other"),
    ("Elamite", "elx", "elamite"),
    ("Persian", "peo", "other"),
    ("Egyptian", "egy", "other"),
    ("Greek", "grc", "other"),
    ("Hurrian", "hur", "hurrian"),
    ("Urartian", "xur", "other"),
]

# Map raw language parts (title-cased) to canonical names
LANG_NORMALIZE: dict[str, str] = {
    "Sumerian": "Sumerian",
    "Akkadian": "Akkadian",
    "Babylonian": "Akkadian",  # CDLI uses "Babylonian" as Akkadian variant
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

# Language values that indicate no real language data (skip junction rows)
LANG_SKIP = {
    "undetermined",
    "uncertain",
    "unclear",
    "no linguistic content",
    "uninscribed",
    "clay",
}


SURFACE_CANON = [
    ("@obverse", "obverse"),
    ("@reverse", "reverse"),
    ("@left", "left_edge"),
    ("@right", "right_edge"),
    ("@top", "top_edge"),
    ("@bottom", "bottom_edge"),
    ("@seal", "seal"),
    ("@edge", "unknown"),
    ("@face", "unknown"),
    ("@a", "obverse"),
    ("@b", "reverse"),
    ("Obv", "obverse"),
    ("Rev", "reverse"),
    ("obverse", "obverse"),
    ("reverse", "reverse"),
    ("left edge", "left_edge"),
    ("right edge", "right_edge"),
    ("top edge", "top_edge"),
    ("bottom edge", "bottom_edge"),
    ("", "unknown"),
]


# ─────────────────────────────────────────────────────────
# PERIOD GROUPS  (canonical_period → group + sort + date range)
# Based on standard Assyriological periodization (Middle Chronology)
# Dates: positive = BCE, negative = CE
# Tuples: (canonical, sort_order, date_start_bce, date_end_bce)
# ─────────────────────────────────────────────────────────
PERIOD_GROUPS: dict[str, list[tuple[str, int, int | None, int | None]]] = {
    "Proto-Literate": [
        ("Pre-Uruk V", 5, 8500, 3500),
        ("Uruk V", 10, 3500, 3350),
        ("Uruk IV", 20, 3350, 3200),
        ("Uruk III", 30, 3200, 3000),
        ("Uruk III-II", 35, 3200, 2900),
        ("Proto-Elamite", 40, 3100, 2900),
        ("Linear Elamite", 42, 2300, 2200),
        ("Jemdet Nasr", 45, 3100, 2900),
    ],
    "Early Dynastic": [
        ("ED I-II", 50, 2900, 2700),
        ("Early Dynastic I-II", 51, 2900, 2700),
        ("ED IIIa", 60, 2600, 2500),
        ("Fara", 65, 2600, 2500),
        ("ED IIIb", 70, 2500, 2340),
        ("Ebla", 75, 2350, 2250),
    ],
    "Sargonic": [
        ("Old Akkadian", 80, 2340, 2200),
        ("Lagash II", 90, 2200, 2100),
    ],
    "Ur III": [
        ("Ur III", 100, 2100, 2000),
    ],
    "Old Babylonian": [
        ("Isin-Larsa", 105, 2000, 1900),
        ("Early Old Babylonian", 110, 2000, 1900),
        ("Old Babylonian", 120, 1900, 1600),
        ("Old Assyrian", 125, 1950, 1850),
        ("Old Elamite", 127, 2700, 1500),
    ],
    "Middle Period": [
        ("Middle Babylonian", 130, 1400, 1100),
        ("Middle Assyrian", 140, 1400, 1000),
        ("Middle Hittite", 143, 1500, 1100),
        ("Middle Elamite", 145, 1300, 1000),
    ],
    "First Millennium": [
        ("Early Neo-Babylonian", 155, 1150, 730),
        ("Neo-Assyrian", 150, 911, 612),
        ("Neo-Babylonian", 160, 626, 539),
        ("Neo-Elamite", 165, 770, 539),
    ],
    "Late / Imperial": [
        ("Achaemenid", 170, 550, 330),
        ("Old Persian", 175, 550, 330),
        ("Hellenistic", 180, 323, 63),
        ("Parthian", 190, 247, -224),
        ("Sassanian", 195, -224, -651),
        ("Islamic", 198, -651, None),
    ],
    "Other": [
        ("uncertain", 900, None, None),
        ("fake (modern)", 910, None, None),
        ("fake (ancient)", 915, None, None),
        ("copy (modern)", 920, None, None),
        ("modern", 920, None, None),
        ("Egyptian 0", 901, 3300, 3000),
        ("Harappan", 902, 2600, 1900),
    ],
}

# Invert: canonical → (group_name, sort_order)
_PERIOD_LOOKUP: dict[str, tuple[str, int]] = {}
_PERIOD_DATES: dict[str, tuple[int | None, int | None]] = {}
for _grp, _members in PERIOD_GROUPS.items():
    for _canonical, _order, _ds, _de in _members:
        _PERIOD_LOOKUP[_canonical] = (_grp, _order)
        _PERIOD_DATES[_canonical] = (_ds, _de)

# ─────────────────────────────────────────────────────────
# PERIOD ALIASES  (compound/variant canonicals → primary canonical)
# Artifacts with these period_normalized values get remapped
# ─────────────────────────────────────────────────────────
PERIOD_ALIASES: dict[str, str] = {
    "Parthian (247 BC-224 AD)": "Parthian",
    "Parthian (247 BC - 224 AD)": "Parthian",
    "Neo-Babylonian (ca. 626-539 BC) or Achaemenid": "Neo-Babylonian",
    "Neo-Babylonian (ca. 626-539 BC).": "Neo-Babylonian",
    "Early Dynastic IIIA (c. 2700-2500 BC)": "ED IIIa",
    "Middle Babylonian (ca. 1400-1100 BC))": "Middle Babylonian",
    "ED I-II (ca. 2900-2700 BC), Old Babylonian (ca. 1900-1600 BC)": "ED I-II",
    "Old Akkadian (ca. 2340-2200 BC); Ur III": "Old Akkadian",
    "Old Akkadian (ca. 2340-2200 BC); Middle Elamite": "Old Akkadian",
    "Ur III (ca. 2100-2000 BC); Early Old Babylonian": "Ur III",
    "ED IIIb (ca. 2500-2340 BC) or Old Babylonian": "ED IIIb",
    "ED IIIb (ca. 2500-2340 BC); Ur III": "ED IIIb",
    "ED IIIb (ca. 2500-2340 BC); Old Akkadian": "ED IIIb",
    "ED IIIa (ca. 2600-2500 BC); Old Babylonian": "ED IIIa",
    "Uruk III (ca. 3200-3000 BC) - Early Dynastic I-II": "Uruk III",
}


# ─────────────────────────────────────────────────────────
# PROVENIENCE REGIONS  (ancient_name → region, subregion)
# Based on standard ANE geographic divisions
# ─────────────────────────────────────────────────────────
# Key: (region, subregion) → list of ancient_name prefixes to match
PROVENIENCE_REGIONS: dict[tuple[str, str], list[str]] = {
    ("South Mesopotamia", "Sumer"): [
        "Ur",
        "Uruk",
        "Lagash",
        "Girsu",
        "Umma",
        "Eridu",
        "Larsa",
        "Bad-tibira",
        "Shuruppak",
        "Zabalam",
        "Tell al-Hiba",
        "Nina",
        "Kuara",
        "Guabba",
    ],
    ("South Mesopotamia", "Akkad"): [
        "Babylon",
        "Sippar",
        "Kish",
        "Borsippa",
        "Dilbat",
        "Kutha",
        "Marad",
        "Jemdet Nasr",
        "Seleucia",
        "Tell ed-Der",
    ],
    ("South Mesopotamia", "Central"): [
        "Nippur",
        "Isin",
        "Drehem",
        "Puzrish-Dagan",
        "Adab",
        "Tummal",
        "Surghul",
    ],
    ("South Mesopotamia", "Sealand"): [
        "Tell Khaiber",
        "Mashkan-shapir",
    ],
    ("North Mesopotamia", "Assyria"): [
        "Assur",
        "Nineveh",
        "Kalhu",
        "Nimrud",
        "Sultantepe",
        "Huzirina",
        "Dur-Sharrukin",
        "Khorsabad",
        "Kar-Tukulti-Ninurta",
        "Tell al-Rimah",
        "Tell Billa",
    ],
    ("North Mesopotamia", "Upper Mesopotamia"): [
        "Tell Brak",
        "Chagar Bazar",
        "Tell Mozan",
        "Tell Leilan",
        "Tell Taya",
        "Nuzi",
        "Gasur",
        "Yorgan Tepe",
        "Kirkuk",
        "Arrapha",
    ],
    ("Elam / Iran", ""): [
        "Susa",
        "Anshan",
        "Tall-i Malyan",
        "Haft Tepe",
        "Kabnak",
        "Choga Zanbil",
        "Dur Untash",
        "Tepe Sialk",
        "Tepe Yahya",
        "Godin Tepe",
        "Persepolis",
        "Pasargadae",
        "Behist",
    ],
    ("Anatolia", ""): [
        "Hattusha",
        "Kanesh",
        "Bogazk",
        "Kultepe",
        "Alalakh",
        "Tarsus",
        "Masat",
    ],
    ("Levant / Syria", ""): [
        "Mari",
        "Ebla",
        "Ugarit",
        "Emar",
        "Terqa",
        "Tuttul",
        "Aleppo",
        "Qatna",
        "Ras Shamra",
        "Meskene",
        "Byblos",
        "Megiddo",
        "Hazor",
        "Lachish",
        "Amarna",
        "Tell el-Amarna",
    ],
    ("East Periphery", ""): [
        "Diyala",
        "Eshnunna",
        "Tell Asmar",
        "Khafaje",
        "Tell Agrab",
        "Ishchali",
        "Tutub",
        "Hamrin",
    ],
    ("West Periphery", ""): [
        "Dilmun",
        "Bahrain",
        "Failaka",
    ],
}

# ─────────────────────────────────────────────────────────
# PROVENIENCE DIRECT  (exact Unicode ancient_name → region)
# For names with diacriticals that prefix matching misses
# ─────────────────────────────────────────────────────────
PROVENIENCE_DIRECT: dict[str, tuple[str, str]] = {
    # South Mesopotamia > Central
    "Puzriš-Dagan": ("South Mesopotamia", "Central"),
    "Irisagrig": ("South Mesopotamia", "Central"),
    "Irisaĝrig": ("South Mesopotamia", "Central"),
    "Du-Enlila": ("South Mesopotamia", "Central"),
    "Kesh": ("South Mesopotamia", "Central"),
    "Sagub": ("South Mesopotamia", "Central"),
    "Gišša": ("South Mesopotamia", "Central"),
    "Gišši": ("South Mesopotamia", "Central"),
    "Maškan-šapir": ("South Mesopotamia", "Central"),
    # South Mesopotamia > Akkad
    "Bābili": ("South Mesopotamia", "Akkad"),
    "Ešnunna": ("South Mesopotamia", "Akkad"),
    "Šaduppum": ("South Mesopotamia", "Akkad"),
    "Nerebtum": ("South Mesopotamia", "Akkad"),
    "Dūr-Abī-ēšuḫ": ("South Mesopotamia", "Akkad"),
    "Lagaba": ("South Mesopotamia", "Akkad"),
    "Kutalla": ("South Mesopotamia", "Akkad"),
    "Sirara": ("South Mesopotamia", "Akkad"),
    "Ālu-ša-Našar": ("South Mesopotamia", "Akkad"),
    "Ma'allanate": ("South Mesopotamia", "Akkad"),
    "Kazallu": ("South Mesopotamia", "Akkad"),
    "Der": ("South Mesopotamia", "Akkad"),
    "Upi": ("South Mesopotamia", "Akkad"),
    "Malgium (Tell Yassir)": ("South Mesopotamia", "Akkad"),
    "Āl-šarri": ("South Mesopotamia", "Akkad"),
    "Dur-Kurigalzu": ("South Mesopotamia", "Akkad"),
    "Bit-šar-Babili": ("South Mesopotamia", "Akkad"),
    "Bīt-Abī-rām": ("South Mesopotamia", "Akkad"),
    "Bīt-Bāba-ēriš": ("South Mesopotamia", "Akkad"),
    "Bīt-Naʾinnašu": ("South Mesopotamia", "Akkad"),
    "Bīt-Dibušiti": ("South Mesopotamia", "Akkad"),
    "Bīt-Ṭāb-Bēl": ("South Mesopotamia", "Akkad"),
    "Bīt-Šinqā": ("South Mesopotamia", "Akkad"),
    "Bīt-ham...": ("South Mesopotamia", "Akkad"),
    "Bīt-Našar": ("South Mesopotamia", "Akkad"),
    "Ālu-ša-Ṭūb-Yāma": ("South Mesopotamia", "Akkad"),
    "Alu-šabtu": ("South Mesopotamia", "Akkad"),
    "Alu-ša-šuma-ukin": ("South Mesopotamia", "Akkad"),
    "Alu-eššu": ("South Mesopotamia", "Akkad"),
    "Alu-binatu": ("South Mesopotamia", "Akkad"),
    "Alu-ša-BAD-MAH-AN": ("South Mesopotamia", "Akkad"),
    "Āl-šarri-ša-qašti-eššeti": ("South Mesopotamia", "Akkad"),
    "Bit-ali-...": ("South Mesopotamia", "Akkad"),
    "Bit-zerija": ("South Mesopotamia", "Akkad"),
    "Bit-Šaḫṭu": ("South Mesopotamia", "Akkad"),
    "Bit-ḫulummu": ("South Mesopotamia", "Akkad"),
    "Bāb-ṣubbāti": ("South Mesopotamia", "Akkad"),
    "Ba-milkišu": ("South Mesopotamia", "Akkad"),
    "Kapri-ša-naqidati": ("South Mesopotamia", "Akkad"),
    "Kapru": ("South Mesopotamia", "Akkad"),
    "Pašime": ("South Mesopotamia", "Akkad"),
    "Naṣir": ("South Mesopotamia", "Akkad"),
    "Naḫalla": ("South Mesopotamia", "Akkad"),
    "Dusabar": ("South Mesopotamia", "Akkad"),
    "Kumu": ("South Mesopotamia", "Akkad"),
    "KI.AN": ("South Mesopotamia", "Akkad"),
    "GARIN-naḫallum": ("South Mesopotamia", "Akkad"),
    # South Mesopotamia > Sumer
    "Garšana": ("South Mesopotamia", "Sumer"),
    "Pī-Kasî": ("South Mesopotamia", "Sumer"),
    "Girigu": ("South Mesopotamia", "Sumer"),
    # South Mesopotamia > Sealand
    "Dūr-Enlilē": ("South Mesopotamia", "Sealand"),
    # North Mesopotamia > Assyria
    "Šibaniba": ("North Mesopotamia", "Assyria"),
    "Tarbisu": ("North Mesopotamia", "Assyria"),
    "Tushhan": ("North Mesopotamia", "Assyria"),
    "Kilizu": ("North Mesopotamia", "Assyria"),
    "Ḫadatu": ("North Mesopotamia", "Assyria"),
    "Apqu-ša-Adad": ("North Mesopotamia", "Assyria"),
    "Tabetu": ("North Mesopotamia", "Assyria"),
    "Šaddikanni": ("North Mesopotamia", "Assyria"),
    "Til Barsip": ("North Mesopotamia", "Assyria"),
    "Marqasu": ("North Mesopotamia", "Assyria"),
    "Kar-bel-matati": ("North Mesopotamia", "Assyria"),
    "Kar-Mullissu": ("North Mesopotamia", "Assyria"),
    "Kar-Nabu": ("North Mesopotamia", "Assyria"),
    "Ḫadiranu-ša-Nabu": ("North Mesopotamia", "Assyria"),
    "Idu": ("North Mesopotamia", "Assyria"),
    # North Mesopotamia > Upper Mesopotamia
    "Nagar": ("North Mesopotamia", "Upper Mesopotamia"),
    "Šubat-Enlil": ("North Mesopotamia", "Upper Mesopotamia"),
    "Ašnakkum": ("North Mesopotamia", "Upper Mesopotamia"),
    "Qattara": ("North Mesopotamia", "Upper Mesopotamia"),
    "Ḫarbe": ("North Mesopotamia", "Upper Mesopotamia"),
    "Kahat": ("North Mesopotamia", "Upper Mesopotamia"),
    "Tigunānum": ("North Mesopotamia", "Upper Mesopotamia"),
    "Mardaman": ("North Mesopotamia", "Upper Mesopotamia"),
    "Baḫe": ("North Mesopotamia", "Upper Mesopotamia"),
    "Udannu": ("North Mesopotamia", "Upper Mesopotamia"),
    # Anatolia
    "Ḫattusa": ("Anatolia", ""),
    "Šapinuwa": ("Anatolia", ""),
    "Melidu": ("Anatolia", ""),
    # Elam / Iran
    "Pārśa": ("Elam / Iran", ""),
    "Anšan": ("Elam / Iran", ""),
    "Ecbatana": ("Elam / Iran", ""),
    "Agamatanu": ("Elam / Iran", ""),
    "Tall-I Takht": ("Elam / Iran", ""),
    "Šahdad (Kerman, Iran)": ("Elam / Iran", ""),
    "Kulišhinaš": ("Elam / Iran", ""),
    "Elammu": ("Elam / Iran", ""),
    "Kišesim": ("Elam / Iran", ""),
    "Qasr-i Abu Nasr": ("Elam / Iran", ""),
    "Kašši...": ("Elam / Iran", ""),
    "Šašrum": ("Elam / Iran", ""),
    "Rusahinili": ("Elam / Iran", ""),
    # Levant / Syria
    "Ekalte": ("Levant / Syria", ""),
    "Harradum": ("Levant / Syria", ""),
    "Guzana": ("Levant / Syria", ""),
    "Hamath": ("Levant / Syria", ""),
    "Hamat": ("Levant / Syria", ""),
    "Karkemish": ("Levant / Syria", ""),
    "Carchemish": ("Levant / Syria", ""),
    "Tunip": ("Levant / Syria", ""),
    "Qāṭīnu": ("Levant / Syria", ""),
    "Qatuna": ("Levant / Syria", ""),
    "Gubla": ("Levant / Syria", ""),
    "Samal": ("Levant / Syria", ""),
    "Nereb": ("Levant / Syria", ""),
    "Harran": ("Levant / Syria", ""),
    "Unqi": ("Levant / Syria", ""),
    "Šūri": ("Levant / Syria", ""),
    "Tell Abu Galgal": ("Levant / Syria", ""),
    # Egypt / North Africa
    "Akhetaten": ("Egypt / North Africa", ""),
    "Abdju": ("Egypt / North Africa", ""),
    "Elbonia": ("Egypt / North Africa", ""),
    "Thêbai": ("Egypt / North Africa", ""),
    # Arabia / Gulf
    "Tema": ("West Periphery", ""),
    # Levant > Judah-Israel
    "Yāhūdu": ("Levant / Syria", "Judah-Israel"),
    "Timnah": ("Levant / Syria", "Judah-Israel"),
    "Antipatris": ("Levant / Syria", "Judah-Israel"),
    "Isqalluna": ("Levant / Syria", "Judah-Israel"),
    "Asdūdu": ("Levant / Syria", "Judah-Israel"),
    "Samerina": ("Levant / Syria", "Judah-Israel"),
    "Hazatu": ("Levant / Syria", "Judah-Israel"),
    # Anatolia > Halicarnassus
    "Halicarnassus": ("Anatolia", ""),
    "Gordion": ("Anatolia", ""),
    # Greek periphery
    "Phoenician": ("Levant / Syria", ""),
    "Aqa": ("Levant / Syria", ""),
}

# Invert: lowercased ancient_name prefix → (region, subregion)
_PROV_LOOKUP: dict[str, tuple[str, str]] = {}
for (_reg, _sub), _names in PROVENIENCE_REGIONS.items():
    for _name in _names:
        _PROV_LOOKUP[_name.lower()] = (_reg, _sub)


def _match_provenience_region(ancient_name: str) -> tuple[str, str]:
    """Match an ancient_name to its (region, subregion).

    Checks PROVENIENCE_DIRECT (exact Unicode match) first,
    then falls back to ASCII prefix matching via PROVENIENCE_REGIONS.
    """
    if not ancient_name:
        return ("Unknown", "")
    # Exact match on Unicode name
    if ancient_name in PROVENIENCE_DIRECT:
        return PROVENIENCE_DIRECT[ancient_name]
    lower = ancient_name.lower()
    # Exact lowercase match on prefix list
    if lower in _PROV_LOOKUP:
        return _PROV_LOOKUP[lower]
    # Prefix match (handles "Nippur?" or "Ur " variants)
    for prefix, region_sub in _PROV_LOOKUP.items():
        if lower.startswith(prefix):
            return region_sub
    # Check if it contains a known name (handles "Tell X" variants)
    for prefix, region_sub in _PROV_LOOKUP.items():
        if prefix in lower:
            return region_sub
    return ("Unknown", "")


def parse_period(raw: str) -> dict | None:
    """
    Parse a raw CDLI period string into canonical form + date range.

    Handles:
      "Ur III (ca. 2100-2000 BC)"      → canonical="Ur III", start=2100, end=2000
      "Ur III (ca. 2100-2000 BC) ?"    → canonical="Ur III", start=2100, end=2000
      "Neo-Babylonian (626-539 BC)"    → canonical="Neo-Babylonian"
      "Sassanian (224-641 AD)"         → canonical="Sassanian", start=-224, end=-641
      "uncertain"                       → canonical="uncertain", start=None, end=None
      "fake (modern)"                   → canonical="fake (modern)", start=None, end=None
      Multi-period (two periods joined) → skip (too ambiguous)
    """
    raw = raw.strip()
    if not raw:
        return None

    # Strip trailing "?" and whitespace
    clean = re.sub(r"\s*\?$", "", raw).strip()

    # Skip multi-period entries (contain ", " between two period names)
    # e.g. "ED I-II (ca. 2900-2700 BC), Old Babylonian (ca. 1900-1600 BC)"
    if re.search(r"\)\s*,\s*[A-Z]", clean):
        # Store as-is with NULL dates
        return {"raw": raw, "canonical": clean, "start": None, "end": None}

    # Pattern: "Name (ca. YYYY-YYYY BC)" or "Name (YYYY-YYYY BC)"
    m = re.match(
        r"^(.+?)\s*\((?:ca\.?\s+)?(\d+)[-–](\d+)\s+(BC|AD)\)\s*$", clean, re.IGNORECASE
    )
    if m:
        name = m.group(1).strip()
        y1 = int(m.group(2))
        y2 = int(m.group(3))
        era = m.group(4).upper()
        # AD dates are stored as negative BCE (or we could store as positive and note era)
        # Store BC as positive, AD as negative
        start = y1 if era == "BC" else -y1
        end = y2 if era == "BC" else -y2
        return {"raw": raw, "canonical": name, "start": start, "end": end}

    # Pattern: "Name (ca. YYYY BC)" — single year
    m = re.match(r"^(.+?)\s*\((?:ca\.?\s+)?(\d+)\s+(BC|AD)\)\s*$", clean, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        y = int(m.group(2))
        era = m.group(3).upper()
        val = y if era == "BC" else -y
        return {"raw": raw, "canonical": name, "start": val, "end": val}

    # No date found — store as-is
    return {"raw": raw, "canonical": clean, "start": None, "end": None}


def parse_provenience(raw: str) -> dict | None:
    """
    Parse "Ancient (mod. Modern)" format.

    "Nippur (mod. Nuffar)"           → ancient="Nippur", modern="Nuffar"
    "uncertain (mod. uncertain)"     → ancient="uncertain", modern="uncertain"
    "Nippur (mod. Nuffar) ?"        → ancient="Nippur" (strip ?)
    "Nippur (mod. Nuffar) ?"        → same
    """
    raw = raw.strip()
    if not raw:
        return None

    # Strip trailing ? and whitespace
    clean = re.sub(r"\s*\??$", "", raw).strip()

    # Strip trailing commas
    clean = clean.rstrip(",").strip()

    # Handle slash compounds: "Babili (mod. Babylon)/Borsippa" -> take first part
    if "/" in clean and "(mod." in clean:
        clean = clean.split("/")[0].strip()

    # Handle trailing typos: "Babili (mod. Babylon)a" -> strip char after close paren
    clean = re.sub(r"\)\s*[a-z]\s*$", ")", clean)

    # Handle missing open paren: "uncertain mod. uncertain)" -> "uncertain"
    if "mod." in clean and "(" not in clean:
        clean = clean.split("mod.")[0].strip()

    m = re.match(r"^(.+?)\s*\(mod\.\s+(.+?)\)\s*$", clean, re.IGNORECASE)
    if m:
        ancient = m.group(1).strip()
        modern = m.group(2).strip()
        return {"raw": raw, "ancient_name": ancient, "modern_name": modern}

    # No "mod." pattern — store ancient name only
    return {"raw": raw, "ancient_name": clean, "modern_name": None}


def normalize_genre(raw: str) -> str:
    """Normalize genre string to canonical form."""
    # Title-case the primary genre (before any semicolon)
    primary = raw.split(";")[0].strip()
    # Handle known case variants
    canonical_map = {
        "administrative": "Administrative",
        "legal": "Legal",
        "letter": "Letter",
        "lexical": "Lexical",
        "literary": "Literary",
        "school": "School",
        "scientific": "Scientific",
        "administative": "Administrative",  # typo in source
        "omens": "Omen",
    }
    return canonical_map.get(
        primary.lower(), primary.title() if primary.islower() else primary
    )


def audit_csv() -> tuple[Counter, Counter, Counter, Counter]:
    """Read CDLI CSV and count distinct values per dimension."""
    periods: Counter = Counter()
    languages: Counter = Counter()
    genres: Counter = Counter()
    proveniences: Counter = Counter()

    with open(CDLI_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["period"].strip():
                periods[row["period"].strip()] += 1
            if row["language"].strip():
                for lang in row["language"].strip().split("; "):
                    if lang.strip():
                        languages[lang.strip()] += 1
            if row["genre"].strip():
                genres[row["genre"].strip()] += 1
            if row["provenience"].strip():
                proveniences[row["provenience"].strip()] += 1

    return periods, languages, genres, proveniences


def seed_periods(conn: psycopg.Connection, periods: Counter, dry_run: bool) -> int:
    inserted = 0
    seen_canonicals: dict[str, dict] = {}

    for raw, _ in periods.most_common():
        parsed = parse_period(raw)
        if not parsed:
            continue

        canonical = parsed["canonical"]
        start = parsed["start"]
        end = parsed["end"]

        # If we've seen this canonical before, use its dates (from the unqualified form)
        if canonical in seen_canonicals:
            existing = seen_canonicals[canonical]
            if start is None:
                start = existing["start"]
            if end is None:
                end = existing["end"]
        else:
            seen_canonicals[canonical] = {"start": start, "end": end}

        # Check PERIOD_ALIASES for compound/variant canonicals
        primary = PERIOD_ALIASES.get(canonical)
        if primary:
            # Use the primary period's group/sort/dates
            group_name, sort_order = _PERIOD_LOOKUP.get(primary, ("Other", 899))
            ds, de = _PERIOD_DATES.get(primary, (None, None))
            if start is None:
                start = ds
            if end is None:
                end = de
        else:
            # Look up group data from PERIOD_GROUPS
            group_name, sort_order = _PERIOD_LOOKUP.get(canonical, ("Other", 899))
            # Fill in dates from group data if not parsed from raw string
            ds, de = _PERIOD_DATES.get(canonical, (None, None))
            if start is None:
                start = ds
            if end is None:
                end = de

        if not dry_run:
            conn.execute(
                """
                INSERT INTO period_canon
                    (raw_period, canonical, date_start_bce, date_end_bce,
                     group_name, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (raw_period) DO UPDATE SET
                    group_name = EXCLUDED.group_name,
                    sort_order = EXCLUDED.sort_order,
                    date_start_bce = EXCLUDED.date_start_bce,
                    date_end_bce = EXCLUDED.date_end_bce
            """,
                (raw, canonical, start, end, group_name, sort_order),
            )
        inserted += 1

    # Ensure primary targets of PERIOD_ALIASES have their own period_canon row.
    # After migration 016, artifacts may reference the primary canonical directly
    # (e.g. "Parthian") but the CSV only has the compound raw form.
    if not dry_run:
        alias_targets = set(PERIOD_ALIASES.values())
        for target in alias_targets:
            group_name, sort_order = _PERIOD_LOOKUP.get(target, ("Other", 899))
            ds, de = _PERIOD_DATES.get(target, (None, None))
            conn.execute(
                """
                INSERT INTO period_canon
                    (raw_period, canonical, date_start_bce, date_end_bce,
                     group_name, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (raw_period) DO UPDATE SET
                    group_name = EXCLUDED.group_name,
                    sort_order = EXCLUDED.sort_order,
                    date_start_bce = EXCLUDED.date_start_bce,
                    date_end_bce = EXCLUDED.date_end_bce
            """,
                (target, target, ds, de, group_name, sort_order),
            )

    return inserted


def seed_languages(conn: psycopg.Connection, dry_run: bool) -> int:
    for cdli_name, oracc_code, full_name, family in LANGUAGE_MAP:
        if not dry_run:
            conn.execute(
                """
                INSERT INTO language_map (cdli_name, oracc_code, full_name, family)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (cdli_name) DO NOTHING
            """,
                (cdli_name, oracc_code, full_name, family),
            )
    return len(LANGUAGE_MAP)


def seed_genres(conn: psycopg.Connection, genres: Counter, dry_run: bool) -> int:
    inserted = 0
    for raw, _ in genres.most_common():
        canonical = normalize_genre(raw)
        if not dry_run:
            conn.execute(
                """
                INSERT INTO genre_canon (raw_genre, canonical)
                VALUES (%s, %s)
                ON CONFLICT (raw_genre) DO NOTHING
            """,
                (raw, canonical),
            )
        inserted += 1
    return inserted


def seed_proveniences(
    conn: psycopg.Connection, proveniences: Counter, dry_run: bool
) -> int:
    inserted = 0
    for raw, _ in proveniences.most_common():
        parsed = parse_provenience(raw)
        if not parsed:
            continue

        ancient = parsed["ancient_name"]
        region, subregion = _match_provenience_region(ancient)

        if not dry_run:
            conn.execute(
                """
                INSERT INTO provenience_canon
                    (raw_provenience, ancient_name, modern_name,
                     region, subregion, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (raw_provenience) DO UPDATE SET
                    region = EXCLUDED.region,
                    subregion = EXCLUDED.subregion,
                    sort_order = EXCLUDED.sort_order
            """,
                (
                    raw,
                    ancient,
                    parsed["modern_name"],
                    region,
                    subregion if subregion else None,
                    inserted,
                ),
            )
        inserted += 1
    return inserted


def seed_canonical_genres(conn: psycopg.Connection, dry_run: bool) -> int:
    """Seed canonical_genres table with deduplicated genre names."""
    for name in CANONICAL_GENRES:
        if not dry_run:
            conn.execute(
                """
                INSERT INTO canonical_genres (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
            """,
                (name,),
            )
    return len(CANONICAL_GENRES)


def seed_canonical_languages(conn: psycopg.Connection, dry_run: bool) -> int:
    """Seed canonical_languages table with atomic language names."""
    for name, oracc_code, family in CANONICAL_LANGUAGES:
        if not dry_run:
            conn.execute(
                """
                INSERT INTO canonical_languages (name, oracc_code, family)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """,
                (name, oracc_code, family),
            )
    return len(CANONICAL_LANGUAGES)


def seed_surfaces(conn: psycopg.Connection, dry_run: bool) -> int:
    for raw, canonical in SURFACE_CANON:
        if not dry_run:
            conn.execute(
                """
                INSERT INTO surface_canon (raw_surface, canonical)
                VALUES (%s, %s)
                ON CONFLICT (raw_surface) DO NOTHING
            """,
                (raw, canonical),
            )
    return len(SURFACE_CANON)


def main():
    parser = argparse.ArgumentParser(description="Seed normalization lookup tables")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate without writing"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 1: SEED LOOKUP TABLES")
    print("=" * 60)

    print("\nAuditing CDLI CSV...", end=" ", flush=True)
    periods, languages, genres, proveniences = audit_csv()
    print(
        f"done. Found {len(periods)} periods, {len(languages)} languages, "
        f"{len(genres)} genres, {len(proveniences)} proveniences."
    )

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        conn = None
    else:
        settings = get_settings()
        conninfo = (
            f"host={settings.db_host} port={settings.db_port} "
            f"dbname={settings.db_name} user={settings.db_user} "
            f"password={settings.db_password}"
        )
        conn = psycopg.connect(conninfo)

    try:
        n_periods = seed_periods(conn, periods, args.dry_run)
        print(f"  period_canon:      {n_periods} rows")

        n_languages = seed_languages(conn, args.dry_run)
        print(f"  language_map:      {n_languages} rows")

        n_genres = seed_genres(conn, genres, args.dry_run)
        print(f"  genre_canon:       {n_genres} rows")

        n_proveniences = seed_proveniences(conn, proveniences, args.dry_run)
        print(f"  provenience_canon: {n_proveniences} rows")

        n_surfaces = seed_surfaces(conn, args.dry_run)
        print(f"  surface_canon:     {n_surfaces} rows")

        n_cgenres = seed_canonical_genres(conn, args.dry_run)
        print(f"  canonical_genres:  {n_cgenres} rows")

        n_clangs = seed_canonical_languages(conn, args.dry_run)
        print(f"  canonical_langs:   {n_clangs} rows")

        if conn and not args.dry_run:
            conn.commit()

        total = (
            n_periods
            + n_languages
            + n_genres
            + n_proveniences
            + n_surfaces
            + n_cgenres
            + n_clangs
        )
        print(
            f"\n{'[DRY RUN] Would insert' if args.dry_run else 'Inserted'} {total} total rows."
        )

        # Validate against expected thresholds
        assert len(periods) >= 75, f"Expected >=75 periods, got {len(periods)}"
        assert len(languages) >= 30, f"Expected >=30 languages, got {len(languages)}"
        assert len(genres) >= 50, f"Expected >=50 genres, got {len(genres)}"
        assert (
            len(proveniences) >= 400
        ), f"Expected >=400 proveniences, got {len(proveniences)}"
        print("Validation: OK")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\nFailed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
