"""Unit tests for the dialect-label map (#186).

A *language* and a *dialect* are different axes of a lemma. ORACC tags many
Akkadian lemmas with an opaque dialect code (e.g. "oldbab") naming a historical
variety — "Old Babylonian Akkadian" is the Akkadian *language* in its Old
Babylonian *dialect*. ``dialect_label`` turns those codes into the names a
reader recognises so the lemma page can show "Akkadian · Old Babylonian".

These tests are pure in-memory — no HTTP, no database. They lock the contract:
known codes map to human names, unknown codes fall through honestly (we surface
what the data carries rather than inventing a label), and absent values yield an
empty string so the template takes the standard empty-state path.
"""

from api.repositories.lexical_repo import DIALECT_LABELS, dialect_label


def test_known_codes_map_to_human_labels():
    assert dialect_label("oldbab") == "Old Babylonian"
    assert dialect_label("stdbab") == "Standard Babylonian"
    assert dialect_label("neoass") == "Neo-Assyrian"


def test_unknown_code_falls_through_to_raw_value():
    # Honest: an untagged/novel code is surfaced as-is, never silently dropped
    # or mislabelled.
    assert dialect_label("zzznew") == "zzznew"


def test_absent_value_is_empty_string():
    # Empty / null → "" so the template uses the #189 empty-state path rather
    # than printing a stray code.
    assert dialect_label(None) == ""
    assert dialect_label("") == ""


def test_label_map_covers_the_corpus_codes():
    # The dialect codes actually present in lexical_lemmas (per the #186 data
    # gate) must all carry a human label, so no real lemma shows a bare code.
    corpus_codes = {
        "stdbab",
        "neoass",
        "oldbab",
        "mbperi",
        "neobab",
        "ltebab",
        "emesal",
        "midass",
        "midbab",
        "earakk",
        "oldass",
    }
    missing = corpus_codes - set(DIALECT_LABELS)
    assert not missing, f"corpus dialect codes without a label: {sorted(missing)}"
