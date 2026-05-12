"""Parse cdli.earth artifact-page HTML to extract image manifest + attribution.

We do NOT cache the HTML body. We extract what we need (image refs + per-image
attribution) and discard. attribution_raw is preserved verbatim so a future
re-parse can re-derive copyright_holder without re-fetching.

The CDLI artifact page shows, for each visual asset:
- A thumbnail at /dl/tn_photo/P######.jpg or /dl/tn_lineart/P######_l.jpg
- A reader URL at /artifacts/<id>/reader/<reader_id>
- A copyright string like "© Vorderasiatisches Museum, Berlin, Germany"

The HTML structure is server-rendered. We use HTMLParser from the stdlib
to avoid adding a BeautifulSoup dependency for a single-purpose parse.
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
    full_url: str  # canonical /dl/photo/<P>.jpg or /dl/lineart/<P>_l.jpg
    thumbnail_url: Optional[str]  # /dl/tn_photo/... if present on the listing
    attribution_raw: Optional[str]  # exact copyright string shown alongside this image


@dataclass(frozen=True)
class ArtifactImageManifest:
    p_number: str
    cdli_artifact_id: Optional[int]
    images: list[ImageRef] = field(default_factory=list)


# CDLI URL fragments we look for in href attributes
_PHOTO_FULL_RE = re.compile(r"/dl/photo/(P\d+)\.jpg", re.IGNORECASE)
_PHOTO_THUMB_RE = re.compile(r"/dl/tn_photo/(P\d+)\.jpg", re.IGNORECASE)
_LINEART_FULL_RE = re.compile(r"/dl/lineart/(P\d+)_l\.jpg", re.IGNORECASE)
_LINEART_THUMB_RE = re.compile(r"/dl/tn_lineart/(P\d+)_l\.jpg", re.IGNORECASE)
_READER_RE = re.compile(r"/artifacts/(\d+)/reader/(\d+)")
_COPYRIGHT_RE = re.compile(r"©\s*[^<\n]+")


def parse_artifact_page(html: str, p_number: str) -> ArtifactImageManifest:
    """Extract image manifest from a CDLI artifact page HTML body.

    Best-effort: CDLI's HTML structure may evolve. If parsing fails to find any
    images, the caller should log a dead-letter rather than retrying.
    """
    parser = _ArtifactPageParser(p_number=p_number)
    parser.feed(html)
    parser.close()

    cdli_artifact_id = _first_reader_artifact_id(html)
    return ArtifactImageManifest(
        p_number=p_number,
        cdli_artifact_id=cdli_artifact_id,
        images=parser.finalize(),
    )


def _first_reader_artifact_id(html: str) -> Optional[int]:
    m = _READER_RE.search(html)
    return int(m.group(1)) if m else None


class _ArtifactPageParser(HTMLParser):
    """Walks the HTML once collecting candidate image rows.

    The CDLI page renders each visual asset in a container that includes
    (a) a link to /dl/photo or /dl/lineart, (b) optionally a link to a
    /artifacts/<id>/reader/<n> viewer, and (c) a copyright string nearby.

    Strategy: greedily collect every image URL and every © string in order,
    then pair them up in finalize() by position.
    """

    def __init__(self, p_number: str) -> None:
        super().__init__()
        self.p_number = p_number
        self._found_full: list[ImageRef] = []
        self._reader_ids: list[int] = []
        self._copyright_strings: list[str] = []
        self._pending_thumb_for: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag not in ("a", "img"):
            return
        attr_map = {k: v for k, v in attrs if v}
        for url in attr_map.values():
            self._absorb_url(url)

    def handle_data(self, data: str) -> None:
        # Strip any extracted copyright strings from the visible text stream.
        for m in _COPYRIGHT_RE.finditer(data):
            text = m.group(0).strip()
            text = re.sub(r"\s+", " ", text)
            self._copyright_strings.append(text)

    def _absorb_url(self, url: str) -> None:
        if (
            (m := _READER_RE.search(url))
            and self.p_number in url
            or (m := _READER_RE.search(url))
        ):
            reader_id = int(m.group(2))
            if reader_id not in self._reader_ids:
                self._reader_ids.append(reader_id)
        if (m := _PHOTO_FULL_RE.search(url)) and m.group(
            1
        ).upper() == self.p_number.upper():
            self._found_full.append(
                ImageRef(
                    image_type="photo",
                    cdli_reader_id=None,
                    full_url=_canonical(url),
                    thumbnail_url=self._pending_thumb_for.get("photo"),
                    attribution_raw=None,
                )
            )
        elif (m := _PHOTO_THUMB_RE.search(url)) and m.group(
            1
        ).upper() == self.p_number.upper():
            self._pending_thumb_for["photo"] = _canonical(url)
        elif (m := _LINEART_FULL_RE.search(url)) and m.group(
            1
        ).upper() == self.p_number.upper():
            self._found_full.append(
                ImageRef(
                    image_type="lineart",
                    cdli_reader_id=None,
                    full_url=_canonical(url),
                    thumbnail_url=self._pending_thumb_for.get("lineart"),
                    attribution_raw=None,
                )
            )
        elif (m := _LINEART_THUMB_RE.search(url)) and m.group(
            1
        ).upper() == self.p_number.upper():
            self._pending_thumb_for["lineart"] = _canonical(url)

    def finalize(self) -> list[ImageRef]:
        """Pair up reader IDs and copyright strings with their image rows.

        Pairing is positional — the i-th image gets the i-th reader_id and
        the i-th copyright. CDLI renders these in a stable order (photos
        first, then line drawings). Where copyright is "© [see publications]"
        we preserve verbatim so the UI can show "credit pending."
        """
        out: list[ImageRef] = []
        for i, ref in enumerate(self._found_full):
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
