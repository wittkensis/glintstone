"""Parse cdli.earth artifact-page HTML to extract image manifest + attribution.

We do NOT cache the HTML body. We extract what we need (image refs + per-image
attribution) and discard. attribution_raw is preserved verbatim so a future
re-parse can re-derive copyright_holder without re-fetching.

The CDLI artifact page renders each visual asset as:
- A thumbnail ``<img src="/dl/tn_photo/P######.jpg">`` or ``/dl/tn_lineart/P######_l.jpg``
- A wrapping ``<a href="/artifacts/<id>/reader/<reader_id>">`` link
- A copyright string nearby like ``© Vorderasiatisches Museum, Berlin, Germany``
  (encoded in the source as the HTML entity ``&copy;``; HTMLParser with
  ``convert_charrefs=True`` decodes it before ``handle_data`` runs).

The HTML does NOT contain the full ``/dl/photo/<P>.jpg`` URL on the page (the
og:image meta tag does, but we don't rely on it). We construct the full URL
deterministically from the P-number and image_type.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Optional


@dataclass(frozen=True)
class ImageRef:
    image_type: str  # 'photo' | 'lineart' | 'other'
    cdli_reader_id: Optional[int]  # numeric ID from /artifacts/<id>/reader/<n>
    full_url: str  # constructed /dl/photo/<P>.jpg or /dl/lineart/<P>_l.jpg
    thumbnail_url: Optional[str]  # /dl/tn_photo or /dl/tn_lineart URL from the page
    attribution_raw: Optional[str]  # exact copyright string shown alongside


@dataclass(frozen=True)
class ArtifactImageManifest:
    p_number: str
    cdli_artifact_id: Optional[int]
    images: list[ImageRef] = field(default_factory=list)


_PHOTO_THUMB_RE = re.compile(r"/dl/tn_photo/(P\d+)\.jpg", re.IGNORECASE)
_LINEART_THUMB_RE = re.compile(r"/dl/tn_lineart/(P\d+)_l\.jpg", re.IGNORECASE)
_READER_RE = re.compile(r"/artifacts/(\d+)/reader/(\d+)")
_COPYRIGHT_RE = re.compile(r"©\s*[^<\n]+")


def parse_artifact_page(html: str, p_number: str) -> ArtifactImageManifest:
    """Extract image manifest from a CDLI artifact page HTML body.

    Best-effort: CDLI's HTML structure may evolve. If parsing fails to find any
    images for this P-number, the caller should log a dead-letter rather than
    retrying.
    """
    parser = _ArtifactPageParser(p_number=p_number)
    parser.feed(html)
    parser.close()

    return ArtifactImageManifest(
        p_number=p_number,
        cdli_artifact_id=_first_reader_artifact_id(html),
        images=parser.finalize(),
    )


def _first_reader_artifact_id(html: str) -> Optional[int]:
    m = _READER_RE.search(html)
    return int(m.group(1)) if m else None


def _construct_full_url(p_number: str, image_type: str) -> str:
    """Compose the canonical /dl/ URL for a P-number's primary photo or lineart.

    Lineart files use the ``_l`` suffix per CDLI convention.
    """
    if image_type == "lineart":
        return f"https://cdli.earth/dl/lineart/{p_number}_l.jpg"
    return f"https://cdli.earth/dl/photo/{p_number}.jpg"


class _ArtifactPageParser(HTMLParser):
    """Single-pass parser: collect thumbnail URLs, reader IDs, and © strings.

    Pairs them positionally in finalize() — CDLI renders Photo then Lineart
    in a stable order, so the i-th image gets the i-th reader_id and
    i-th copyright string.
    """

    def __init__(self, p_number: str) -> None:
        # convert_charrefs=True (default since Python 3.5) decodes &copy; → ©
        # before handle_data sees it, which is what _COPYRIGHT_RE expects.
        super().__init__(convert_charrefs=True)
        self.p_number = p_number
        self._images: list[ImageRef] = []
        self._reader_ids: list[int] = []
        self._copyright_strings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag not in ("a", "img"):
            return
        for _key, value in attrs:
            if value:
                self._absorb_url(value)

    def handle_data(self, data: str) -> None:
        for m in _COPYRIGHT_RE.finditer(data):
            text = re.sub(r"\s+", " ", m.group(0).strip())
            self._copyright_strings.append(text)

    def _absorb_url(self, url: str) -> None:
        if m := _READER_RE.search(url):
            reader_id = int(m.group(2))
            if reader_id not in self._reader_ids:
                self._reader_ids.append(reader_id)

        if m := _PHOTO_THUMB_RE.search(url):
            if m.group(1).upper() == self.p_number.upper():
                self._maybe_add_image("photo", _canonical(url))
        elif m := _LINEART_THUMB_RE.search(url):
            if m.group(1).upper() == self.p_number.upper():
                self._maybe_add_image("lineart", _canonical(url))

    def _maybe_add_image(self, image_type: str, thumb_url: str) -> None:
        # Idempotent: the same thumbnail can appear multiple times on the page
        # (gallery + dropdown), but it's still one image.
        if any(i.thumbnail_url == thumb_url for i in self._images):
            return
        self._images.append(
            ImageRef(
                image_type=image_type,
                cdli_reader_id=None,
                full_url=_construct_full_url(self.p_number, image_type),
                thumbnail_url=thumb_url,
                attribution_raw=None,
            )
        )

    def finalize(self) -> list[ImageRef]:
        out: list[ImageRef] = []
        for i, ref in enumerate(self._images):
            reader_id = self._reader_ids[i] if i < len(self._reader_ids) else None
            attribution = (
                self._copyright_strings[i] if i < len(self._copyright_strings) else None
            )
            out.append(
                ImageRef(
                    image_type=ref.image_type,
                    cdli_reader_id=reader_id,
                    full_url=ref.full_url,
                    thumbnail_url=ref.thumbnail_url,
                    attribution_raw=attribution,
                )
            )
        return out


def _canonical(url: str) -> str:
    """Make a path-only URL absolute against cdli.earth."""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"https://cdli.earth{url}"
    return url


def derive_copyright_holder(attribution_raw: Optional[str]) -> Optional[str]:
    """Derive a clean institution name from a raw attribution string.

    "© Vorderasiatisches Museum, Berlin, Germany" → "Vorderasiatisches Museum, Berlin, Germany"
    "© [see publications]" → None (placeholder, real attribution lives elsewhere)
    """
    if not attribution_raw:
        return None
    cleaned = attribution_raw.strip().lstrip("©").strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        return None
    return cleaned or None


def build_credit_line(attribution_raw: Optional[str]) -> Optional[str]:
    """Display-ready credit string for the UI."""
    holder = derive_copyright_holder(attribution_raw)
    if not holder:
        return "Image courtesy of CDLI — credit pending verification"
    return f"Image courtesy of {holder}, via CDLI"
