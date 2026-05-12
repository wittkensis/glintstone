"""Unit tests for ingestion/images/parser.py.

Uses inline HTML snippets that mirror cdli.earth's rendering so the test
doesn't depend on network access. If CDLI changes its HTML structure, these
tests will start failing — that's a feature.
"""

from __future__ import annotations

from ingestion.images.parser import (
    build_credit_line,
    derive_copyright_holder,
    parse_artifact_page,
)


SAMPLE_PAGE_P000001 = """
<html><body>
  <div class="visual-asset">
    <a href="/artifacts/1/reader/88909">
      <img src="/dl/tn_photo/P000001.jpg" alt="photo" />
    </a>
    <p>Photo</p>
    <p>© Vorderasiatisches Museum, Berlin, Germany</p>
    <a href="/dl/photo/P000001.jpg">Download</a>
  </div>
  <div class="visual-asset">
    <a href="/artifacts/1/reader/4">
      <img src="/dl/tn_lineart/P000001_l.jpg" alt="lineart" />
    </a>
    <p>Lineart</p>
    <p>© [see publications]</p>
    <a href="/dl/lineart/P000001_l.jpg">Download</a>
  </div>
</body></html>
"""


class TestParseArtifactPage:
    def test_detects_both_photo_and_lineart(self) -> None:
        manifest = parse_artifact_page(SAMPLE_PAGE_P000001, "P000001")
        types = {img.image_type for img in manifest.images}
        assert types == {"photo", "lineart"}

    def test_captures_cdli_artifact_id_from_reader_url(self) -> None:
        manifest = parse_artifact_page(SAMPLE_PAGE_P000001, "P000001")
        assert manifest.cdli_artifact_id == 1

    def test_canonical_full_urls_are_absolute(self) -> None:
        manifest = parse_artifact_page(SAMPLE_PAGE_P000001, "P000001")
        for img in manifest.images:
            assert img.full_url.startswith("https://cdli.earth/")

    def test_attribution_captured_verbatim(self) -> None:
        manifest = parse_artifact_page(SAMPLE_PAGE_P000001, "P000001")
        attributions = [img.attribution_raw for img in manifest.images]
        assert "© Vorderasiatisches Museum, Berlin, Germany" in attributions
        assert "© [see publications]" in attributions

    def test_empty_page_returns_empty_manifest(self) -> None:
        manifest = parse_artifact_page("<html></html>", "P000001")
        assert manifest.images == []
        assert manifest.cdli_artifact_id is None

    def test_p_number_mismatch_is_skipped(self) -> None:
        # If the page claims to be P000001 but the caller passed P999999,
        # the parser should not return rows for the wrong artifact.
        manifest = parse_artifact_page(SAMPLE_PAGE_P000001, "P999999")
        assert manifest.images == []


class TestDeriveCopyrightHolder:
    def test_drops_copyright_symbol_and_trims(self) -> None:
        assert (
            derive_copyright_holder("© Vorderasiatisches Museum, Berlin")
            == "Vorderasiatisches Museum, Berlin"
        )

    def test_placeholder_attribution_returns_none(self) -> None:
        # Common CDLI placeholder when the rights holder isn't filed at
        # image level — real attribution lives in the publications block.
        assert derive_copyright_holder("© [see publications]") is None

    def test_none_input(self) -> None:
        assert derive_copyright_holder(None) is None


class TestBuildCreditLine:
    def test_with_attribution(self) -> None:
        assert (
            build_credit_line("© British Museum")
            == "Image courtesy of British Museum, via CDLI"
        )

    def test_placeholder_uses_pending_text(self) -> None:
        line = build_credit_line("© [see publications]")
        assert line is not None
        assert "pending" in line.lower()

    def test_none_uses_pending_text(self) -> None:
        line = build_credit_line(None)
        assert line is not None
        assert "pending" in line.lower()
