"""
CAD Entry Extraction Schema for langextract.

This module defines the data structures and extraction configuration
for parsing Chicago Assyrian Dictionary entries.

Schema based on analysis of CAD entry format:
- Headword with part of speech
- Multiple meanings (numbered a, b, c or 1', 2')
- Attestations with text references and translations
- Cross-references to other entries
- Sumerian logograms
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CADAttestation:
    """A textual attestation/citation for a word meaning."""
    text_reference: str  # e.g., "CT 25 50:3", "TCL 4 105:5"
    akkadian_text: Optional[str] = None  # The quoted Akkadian text
    translation: Optional[str] = None  # English translation if provided
    period: Optional[str] = None  # e.g., "OB", "SB", "NA", "NB", "MA"


@dataclass
class CADMeaning:
    """A meaning/definition of a dictionary entry."""
    position: str  # e.g., "a", "b", "1'", "2'"
    definition: str  # The meaning/definition text
    semantic_domain: Optional[str] = None  # e.g., "legal", "medical"
    context: Optional[str] = None  # e.g., "in glass texts"
    attestations: List[CADAttestation] = field(default_factory=list)


@dataclass
class CADCrossReference:
    """A cross-reference to another dictionary entry."""
    to_headword: str  # Target headword
    reference_type: str  # "see", "cf.", "compare", "variant"


@dataclass
class CADLogogram:
    """A Sumerian logogram equivalent."""
    sumerian_form: str  # e.g., "A.BÁR", "ŠU.KAL"
    pronunciation: Optional[str] = None  # Reading/pronunciation gloss
    context: Optional[str] = None  # Usage context


@dataclass
class CADEntry:
    """A complete dictionary entry."""
    headword: str  # The Akkadian word (transliterated)
    part_of_speech: Optional[str] = None  # e.g., "s.", "v.", "adj."
    meanings: List[CADMeaning] = field(default_factory=list)
    logograms: List[CADLogogram] = field(default_factory=list)
    cross_references: List[CADCrossReference] = field(default_factory=list)


# Extraction configuration for langextract
EXTRACTION_CONFIG = {
    "entity_types": [
        {
            "name": "CADEntry",
            "description": "A dictionary entry for an Akkadian word",
            "schema": CADEntry,
        },
    ],

    "extraction_prompt": """
You are extracting dictionary entries from the Chicago Assyrian Dictionary (CAD).

Each entry follows this structure:
- HEADWORD followed by part of speech (s. = noun, v. = verb, adj. = adjective, adv. = adverb)
- Optional Sumerian logograms in CAPS (e.g., A.BÁR, ŠU.KAL)
- Numbered meanings (a, b, c or 1', 2')
- Attestations with text references like "CT 25 50:3" or "TCL 4 105:5"
- Cross-references starting with "cf." or "see"

Period abbreviations:
- OA = Old Assyrian
- OB = Old Babylonian
- MA = Middle Assyrian
- MB = Middle Babylonian
- NA = Neo-Assyrian
- NB = Neo-Babylonian
- SB = Standard Babylonian

Extract each complete entry with all its meanings, attestations, and cross-references.
Preserve the exact headword spelling including diacritics (ā, ē, ī, ū, š, ṣ, ṭ, ḫ).
""",

    "model_settings": {
        "temperature": 0.1,  # Low temperature for consistent extraction
        "max_output_tokens": 8192,
    },

    "chunking": {
        "strategy": "semantic",  # Chunk by entry boundaries
        "overlap_tokens": 200,  # Overlap to catch entries split across chunks
    },
}


# Period mapping for normalization
PERIOD_CODES = {
    "OA": "Old Assyrian",
    "OB": "Old Babylonian",
    "MA": "Middle Assyrian",
    "MB": "Middle Babylonian",
    "NA": "Neo-Assyrian",
    "NB": "Neo-Babylonian",
    "SB": "Standard Babylonian",
    "jB": "Late Babylonian",
    "NA/NB": "Neo-Assyrian/Neo-Babylonian",
}


# Part of speech mapping
POS_CODES = {
    "s.": "noun",
    "v.": "verb",
    "adj.": "adjective",
    "adv.": "adverb",
    "prep.": "preposition",
    "conj.": "conjunction",
    "interj.": "interjection",
    "num.": "numeral",
}
