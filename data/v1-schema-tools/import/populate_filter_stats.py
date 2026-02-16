#!/usr/bin/env python3
"""
Populate filter stats tables with hierarchical groupings and counts.
Run after main data import to update aggregation tables.
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "database" / "glintstone.db"

# =============================================================================
# LANGUAGE MAPPINGS - Group by root language family
# =============================================================================

LANGUAGE_ROOT_MAP = {
    # Sumerian family
    "Sumerian": "Sumerian",
    "Sumerian ?": "Sumerian",
    "Sumerian; Akkadian": "Sumerian",  # Primary Sumerian
    "Sumerian, Akkadian": "Sumerian",
    "Sumerian; Akkadian (pseudo)": "Sumerian",

    # Akkadian family (including dialects)
    "Akkadian": "Akkadian",
    "Akkadian ?": "Akkadian",
    "Akkadian; Persian; Elamite": "Akkadian",
    "Akkadian, Aramaic": "Akkadian",
    "Akkadian; Aramaic": "Akkadian",
    "Akkadian; Persian; Elamite; Egyptian": "Akkadian",
    "Akkadian; Elamite": "Akkadian",
    "Akkadian; Elamite; Persian": "Akkadian",
    "Akkadian; Persian": "Akkadian",
    "Akkadian; Elamite; Persian; Egyptian": "Akkadian",
    "Akkadian; Egyptian": "Akkadian",
    "Akkadian; Persian, Elamite, Babylonian": "Akkadian",
    "Akkadian; Persian; Elamite Egyptian": "Akkadian",
    "Akkadian, Aramaic?": "Akkadian",
    "Akkadian; Elamite; Persian; Egyptian ?": "Akkadian",
    "Akkadian; Greek": "Akkadian",
    "Persian, Babylonian": "Akkadian",  # Babylonian is Akkadian dialect

    # Elamite family
    "Elamite": "Elamite",
    "Persian; Elamite": "Elamite",
    "Persian; Elamite; Akkadian": "Elamite",
    "Persian, Elamite": "Elamite",

    # Hittite/Anatolian
    "Hittite": "Anatolian",
    "Hittite; Hurrian": "Anatolian",
    "Luwian": "Anatolian",
    "Hurrian": "Anatolian",

    # Northwest Semitic
    "Eblaite": "Northwest Semitic",
    "Ugaritic": "Northwest Semitic",
    "Aramaic": "Northwest Semitic",
    "Aramaic ?": "Northwest Semitic",
    "Hebrew": "Northwest Semitic",
    "Qatabanian": "Northwest Semitic",  # South Arabian
    "Arabic": "Northwest Semitic",
    "Mandaic": "Northwest Semitic",

    # Indo-European (non-Anatolian)
    "Persian": "Indo-European",
    "Greek": "Indo-European",

    # Other
    "Egyptian": "Other",
    "Egyptian ?": "Other",
    "Urartian": "Other",
    "undetermined": "Undetermined",
    "uncertain": "Undetermined",
    "unclear": "Undetermined",
    "no linguistic content": "Undetermined",
    "uninscribed": "Undetermined",
    "bilingual": "Undetermined",
    "clay": "Undetermined",  # Data error
}

def get_root_language(lang: str) -> str:
    """Determine root language family for a language string."""
    if not lang:
        return "Undetermined"

    # Check exact match first
    if lang in LANGUAGE_ROOT_MAP:
        return LANGUAGE_ROOT_MAP[lang]

    # Check if it starts with a known language
    lang_lower = lang.lower()
    if lang_lower.startswith("sumerian"):
        return "Sumerian"
    if lang_lower.startswith("akkadian"):
        return "Akkadian"
    if lang_lower.startswith("elamite"):
        return "Elamite"
    if lang_lower.startswith("hittite") or lang_lower.startswith("hurrian"):
        return "Anatolian"
    if lang_lower.startswith("persian"):
        return "Indo-European"
    if lang_lower.startswith("aramaic"):
        return "Northwest Semitic"
    if lang_lower.startswith("egyptian"):
        return "Other"

    return "Other"


# =============================================================================
# GENRE MAPPINGS - Group by category
# =============================================================================

GENRE_CATEGORY_MAP = {
    # Administrative
    "Administrative": "Administrative",
    "Administrative ?": "Administrative",
    "administrative": "Administrative",

    # Legal
    "Legal": "Legal",
    "Legal ?": "Legal",
    "legal": "Legal",

    # Literary
    "Literary": "Literary",
    "Literary ?": "Literary",
    "Literary; Mathematical": "Literary",
    "Literary; Lexical": "Literary",

    # Scholarly/Educational
    "Lexical": "Scholarly",
    "Lexical ?": "Scholarly",
    "Lexical; Mathematical": "Scholarly",
    "Lexical; Literary": "Scholarly",
    "Lexical; School": "Scholarly",
    "School": "Scholarly",
    "School ?": "Scholarly",

    # Scientific
    "Mathematical": "Scientific",
    "Mathematical ?": "Scientific",
    "Astronomical": "Scientific",
    "Scientific": "Scientific",
    "Omen": "Scientific",

    # Religious
    "Prayer/Incantation": "Religious",
    "Ritual": "Religious",
    "Ritual ?": "Religious",
    "Votive": "Religious",
    "Private/Votive": "Religious",

    # Epistolary
    "Letter": "Epistolary",
    "Letter ?": "Epistolary",
    "letter": "Epistolary",

    # Royal/Historical
    "Royal/Monumental": "Royal/Historical",
    "Royal/Monumental ?": "Royal/Historical",
    "Royal/Votive": "Royal/Historical",
    "Historical": "Royal/Historical",

    # Other
    "uncertain": "Other",
    "Uncertain": "Other",
    "fake (modern)": "Other",
    "fake (modern) ?": "Other",
    "Other (see subgenre)": "Other",
}

def get_genre_category(genre: str) -> str:
    """Determine category for a genre string."""
    if not genre:
        return "Other"

    if genre in GENRE_CATEGORY_MAP:
        return GENRE_CATEGORY_MAP[genre]

    # Fallback patterns
    genre_lower = genre.lower()
    if "admin" in genre_lower:
        return "Administrative"
    if "legal" in genre_lower:
        return "Legal"
    if "literary" in genre_lower:
        return "Literary"
    if "lexical" in genre_lower or "school" in genre_lower:
        return "Scholarly"
    if "math" in genre_lower or "astro" in genre_lower or "omen" in genre_lower:
        return "Scientific"
    if "prayer" in genre_lower or "ritual" in genre_lower or "votive" in genre_lower:
        return "Religious"
    if "letter" in genre_lower:
        return "Epistolary"
    if "royal" in genre_lower or "monument" in genre_lower or "histor" in genre_lower:
        return "Royal/Historical"

    return "Other"


# =============================================================================
# PROVENIENCE MAPPINGS - Group by region
# =============================================================================

# Major sites mapped to regions
SITE_REGION_MAP = {
    # Southern Babylonia (Sumer)
    "Girsu": "Babylonia",
    "Umma": "Babylonia",
    "Ur": "Babylonia",
    "Uruk": "Babylonia",
    "Nippur": "Babylonia",
    "Larsa": "Babylonia",
    "Isin": "Babylonia",
    "Adab": "Babylonia",
    "Šuruppak": "Babylonia",
    "Puzriš-Dagan": "Babylonia",
    "Drehem": "Babylonia",
    "Lagash": "Babylonia",
    "Garšana": "Babylonia",
    "Irisagrig": "Babylonia",
    "Kisurra": "Babylonia",
    "Šaduppum": "Babylonia",
    "Nerebtum": "Babylonia",

    # Northern Babylonia / Akkad
    "Sippar": "Babylonia",
    "Bābili": "Babylonia",
    "Babylon": "Babylonia",
    "Kish": "Babylonia",
    "Borsippa": "Babylonia",
    "Ešnunna": "Babylonia",
    "Gasur": "Babylonia",
    "Nuzi": "Babylonia",
    "Abu Salabikh": "Babylonia",

    # Assyria
    "Nineveh": "Assyria",
    "Assur": "Assyria",
    "Kalhu": "Assyria",
    "Nimrud": "Assyria",
    "Kuyunjik": "Assyria",
    "Qalat Sherqat": "Assyria",

    # Elam
    "Susa": "Elam",
    "Shush": "Elam",
    "Kabnak": "Elam",
    "Haft Tepe": "Elam",
    "Pārśa": "Elam",
    "Persepolis": "Elam",

    # Anatolia
    "Ḫattusa": "Anatolia",
    "Boğazkale": "Anatolia",
    "Kanesh": "Anatolia",
    "Kültepe": "Anatolia",
    "Alalakh": "Anatolia",

    # Syria
    "Mari": "Syria",
    "Ebla": "Syria",
    "Emar": "Syria",
    "Ugarit": "Syria",
    "Tell Hariri": "Syria",
    "Tell Mardikh": "Syria",
    "Tell Meskene": "Syria",
    "Ras Shamra": "Syria",
}

def get_provenience_region(prov: str) -> str:
    """Determine region for a provenience string."""
    if not prov:
        return "Unknown"

    # Check for known sites
    for site, region in SITE_REGION_MAP.items():
        if site.lower() in prov.lower():
            return region

    # Check for region hints in the string
    prov_lower = prov.lower()
    if "babylonia" in prov_lower:
        return "Babylonia"
    if "assyria" in prov_lower:
        return "Assyria"
    if "elam" in prov_lower or "persia" in prov_lower or "iran" in prov_lower:
        return "Elam"
    if "anatolia" in prov_lower or "turkey" in prov_lower or "hittite" in prov_lower:
        return "Anatolia"
    if "syria" in prov_lower:
        return "Syria"
    if "egypt" in prov_lower:
        return "Egypt"

    # Check if uncertain
    if "uncertain" in prov_lower or "unclear" in prov_lower or "unknown" in prov_lower:
        return "Unknown"

    return "Other"


# =============================================================================
# PERIOD MAPPINGS - Sort order and grouping
# =============================================================================

# Period sort order (approximate chronological)
PERIOD_SORT_ORDER = {
    "Pre-Uruk V": 1,
    "Uruk V": 2,
    "Uruk IV": 3,
    "Uruk III": 4,
    "Proto-Elamite": 5,
    "ED I-II": 10,
    "ED IIIa": 11,
    "ED IIIb": 12,
    "Ebla": 15,
    "Old Akkadian": 20,
    "Lagash II": 25,
    "Ur III": 30,
    "Early Old Babylonian": 35,
    "Old Babylonian": 40,
    "Old Assyrian": 45,
    "Middle Hittite": 50,
    "Middle Babylonian": 55,
    "Middle Assyrian": 60,
    "Middle Elamite": 65,
    "Early Neo-Babylonian": 70,
    "Neo-Assyrian": 75,
    "Neo-Elamite": 80,
    "Neo-Babylonian": 85,
    "Achaemenid": 90,
    "Hellenistic": 95,
    "Sassanian": 100,
    "First Millennium": 85,  # Approximate
    "Late Babylonian": 95,
}

def get_period_sort_order(period: str) -> int:
    """Get sort order for a period."""
    if not period:
        return 999

    # Check exact match (without date ranges)
    for key, order in PERIOD_SORT_ORDER.items():
        if key.lower() in period.lower():
            return order

    # Check for fake/uncertain
    if "fake" in period.lower() or "uncertain" in period.lower():
        return 998

    return 500  # Middle default


def get_period_group(period: str) -> str:
    """Get broader period group."""
    if not period:
        return "Unknown"

    period_lower = period.lower()

    if "uruk" in period_lower or "pre-uruk" in period_lower:
        return "Uruk Period"
    if "ed " in period_lower or "early dynastic" in period_lower:
        return "Early Dynastic"
    if "ebla" in period_lower:
        return "Early Bronze Age Syria"
    if "old akkadian" in period_lower or "lagash" in period_lower:
        return "Akkadian/Post-Akkadian"
    if "ur iii" in period_lower:
        return "Ur III"
    if "old babylonian" in period_lower or "early old babylonian" in period_lower:
        return "Old Babylonian"
    if "old assyrian" in period_lower:
        return "Old Assyrian"
    if "middle" in period_lower:
        return "Middle Bronze Age"
    if "neo-assyrian" in period_lower or "neo assyrian" in period_lower:
        return "Neo-Assyrian"
    if "neo-babylonian" in period_lower or "neo babylonian" in period_lower:
        return "Neo-Babylonian"
    if "achaemenid" in period_lower:
        return "Achaemenid"
    if "hellenistic" in period_lower or "seleucid" in period_lower:
        return "Hellenistic"
    if "sassanian" in period_lower:
        return "Late Antiquity"
    if "proto-elamite" in period_lower:
        return "Proto-Elamite"
    if "elamite" in period_lower:
        return "Elamite"
    if "hittite" in period_lower:
        return "Hittite"
    if "fake" in period_lower:
        return "Modern Fakes"

    return "Other"


# =============================================================================
# MAIN POPULATION FUNCTIONS
# =============================================================================

def populate_language_stats(conn: sqlite3.Connection):
    """Populate language_stats table."""
    print("Populating language_stats...")
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM language_stats")

    # Get all languages with counts
    cursor.execute("""
        SELECT language, COUNT(*) as cnt
        FROM artifacts
        WHERE language IS NOT NULL AND language != ''
        GROUP BY language
    """)

    now = int(time.time())
    rows = cursor.fetchall()

    for lang, count in rows:
        root = get_root_language(lang)
        cursor.execute("""
            INSERT OR REPLACE INTO language_stats (language, root_language, tablet_count, updated_at)
            VALUES (?, ?, ?, ?)
        """, (lang, root, count, now))

    conn.commit()
    print(f"  Inserted {len(rows)} language entries")


def populate_period_stats(conn: sqlite3.Connection):
    """Populate period_stats table."""
    print("Populating period_stats...")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM period_stats")

    cursor.execute("""
        SELECT period, COUNT(*) as cnt
        FROM artifacts
        WHERE period IS NOT NULL AND period != ''
        GROUP BY period
    """)

    now = int(time.time())
    rows = cursor.fetchall()

    for period, count in rows:
        sort_order = get_period_sort_order(period)
        period_group = get_period_group(period)
        cursor.execute("""
            INSERT OR REPLACE INTO period_stats (period, period_group, sort_order, tablet_count, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (period, period_group, sort_order, count, now))

    conn.commit()
    print(f"  Inserted {len(rows)} period entries")


