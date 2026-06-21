"""Parse ORACC credit prose into (name, role) attribution pairs (#261).

The attribution data for ORACC editions lives as unparsed prose in
``artifact_credits.credits_text`` — e.g.::

    Adapted from Manfried Dietrich, ... (SAA 17), 2003. Lemmatised by
    Mikko Luukko, 2009-11, as part of the ... project ... directed by
    Karen Radner.

This module turns that prose into a list of ``CreditMatch`` records
``(name, role)`` and provides the **exact** name-normalization used to match a
parsed name against ``scholars.normalized_name``.

Two hard rules, both load-bearing for scholar attribution accuracy
(CLAUDE.md: "Their careers depend on the data being accurate and properly
attributed"):

1.  **Pure functions, no DB.** The DB match/insert lives in the caller
    (backfill script + connector) so this module is trivially unit-testable.
2.  **Conservative by construction.** ``normalize_name`` reproduces the exact
    ``surname_initials`` form stored in ``scholars.normalized_name`` (verified
    globally unique across 86,504 rows). The caller attributes a parsed name
    ONLY when its normalized form matches exactly one scholar. Ambiguous or
    unmatched names are dropped, never guessed.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Roles in the junction's CHECK constraint (migration 050). Order here is the
# precedence used when the same name appears under two phrasings in one credit.
ROLE_LEMMATIZER = "lemmatizer"
ROLE_EDITOR = "editor"
ROLE_ADAPTER = "adapter"
ROLE_DIRECTOR = "director"
ROLE_CREATOR = "creator"
ROLE_CONTRIBUTOR = "contributor"

# Surname particles that are dropped from the surname token, mirroring the
# observed scholars.normalized_name forms ("von Bothmer, Dietrich" -> bothmer_d).
_PARTICLES = {
    "von",
    "van",
    "de",
    "der",
    "den",
    "del",
    "della",
    "di",
    "da",
    "du",
    "le",
    "la",
    "el",
    "al",
    "bin",
    "ibn",
    "ter",
    "ten",
}

# Honorifics / suffixes stripped before parsing a name token.
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}


@dataclass(frozen=True)
class CreditMatch:
    """One (name, role) pair lifted from a credit string, pre-DB-match."""

    name: str
    role: str


def normalize_name(raw: str) -> str:
    """Reduce a personal name to the ``surname_initials`` form used as the key
    in ``scholars.normalized_name`` (e.g. "Mikko Luukko" -> ``luukko_m``,
    "Luukko, Mikko" -> ``luukko_m``, "von Bothmer, Dietrich" -> ``bothmer_d``).

    Returns ``""`` when the input does not look like a person name (no surname,
    or only initials) — the caller treats an empty result as "no match".

    NOTE: the stored values sometimes carry a disambiguation digit suffix
    (``radner_k1``) added when a date was present on the source name. A parsed
    credit name has no such suffix, so it matches only the un-suffixed scholar.
    Since ``normalized_name`` is globally unique, an exact match is unambiguous;
    a name whose base form collides with a ``*_kN`` sibling simply matches the
    base-form scholar, which is the conservative, correct behaviour.
    """
    name = raw.strip()
    if not name:
        return ""

    # "Surname, Given" -> "Given Surname". Only the first comma matters; a
    # trailing date ("Radner, Karen 1972-") is handled by token cleaning below.
    if "," in name:
        surname_part, _, given_part = name.partition(",")
        name = f"{given_part.strip()} {surname_part.strip()}".strip()

    # ASCII-fold (Lüükko -> Luukko), keep hyphens and spaces.
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.replace("‐", "-").replace("‑", "-")  # fancy hyphens

    # Tokenise on whitespace; keep hyphenated surnames intact (meyer-dietrich).
    tokens = [t for t in re.split(r"\s+", name) if t]
    # Drop trailing date/lifespan tokens and honorific suffixes.
    cleaned: list[str] = []
    for tok in tokens:
        bare = re.sub(r"[^\w\-']", "", tok).lower()
        if not bare:
            continue
        if re.fullmatch(r"\d{3,4}(-\d{0,4})?", bare):  # 1972, 1972-, 1891-1952
            continue
        if bare in _SUFFIXES:
            continue
        cleaned.append(tok)

    if len(cleaned) < 2:
        return ""

    # Surname = last token (drop a leading particle if the surname is a single
    # particle-prefixed token like "van Driel" given as two tokens).
    surname_tok = cleaned[-1]
    given_toks = cleaned[:-1]
    # If the token before the surname is a particle, fold it away.
    while given_toks and given_toks[-1].lower().strip(".") in _PARTICLES:
        given_toks = given_toks[:-1]
    # Drop any leading particles in the given names too.
    given_toks = [g for g in given_toks if g.lower().strip(".") not in _PARTICLES]

    # Keep lowercase letters (incl. residual non-ASCII like ß, which the stored
    # normalizer preserves — "Groß" -> "groß", not "gros") and hyphens. NFKD
    # above already folded combining diacritics (ü -> u), matching the stored
    # forms; ß has no decomposition, so it survives here by design.
    surname = re.sub(r"[^\w\-]", "", surname_tok.lower(), flags=re.UNICODE)
    surname = surname.strip("_")
    if not surname or surname == "-":
        return ""

    # Initials = first letter of each given-name token, in order.
    initials = ""
    for g in given_toks:
        g_clean = re.sub(r"[^\w]", "", g.lower(), flags=re.UNICODE)
        if g_clean:
            initials += g_clean[0]
    if not initials:
        return ""

    return f"{surname}_{initials}"


# --- role phrase patterns -------------------------------------------------
#
# Each pattern captures the name span that follows the role phrase. The name
# span is then split on " and " / "&" / "," (handled by _split_names) so
# multi-author phrases ("by John Carnahan and Jeremie Peterson") yield both.
#
# A name span runs until a sentence/clause boundary: a period that ends a
# sentence, a comma followed by a 4-digit year, or " as part of", " for the",
# " for X project", etc. We stop the capture conservatively to avoid swallowing
# trailing prose into a "name".

# Boundary that terminates a name span. Kept deliberately tight.
_NAME_SPAN = r"(?P<names>.+?)"

# Citation-style span: the leading author of a bibliographic reference, which
# runs up to the first comma. "Adapted from Mikko Luukko, The Correspondence..."
# captures "Mikko Luukko"; "Adapted from Giovanni B. Lanfranchi and Simo
# Parpola, ..." captures "Giovanni B. Lanfranchi and Simo Parpola" — which
# _split_names then REJECTS (contains "and", ambiguous co-authorship), leaving
# it unattributed. Under-attribute rather than mis-attribute (the #261 mandate).
_CITE_SPAN = r"(?P<names>[^,]+)"
# A period only ends the name span when it is NOT a single-initial abbreviation
# ("Heather D. Baker" must not stop at "D."). The negative lookbehind rejects a
# period preceded by whitespace + a lone capital (i.e. an initial).
_STOP = (
    r"(?="
    r"\s*(?:(?<![\s][A-Z])[.;]|,\s*\d{4}"  # period (not an initial)/semicolon, or ", 2017"
    r"|\s+as\s+part\b|\s+for\s+the\b|\s+for\s+[A-Z]"  # " as part of", " for the/X project"
    r"|\s+and\s+released\b|\s+and\s+the\b"
    r"|\s+\(|$)"
    r")"
)

# Each entry: (role, compiled-pattern, citation_style).
#
# citation_style=False  -> a "by X (and Y)" list: split co-authors on and/&.
# citation_style=True   -> a bibliographic citation ("Adapted from <Author>,
#                          <Title>, <Year>"): take ONLY the single leading name
#                          up to the first comma, and do NOT split on "and"
#                          (the "and" almost always belongs to the title, not a
#                          second creditable person). This is the conservative
#                          choice — under-attribute rather than mis-attribute.
_ROLE_PATTERNS: list[tuple[str, re.Pattern[str], bool]] = [
    # "directed by Karen Radner"
    (ROLE_DIRECTOR, re.compile(r"directed\s+by\s+" + _NAME_SPAN + _STOP, re.I), False),
    # "Lemmatised/Lemmatized by X"  /  "lemmatized by X"
    (
        ROLE_LEMMATIZER,
        re.compile(r"lemmati[sz]ed\s+by\s+" + _NAME_SPAN + _STOP, re.I),
        False,
    ),
    # "Edition by X" / "Edited by X" / "Edition: X"
    (
        ROLE_EDITOR,
        re.compile(r"(?:edition|edited)\s*(?:by|:)\s*" + _NAME_SPAN + _STOP, re.I),
        False,
    ),
    # "Created by X"
    (ROLE_CREATOR, re.compile(r"created\s+by\s+" + _NAME_SPAN + _STOP, re.I), False),
    # "Adapted from <citation>" — citation-style: leading name only, no and-split.
    (
        ROLE_ADAPTER,
        re.compile(r"adapted\s+from\s+" + _CITE_SPAN, re.I),
        True,
    ),
    # "edition courtesy X" / "Identification X" -> generic contributor
    (
        ROLE_CONTRIBUTOR,
        re.compile(
            r"(?:edition\s+courtesy|identification)\s+" + _NAME_SPAN + _STOP, re.I
        ),
        False,
    ),
]

# Tokens that signal the captured span is an institution/project, not a person.
# These are dropped wholesale (we attribute people, conservatively).
_INSTITUTION_HINTS = re.compile(
    r"\b(project|university|institute|museum|college|programme|program|"
    r"foundation|chair|professorship|corpus|edition|press|gmbh|"
    r"and the|et al)\b",
    re.I,
)


def _is_plausible_person(head: str) -> bool:
    """A conservative personal-name gate: 2-4 words, no institution hints, and
    no all-caps title words. Rejects prose/titles so they never reach a match.
    """
    if not head or _INSTITUTION_HINTS.search(head):
        return False
    words = head.split()
    if len(words) < 2 or len(words) > 4:
        return False
    # Reject if any word (beyond a 1-2 char initial) is ALL CAPS — a sign the
    # span is a title fragment ("RIMB", "SAA") rather than a personal name.
    for w in words:
        bare = re.sub(r"[^A-Za-z]", "", w)
        if len(bare) > 2 and bare.isupper():
            return False
    return True


def _split_names(span: str, citation_style: bool) -> list[str]:
    """Split a captured name span into individual personal names.

    by-list style ("John Carnahan and Jeremie Peterson") -> both names.
    citation style ("Mikko Luukko") -> the single leading name; a citation span
    that still contains " and " / "&" is co-authored-ambiguous and REJECTED
    (returns []), per the under-attribute-don't-misattribute rule.
    """
    span = span.strip().strip(".,;:")
    if not span:
        return []

    if citation_style:
        # The leading author, up to the first comma (the rest is title/series).
        head = span.split(",")[0].strip().strip(".,;:")
        # Ambiguous co-authorship — leave unattributed rather than guess.
        if re.search(r"\s+and\s+|\s*&\s*", head, re.I):
            return []
        return [head] if _is_plausible_person(head) else []

    parts = re.split(r"\s+and\s+|\s*&\s*", span)
    out: list[str] = []
    for p in parts:
        head = p.split(",")[0].strip().strip(".,;:")
        if _is_plausible_person(head):
            out.append(head)
    return out


def parse_credits(text: str) -> list[CreditMatch]:
    """Extract ``(name, role)`` pairs from one credit string.

    De-duplicates on (normalized-ish name, role): if the same surname appears
    twice under the same role, it is emitted once. Different roles for the same
    person are kept (a scholar can be both lemmatizer and editor).
    """
    if not text or not text.strip():
        return []

    seen: set[tuple[str, str]] = set()
    out: list[CreditMatch] = []
    for role, pat, citation_style in _ROLE_PATTERNS:
        for m in pat.finditer(text):
            for name in _split_names(m.group("names"), citation_style):
                key = (name.lower(), role)
                if key in seen:
                    continue
                seen.add(key)
                out.append(CreditMatch(name=name, role=role))
    return out
