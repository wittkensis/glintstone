"""Unit tests for #330 word→token alignment in api.services.atf_parser.

The parser stamps ``tokens.id`` onto ``.atf-word`` objects (consumed by the
frontend interpret_token feature) — but ONLY where a line's content words align
1:1 with its tokens AND every pair's normalized surface form matches. A wrong
map mis-attributes a scholarly interpretation, so the guard refuses (stamps
nothing) on any mismatch. These cases are distilled from real prod data
(P229547 aligns cleanly; P336245 / broken lines refuse).
"""

from __future__ import annotations

from api.services.atf_parser import parse_atf_response


def _tokens(*forms: str, start_id: int = 1000, start_pos: int = 0) -> list[dict]:
    """Build ordered token rows (id, position, raw_form)."""
    return [
        {"id": start_id + i, "position": start_pos + i, "raw_form": f}
        for i, f in enumerate(forms)
    ]


def _words(parsed: dict) -> list[dict]:
    """Flatten all word objects from the first content line of the response."""
    line = parsed["surfaces"][0]["columns"][0]["lines"][0]
    return line["words"]


def _line(line_id: int, raw: str) -> dict:
    return {
        "line_id": line_id,
        "line_number": "1",
        "raw_atf": raw,
        "is_ruling": False,
        "is_blank": False,
        "surface_type": "obverse",
        "column_number": 1,
    }


def test_clean_line_aligns_and_stamps_in_order():
    """Every content word gets the correct token_id (real-data shape)."""
    raw = "lu₂ gub-ba mu-uh₂-hu-um"
    tokens = {5: _tokens("lu₂", "gub-ba", "mu-uh₂-hu-um", start_id=9220371)}
    parsed = parse_atf_response([_line(5, raw)], tokens)
    words = [w for w in _words(parsed) if w["type"] in ("word", "logogram")]
    assert [w["text"] for w in words] == ["lu₂", "gub-ba", "mu-uh₂-hu-um"]
    assert [w["token_id"] for w in words] == [9220371, 9220372, 9220373]


def test_subscript_and_case_normalization_still_aligns():
    """za-ab-bu-u₂ (word) vs za-ab-bu-u₂ (token), SAL logogram vs SAL token."""
    raw = "⸢SAL⸣ lu₂-ni₂-su-ub-ba za-ba-a-tum"
    tokens = {7: _tokens("SAL", "lu₂-ni₂-su-ub-ba", "za-ba-a-tum", start_id=200)}
    parsed = parse_atf_response([_line(7, raw)], tokens)
    words = [w for w in _words(parsed) if w["type"] in ("word", "logogram")]
    assert [w.get("token_id") for w in words] == [200, 201, 202]


def test_break_placeholder_tokens_are_ignored_when_counting():
    """ORACC 'x' break tokens are dropped; parser collapses [x x x] to one word.

    The single ``broken`` word carries no token_id, and the real words align.
    """
    raw = "[x x x] a-di AGA"
    # ORACC emits per-x break tokens plus the two real words.
    tokens = {
        9: [
            {"id": 1, "position": 0, "raw_form": "x"},
            {"id": 2, "position": 1, "raw_form": "x"},
            {"id": 3, "position": 2, "raw_form": "x"},
            {"id": 50, "position": 31, "raw_form": "a-di"},
            {"id": 51, "position": 32, "raw_form": "AGA"},
        ]
    }
    parsed = parse_atf_response([_line(9, raw)], tokens)
    words = _words(parsed)
    broken = [w for w in words if w["type"] == "broken"]
    real = [w for w in words if w["type"] in ("word", "logogram")]
    assert broken and "token_id" not in broken[0]
    assert [w.get("token_id") for w in real] == [50, 51]


def test_count_mismatch_refuses_whole_line():
    """Parser yields more content words than real tokens ⇒ stamp nothing."""
    # Determinative split: parser sees {d} + EN as a determinative word; if the
    # token stream collapses differently the counts diverge → refuse.
    raw = "a-di AGA {d}EN extra-word"
    tokens = {11: _tokens("a-di", "AGA", "{d}EN", start_id=300)}  # 3 tokens, 4 words
    parsed = parse_atf_response([_line(11, raw)], tokens)
    for w in _words(parsed):
        assert "token_id" not in w, f"mis-mapped on count mismatch: {w}"


def test_form_mismatch_refuses_whole_line():
    """Counts match but a form disagrees ([i]-na→-na vs i-na) ⇒ stamp nothing."""
    raw = "[i]-na UGU"  # parser yields '-na' for the broken-bracket word
    tokens = {13: _tokens("i-na", "UGU", start_id=400)}
    parsed = parse_atf_response([_line(13, raw)], tokens)
    for w in _words(parsed):
        assert "token_id" not in w, f"mis-mapped on form mismatch: {w}"


def test_no_tokens_supplied_leaves_words_unstamped():
    """Backwards compatible: payloads predating the join carry no token_id."""
    parsed = parse_atf_response([_line(1, "lu₂ gub-ba")], None)
    for w in _words(parsed):
        assert "token_id" not in w
