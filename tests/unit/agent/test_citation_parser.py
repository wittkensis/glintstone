"""Citation parser + validator tests."""

from core.agent.citation_parser import (
    SynthesisGroundingError,
    extract_marker_ns,
    validate,
)


def test_extract_marker_ns_simple():
    assert extract_marker_ns("This is fact [1] and [3].") == [1, 3]


def test_extract_marker_ns_duplicates():
    assert extract_marker_ns("[1] and [1] again.") == [1, 1]


def test_validate_accepts_well_formed_text():
    text = "An Ur III administrative tablet from Drehem [1][2][3]. Mentions barley [4]."
    valid_ns = {1, 2, 3, 4}
    result = validate(text, valid_ns, best_guess_allowed=False)
    assert result.ok, result.complaint


def test_validate_rejects_unknown_n():
    text = "An Ur III tablet [1][99]."
    valid_ns = {1, 2, 3}
    result = validate(text, valid_ns, best_guess_allowed=False)
    assert not result.ok
    assert 99 in (result.unknown_ns or [])
    assert "99" in result.complaint


def test_validate_rejects_uncited_factual_claim():
    text = "This tablet is Ur III. It mentions barley."
    valid_ns = {1, 2, 3}
    result = validate(text, valid_ns, best_guess_allowed=False)
    assert not result.ok
    assert (
        "factual claims without [n]" in result.complaint.lower()
        or result.uncited_sentences
    )


def test_validate_rejects_hypothesis_when_not_allowed():
    text = "An Ur III tablet [1]. (hypothesis) Resembles silver-distribution tablets [2][3][4]."
    valid_ns = {1, 2, 3, 4}
    result = validate(text, valid_ns, best_guess_allowed=False)
    assert not result.ok
    assert "[BEST_GUESS]" in result.complaint


def test_validate_accepts_hypothesis_when_allowed():
    text = "An Ur III tablet [1]. (hypothesis) Resembles silver-distribution tablets [2][3][4]."
    valid_ns = {1, 2, 3, 4}
    result = validate(text, valid_ns, best_guess_allowed=True)
    assert result.ok, result.complaint


def test_validate_rejects_forbidden_hypothesis_phrasing():
    text = "An Ur III tablet [1]. (hypothesis) This token is Šamaš [2]."
    valid_ns = {1, 2}
    result = validate(text, valid_ns, best_guess_allowed=True)
    assert not result.ok
    assert "resembles" in result.complaint.lower()


def test_validate_rejects_too_long_output():
    sentences = " ".join("Fact about it [1]." for _ in range(8))
    valid_ns = {1}
    result = validate(sentences, valid_ns, best_guess_allowed=False)
    assert not result.ok
    assert "Maximum is 5" in result.complaint


def test_synthesis_grounding_error_carries_context():
    err = SynthesisGroundingError(last_complaint="bad citation", last_text="some text")
    assert "bad citation" in str(err)
    assert err.last_complaint == "bad citation"
    assert err.last_text == "some text"
