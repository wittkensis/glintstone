"""Lookup / canon table seeder — the prerequisite for all other connectors.

Seeds seven normalization tables from two sources:

  Static (baked in):
    language_map        CDLI label → ORACC code + family
    canonical_languages atomic language names for junction table
    canonical_genres    atomic genre names for junction table
    surface_canon       ATF @-markers → canonical surface names

  Dynamic (derived from cdli_cat.csv):
    period_canon        raw period strings → canonical + date range + group
    genre_canon         raw genre strings → canonical genre name
    provenience_canon   raw provenience strings → ancient/modern + region

All inserts are ON CONFLICT DO UPDATE so re-runs are safe.
`cdli-catalog` declares `runs_after = ["lookup-tables"]` — this must run first.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator, Optional

from ingestion.base import (
    ConflictPolicy,
    LoadStats,
    RunContext,
    SourceConnector,
    SourceManifest,
)
from ingestion.loader import upsert_batch

DEFAULT_CSV = Path("source-data/sources/CDLI/metadata/cdli_cat.csv")

# Unique key per target table
_TABLE_KEYS: dict[str, list[str]] = {
    "language_map": ["cdli_name"],
    "canonical_languages": ["name"],
    "canonical_genres": ["name"],
    "surface_canon": ["raw_surface"],
    "period_canon": ["raw_period"],
    "genre_canon": ["raw_genre"],
    "provenience_canon": ["raw_provenience"],
}

# ─────────────────────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────────────────────

LANGUAGE_MAP = [
    # (cdli_name, oracc_code, full_name, family)
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
# PERIOD GROUPS  (canonical → group + sort + date range)
# Middle Chronology. Positive = BCE, negative = CE.
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

# Derived lookups: canonical → (group_name, sort_order) and (date_start, date_end)
_PERIOD_GROUP: dict[str, tuple[str, int]] = {}
_PERIOD_DATES: dict[str, tuple[int | None, int | None]] = {}
for _grp, _members in PERIOD_GROUPS.items():
    for _canonical, _order, _ds, _de in _members:
        _PERIOD_GROUP[_canonical] = (_grp, _order)
        _PERIOD_DATES[_canonical] = (_ds, _de)

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
# PROVENIENCE REGIONS
# ─────────────────────────────────────────────────────────
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

PROVENIENCE_DIRECT: dict[str, tuple[str, str]] = {
    "Puzriš-Dagan": ("South Mesopotamia", "Central"),
    "Irisagrig": ("South Mesopotamia", "Central"),
    "Irisaĝrig": ("South Mesopotamia", "Central"),
    "Du-Enlila": ("South Mesopotamia", "Central"),
    "Kesh": ("South Mesopotamia", "Central"),
    "Sagub": ("South Mesopotamia", "Central"),
    "Gišša": ("South Mesopotamia", "Central"),
    "Gišši": ("South Mesopotamia", "Central"),
    "Maškan-šapir": ("South Mesopotamia", "Central"),
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
    "Garšana": ("South Mesopotamia", "Sumer"),
    "Pī-Kasî": ("South Mesopotamia", "Sumer"),
    "Girigu": ("South Mesopotamia", "Sumer"),
    "Dūr-Enlilē": ("South Mesopotamia", "Sealand"),
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
    "Ḫattusa": ("Anatolia", ""),
    "Šapinuwa": ("Anatolia", ""),
    "Melidu": ("Anatolia", ""),
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
    "Akhetaten": ("Egypt / North Africa", ""),
    "Abdju": ("Egypt / North Africa", ""),
    "Elbonia": ("Egypt / North Africa", ""),
    "Thêbai": ("Egypt / North Africa", ""),
    "Tema": ("West Periphery", ""),
    "Yāhūdu": ("Levant / Syria", "Judah-Israel"),
    "Timnah": ("Levant / Syria", "Judah-Israel"),
    "Antipatris": ("Levant / Syria", "Judah-Israel"),
    "Isqalluna": ("Levant / Syria", "Judah-Israel"),
    "Asdūdu": ("Levant / Syria", "Judah-Israel"),
    "Samerina": ("Levant / Syria", "Judah-Israel"),
    "Hazatu": ("Levant / Syria", "Judah-Israel"),
    "Halicarnassus": ("Anatolia", ""),
    "Gordion": ("Anatolia", ""),
    "Phoenician": ("Levant / Syria", ""),
    "Aqa": ("Levant / Syria", ""),
}

# Prefix lookup built from PROVENIENCE_REGIONS (lowercased for matching)
_PROV_PREFIX: dict[str, tuple[str, str]] = {}
for (_reg, _sub), _names in PROVENIENCE_REGIONS.items():
    for _n in _names:
        _PROV_PREFIX[_n.lower()] = (_reg, _sub)

# Map raw genre parts (lowercased) → canonical name
GENRE_NORMALIZE: dict[str, str] = {
    "administrative": "Administrative",
    "administative": "Administrative",  # typo in source
    "administrative record": "Administrative",
    "astronomical": "Astronomical",
    "astronomical, omen": "Astronomical",
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
    "royal/votive": "Royal/Monumental",
    "royal inscription": "Royal/Monumental",
    "school": "School",
    "scientific": "Scientific",
    "votive": "Votive",
}


# ─────────────────────────────────────────────────────────
# CONNECTOR
# ─────────────────────────────────────────────────────────


class LookupTablesConnector(SourceConnector):
    id = "lookup-tables"
    display_name = "Lookup / Canon Tables"
    description = (
        "Seeds period_canon, language_map, genre_canon, provenience_canon, "
        "surface_canon, canonical_genres, and canonical_languages. "
        "Must run before cdli-catalog."
    )
    kind = "lookup"
    runs_after = []
    upstream_url = "https://cdli.mpiwg-berlin.mpg.de/"
    license = "CC-BY-NC-3.0"

    def __init__(self, csv_path: Optional[Path] = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV

    # --- discover --------------------------------------------------------

    def discover(self, ctx: RunContext) -> SourceManifest:
        if not self.csv_path.exists():
            ctx.warn("lookup.source_missing", path=str(self.csv_path))
            return SourceManifest()
        checksum = _file_checksum(self.csv_path)
        return SourceManifest(
            checksum=checksum,
            raw_path=str(self.csv_path),
            metadata={"size_bytes": self.csv_path.stat().st_size},
        )

    # --- extract ---------------------------------------------------------

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        """Yield one dict per target row, tagged with `_target` table name.

        Static tables are emitted first (no CSV required). Dynamic tables
        (period_canon, genre_canon, provenience_canon) require the CSV.
        """
        # Static: language_map
        for cdli_name, oracc_code, full_name, family in LANGUAGE_MAP:
            yield {
                "_target": "language_map",
                "cdli_name": cdli_name,
                "oracc_code": oracc_code,
                "full_name": full_name,
                "family": family,
            }

        # Static: canonical_languages
        for name, oracc_code, family in CANONICAL_LANGUAGES:
            yield {
                "_target": "canonical_languages",
                "name": name,
                "oracc_code": oracc_code,
                "family": family,
            }

        # Static: canonical_genres
        for name in CANONICAL_GENRES:
            yield {"_target": "canonical_genres", "name": name}

        # Static: surface_canon
        for raw_surface, canonical in SURFACE_CANON:
            yield {
                "_target": "surface_canon",
                "raw_surface": raw_surface,
                "canonical": canonical,
            }

        if not self.csv_path.exists():
            ctx.warn("lookup.csv_missing_skip_dynamic", path=str(self.csv_path))
            return

        # Scan CSV to collect distinct values for dynamic canon tables
        ctx.info("lookup.scan_csv", path=str(self.csv_path))
        periods: Counter[str] = Counter()
        genres: Counter[str] = Counter()
        proveniences: Counter[str] = Counter()

        with open(self.csv_path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("period", "").strip():
                    periods[row["period"].strip()] += 1
                if row.get("genre", "").strip():
                    genres[row["genre"].strip()] += 1
                if row.get("provenience", "").strip():
                    proveniences[row["provenience"].strip()] += 1

        ctx.info(
            "lookup.csv_scanned",
            periods=len(periods),
            genres=len(genres),
            proveniences=len(proveniences),
        )

        # Dynamic: period_canon (from CSV + static alias targets)
        yield from _emit_periods(periods)

        # Dynamic: genre_canon
        for raw in genres:
            canonical = _normalize_genre(raw)
            yield {"_target": "genre_canon", "raw_genre": raw, "canonical": canonical}

        # Dynamic: provenience_canon (order preserved — sort_order = enumeration)
        for sort_order, raw in enumerate(proveniences):
            parsed = _parse_provenience(raw)
            if not parsed:
                continue
            region, subregion = _match_provenience_region(parsed["ancient_name"])
            yield {
                "_target": "provenience_canon",
                "raw_provenience": raw,
                "ancient_name": parsed["ancient_name"],
                "modern_name": parsed["modern_name"],
                "region": region,
                "subregion": subregion or None,
                "sort_order": sort_order,
            }

    # --- load ------------------------------------------------------------

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        ctx.info("lookup.load_start")
        by_target: dict[str, list[dict]] = {}
        for row in rows:
            target = row.pop("_target")
            by_target.setdefault(target, []).append(row)

        total = LoadStats()
        for table, batch in by_target.items():
            unique_key = _TABLE_KEYS[table]
            stats = upsert_batch(
                ctx.db,
                table=table,
                rows=batch,
                unique_key=unique_key,
                policy=ConflictPolicy.UPDATE,
            )
            ctx.info(
                f"lookup.loaded.{table}", inserted=stats.inserted, updated=stats.updated
            )
            total = total.merge(stats)

        return total

    # --- verify ----------------------------------------------------------

    def verify(self, ctx: RunContext) -> None:
        checks = [
            ("period_canon", 75),
            ("language_map", 30),
            ("genre_canon", 50),
            ("provenience_canon", 400),
        ]
        for table, minimum in checks:
            row = ctx.db.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
            n = row["n"] if isinstance(row, dict) else row[0]
            ctx.info(f"lookup.verify.{table}", count=n)
            if n < minimum:
                raise AssertionError(f"{table} has {n:,} rows; expected ≥ {minimum:,}.")


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _emit_periods(periods: Counter) -> Iterator[dict]:
    """Yield period_canon rows from discovered CSV periods + alias targets."""
    seen: dict[str, dict] = {}

    for raw, _ in periods.most_common():
        parsed = _parse_period(raw)
        if not parsed:
            continue
        canonical = parsed["canonical"]
        start, end = parsed["start"], parsed["end"]

        # Carry dates forward from the first (most frequent) sighting
        if canonical in seen:
            existing = seen[canonical]
            if start is None:
                start = existing["start"]
            if end is None:
                end = existing["end"]
        else:
            seen[canonical] = {"start": start, "end": end}

        primary = PERIOD_ALIASES.get(canonical)
        if primary:
            group_name, sort_order = _PERIOD_GROUP.get(primary, ("Other", 899))
            ds, de = _PERIOD_DATES.get(primary, (None, None))
        else:
            group_name, sort_order = _PERIOD_GROUP.get(canonical, ("Other", 899))
            ds, de = _PERIOD_DATES.get(canonical, (None, None))

        if start is None:
            start = ds
        if end is None:
            end = de

        yield {
            "_target": "period_canon",
            "raw_period": raw,
            "canonical": canonical,
            "date_start_bce": start,
            "date_end_bce": end,
            "group_name": group_name,
            "sort_order": sort_order,
        }

    # Ensure alias targets (e.g. "Parthian") have their own row
    for target in set(PERIOD_ALIASES.values()):
        group_name, sort_order = _PERIOD_GROUP.get(target, ("Other", 899))
        ds, de = _PERIOD_DATES.get(target, (None, None))
        yield {
            "_target": "period_canon",
            "raw_period": target,
            "canonical": target,
            "date_start_bce": ds,
            "date_end_bce": de,
            "group_name": group_name,
            "sort_order": sort_order,
        }


def _parse_period(raw: str) -> dict | None:
    raw = raw.strip()
    if not raw:
        return None
    clean = re.sub(r"\s*\?$", "", raw).strip()

    # Multi-period entries: store as-is with NULL dates
    if re.search(r"\)\s*,\s*[A-Z]", clean):
        return {"raw": raw, "canonical": clean, "start": None, "end": None}

    m = re.match(
        r"^(.+?)\s*\((?:ca\.?\s+)?(\d+)[-–](\d+)\s+(BC|AD)\)\s*$",
        clean,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
        y1, y2 = int(m.group(2)), int(m.group(3))
        era = m.group(4).upper()
        start = y1 if era == "BC" else -y1
        end = y2 if era == "BC" else -y2
        return {"raw": raw, "canonical": name, "start": start, "end": end}

    m = re.match(r"^(.+?)\s*\((?:ca\.?\s+)?(\d+)\s+(BC|AD)\)\s*$", clean, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        val = int(m.group(2)) * (1 if m.group(3).upper() == "BC" else -1)
        return {"raw": raw, "canonical": name, "start": val, "end": val}

    return {"raw": raw, "canonical": clean, "start": None, "end": None}


def _parse_provenience(raw: str) -> dict | None:
    raw = raw.strip()
    if not raw:
        return None
    clean = re.sub(r"\s*\??$", "", raw).strip().rstrip(",").strip()

    if "/" in clean and "(mod." in clean:
        clean = clean.split("/")[0].strip()
    clean = re.sub(r"\)\s*[a-z]\s*$", ")", clean)
    if "mod." in clean and "(" not in clean:
        clean = clean.split("mod.")[0].strip()

    m = re.match(r"^(.+?)\s*\(mod\.\s+(.+?)\)\s*$", clean, re.IGNORECASE)
    if m:
        return {"ancient_name": m.group(1).strip(), "modern_name": m.group(2).strip()}
    return {"ancient_name": clean, "modern_name": None}


def _normalize_genre(raw: str) -> str:
    primary = raw.split(";")[0].strip()
    return GENRE_NORMALIZE.get(
        primary.lower(), primary.title() if primary.islower() else primary
    )


def _match_provenience_region(ancient_name: str) -> tuple[str, str]:
    if not ancient_name:
        return ("Unknown", "")
    if ancient_name in PROVENIENCE_DIRECT:
        return PROVENIENCE_DIRECT[ancient_name]
    lower = ancient_name.lower()
    if lower in _PROV_PREFIX:
        return _PROV_PREFIX[lower]
    for prefix, region_sub in _PROV_PREFIX.items():
        if lower.startswith(prefix):
            return region_sub
    for prefix, region_sub in _PROV_PREFIX.items():
        if prefix in lower:
            return region_sub
    return ("Unknown", "")