def populate_provenience_stats(conn: sqlite3.Connection):
    """Populate provenience_stats table."""
    print("Populating provenience_stats...")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM provenience_stats")

    cursor.execute("""
        SELECT provenience, COUNT(*) as cnt
        FROM artifacts
        WHERE provenience IS NOT NULL AND provenience != ''
        GROUP BY provenience
    """)

    now = int(time.time())
    rows = cursor.fetchall()

    for prov, count in rows:
        region = get_provenience_region(prov)
        cursor.execute("""
            INSERT OR REPLACE INTO provenience_stats (provenience, region, tablet_count, updated_at)
            VALUES (?, ?, ?, ?)
        """, (prov, region, count, now))

    conn.commit()
    print(f"  Inserted {len(rows)} provenience entries")


def populate_genre_stats(conn: sqlite3.Connection):
    """Populate genre_stats table."""
    print("Populating genre_stats...")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM genre_stats")

    cursor.execute("""
        SELECT genre, COUNT(*) as cnt
        FROM artifacts
        WHERE genre IS NOT NULL AND genre != ''
        GROUP BY genre
    """)

    now = int(time.time())
    rows = cursor.fetchall()

    for genre, count in rows:
        category = get_genre_category(genre)
        cursor.execute("""
            INSERT OR REPLACE INTO genre_stats (genre, category, tablet_count, updated_at)
            VALUES (?, ?, ?, ?)
        """, (genre, category, count, now))

    conn.commit()
    print(f"  Inserted {len(rows)} genre entries")


