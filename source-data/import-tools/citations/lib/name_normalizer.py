#!/usr/bin/env python3
"""
Scholar name normalization for cross-source deduplication.

Handles Assyriology-specific challenges:
- Diacritics: "Zólyomi" vs "Zolyomi"
- Particles: "von Soden" vs "Soden, W. von"
- Initials: "D. R. Frayne" vs "Douglas R. Frayne"
- BibTeX format: "Englund, Robert K. & Nissen, Hans J."
"""

import re
import unicodedata
from dataclasses import dataclass

# Name particles that should sort under the following word
PARTICLES = {"von", "van", "de", "del", "della", "di", "du", "le", "la", "al", "el"}


@dataclass
class NormalizedName:
    surname: str
    given: str
    initials: str
    normalized_key: str  # For fast dedup lookup
    raw: str


def strip_diacritics(text: str) -> str:
    """Remove diacritics: Jägersma -> Jagersma, Zólyomi -> Zolyomi."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def extract_initials(given: str) -> str:
    """Extract initials from given names: 'Douglas R.' -> 'dr', 'D. R.' -> 'dr'."""
    if not given:
        return ""
    parts = re.split(r"[\s.]+", given.strip())
    return "".join(p[0].lower() for p in parts if p)


def parse_name(raw: str) -> NormalizedName:
    """
    Parse a scholar name into normalized components.

    Handles formats:
    - "Surname, Given Names"  (BibTeX style)
    - "Given Names Surname"   (natural order)
    - "von Soden, Wolfram"    (particles)
    - "D. R. Frayne"          (initials)
    """
    raw = raw.strip()
    if not raw:
        return NormalizedName("", "", "", "", raw)

    surname = ""
    given = ""

    if "," in raw:
        # BibTeX format: "Surname, Given" or "von Soden, Wolfram"
        parts = raw.split(",", 1)
        surname = parts[0].strip()
        given = parts[1].strip() if len(parts) > 1 else ""

        # Check if particle is at the end of given: "Soden, W. von"
        given_words = given.split()
        if given_words and given_words[-1].lower() in PARTICLES:
            particle = given_words.pop()
            given = " ".join(given_words)
            surname = f"{particle} {surname}"
    else:
        # Natural order: "Given Surname" or "D. R. Frayne"
        words = raw.split()
        if len(words) == 1:
            surname = words[0]
        else:
            # Find where surname starts (skip particles and given names)
            # Heuristic: last capitalized non-particle word is surname
            surname_idx = len(words) - 1
            # Check for trailing particles that belong to surname
            while surname_idx > 0 and words[surname_idx - 1].lower() in PARTICLES:
                surname_idx -= 1
            surname = " ".join(words[surname_idx:])
            given = " ".join(words[:surname_idx])

    # Extract particle from surname if present at start
    surname_words = surname.split()
    particle = ""
    if len(surname_words) > 1 and surname_words[0].lower() in PARTICLES:
        particle = surname_words[0]
        surname_core = " ".join(surname_words[1:])
    else:
        surname_core = surname

    initials = extract_initials(given)

    # Build normalized key: lowercase, no diacritics, "surname_initials"
    norm_surname = strip_diacritics(surname_core).lower().strip()
    norm_key = f"{norm_surname}_{initials}" if initials else norm_surname

    return NormalizedName(
        surname=surname,
        given=given,
        initials=initials,
        normalized_key=norm_key,
        raw=raw,
    )


def parse_author_string(authors_str: str) -> list[NormalizedName]:
    """
    Parse a BibTeX-style author string into individual names.

    Handles: "Englund, Robert K. & Nissen, Hans J."
    Also handles: "Englund, Robert K.; Nissen, Hans J."
    """
    if not authors_str:
        return []

    # Split on " & ", " and ", or ";"
    parts = re.split(r"\s*(?:&|;|\band\b)\s*", authors_str)
    return [parse_name(p) for p in parts if p.strip()]


def names_match(a: NormalizedName, b: NormalizedName, threshold: float = 0.85) -> float:
    """
    Compare two normalized names and return confidence score.

    Returns:
        0.0 - 1.0 confidence that these are the same person.
    """
    if not a.normalized_key or not b.normalized_key:
        return 0.0

    # Exact key match
    if a.normalized_key == b.normalized_key:
        return 1.0

    # Same surname, compatible initials
    a_surname = strip_diacritics(a.surname).lower()
    b_surname = strip_diacritics(b.surname).lower()

    # Strip particles for comparison
    for p in PARTICLES:
        a_surname = re.sub(rf"^{p}\s+", "", a_surname)
        b_surname = re.sub(rf"^{p}\s+", "", b_surname)

    if a_surname != b_surname:
        return 0.0

    # Surnames match -- check initials compatibility
    if not a.initials or not b.initials:
        # One has no initials -- surname match only
        return 0.7

    # Check if one set of initials is a prefix of the other
    # "dr" matches "d" (D. Frayne vs D. R. Frayne)
    shorter = min(a.initials, b.initials, key=len)
    longer = max(a.initials, b.initials, key=len)

    if longer.startswith(shorter):
        return 0.9

    if shorter == longer:
        return 1.0

    # Different initials with same surname -- likely different people
    return 0.3