def print_summary(conn: sqlite3.Connection):
    """Print summary of populated stats."""
    cursor = conn.cursor()

    print("\n=== Filter Stats Summary ===\n")

    # Language summary
    print("Languages by root:")
    cursor.execute("""
        SELECT root_language, SUM(tablet_count) as total, COUNT(*) as variants
        FROM language_stats
        GROUP BY root_language
        ORDER BY total DESC
    """)
    for root, total, variants in cursor.fetchall():
        print(f"  {root}: {total:,} tablets ({variants} variants)")

    # Genre summary
    print("\nGenres by category:")
    cursor.execute("""
        SELECT category, SUM(tablet_count) as total, COUNT(*) as variants
        FROM genre_stats
        GROUP BY category
        ORDER BY total DESC
    """)
    for cat, total, variants in cursor.fetchall():
        print(f"  {cat}: {total:,} tablets ({variants} genres)")

    # Provenience summary
    print("\nProveniences by region:")
    cursor.execute("""
        SELECT region, SUM(tablet_count) as total, COUNT(*) as sites
        FROM provenience_stats
        GROUP BY region
        ORDER BY total DESC
    """)
    for region, total, sites in cursor.fetchall():
        print(f"  {region}: {total:,} tablets ({sites} sites)")

    # Period summary
    print("\nPeriods by group:")
    cursor.execute("""
        SELECT period_group, SUM(tablet_count) as total, COUNT(*) as periods
        FROM period_stats
        GROUP BY period_group
        ORDER BY MIN(sort_order)
    """)
    for group, total, periods in cursor.fetchall():
        print(f"  {group}: {total:,} tablets ({periods} periods)")


def main():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        populate_language_stats(conn)
        populate_period_stats(conn)
        populate_provenience_stats(conn)
        populate_genre_stats(conn)
        print_summary(conn)
        print("\nFilter stats population complete!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
