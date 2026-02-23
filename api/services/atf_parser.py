"""
ATF Parser Service
Transforms flat DB lines into structured surface/column/line format
for the ATF viewer. Port of the PHP ATFParser.
"""

import re
from collections import OrderedDict

# Surface display labels
SURFACE_LABELS: dict[str, str] = {
    "obverse": "Obverse",
    "reverse": "Reverse",
    "left_edge": "Left Edge",
    "right_edge": "Right Edge",
    "top_edge": "Top Edge",
    "bottom_edge": "Bottom Edge",
    "left": "Left Edge",
    "right": "Right Edge",
    "top": "Top",
    "bottom": "Bottom",
    "edge": "Edge",
    "face": "Face",
    "seal": "Seal",
}

# Determinative metadata
DETERMINATIVES: dict[str, dict] = {
    "d": {"type": "divine", "label": "divine name", "display": "\u1d48"},
    "f": {"type": "female", "label": "female name", "display": "\u1da0"},
    "m": {"type": "male", "label": "male name", "display": "\u1d50"},
    "ki": {"type": "place", "label": "place name", "display": "\u1d4f\u2071"},
    "disz": {"type": "count", "label": "count marker", "display": ""},
    "gesz": {
        "type": "wood",
        "label": "wooden object",
        "display": "\u1d4d\u1d49\u02e2\u1dbb",
    },
    "gi": {"type": "reed", "label": "reed object", "display": "\u1d4d\u2071"},
    "kusz": {
        "type": "leather",
        "label": "leather object",
        "display": "\u1d4f\u1d58\u02e2\u1dbb",
    },
    "tug2": {"type": "cloth", "label": "textile", "display": "\u1d57\u1d58\u1d4d"},
    "urud": {
        "type": "copper",
        "label": "copper/bronze",
        "display": "\u1d58\u02b3\u1d58\u1d48",
    },
    "na4": {"type": "stone", "label": "stone object", "display": "\u207f\u1d43\u2074"},
    "id2": {"type": "water", "label": "river/canal", "display": "\u2071\u1d48"},
    "u2": {"type": "plant", "label": "plant", "display": "\u1d58\u00b2"},
    "iri": {"type": "city", "label": "city", "display": "\u2071\u02b3\u2071"},
    "kur": {"type": "land", "label": "land/mountain", "display": "\u1d4f\u1d58\u02b3"},
    "lu2": {"type": "person", "label": "person", "display": ""},
}

# Characters valid inside a word token (regex character class)
_WORD_CHARS = re.compile(
    r"[a-zA-Z0-9šṣṭāēīūâêîûŠṢṬĀĒĪŪÂÊÎÛ₀₁₂₃₄₅₆₇₈₉()\-~@|#?!×+]",
    re.UNICODE,
)

# Subscript digit removal
_SUBSCRIPT_MAP = str.maketrans("", "", "₀₁₂₃₄₅₆₇₈₉")

# Numeric token pattern: e.g., 1(N01), 3(disz), 1/2(iku)
_NUMERIC_PATTERN = re.compile(r"^[\d/]+\([A-Za-z0-9_]+\)(?:[#?!]*)$")


def parse_atf_response(lines: list[dict]) -> dict:
    """Transform flat DB lines into structured surface/column/line format.

    Input: [{line_number, raw_atf, is_ruling, is_blank, surface_type, column_number}, ...]
    Output: {surfaces: [...], hasMultipleSurfaces, hasMultipleColumns}
    """
    # Group lines by (surface_type, column_number), preserving first-appearance order
    # Key: surface_type → OrderedDict[column_number → [lines]]
    surface_columns: OrderedDict[str, OrderedDict[int, list[dict]]] = OrderedDict()
    for line in lines:
        st = line.get("surface_type") or "obverse"
        col = line.get("column_number", 0)
        if st not in surface_columns:
            surface_columns[st] = OrderedDict()
        if col not in surface_columns[st]:
            surface_columns[st][col] = []
        surface_columns[st][col].append(line)

    surfaces = []
    for surface_type, col_groups in surface_columns.items():
        label = SURFACE_LABELS.get(surface_type, surface_type.replace("_", " ").title())

        columns = []
        for col_num, col_lines in col_groups.items():
            parsed_lines = []
            for db_line in col_lines:
                parsed = _parse_db_line(db_line)
                if parsed is not None:
                    parsed_lines.append(parsed)
            columns.append(
                {
                    "number": col_num,
                    "lines": parsed_lines,
                }
            )

        surfaces.append(
            {
                "name": surface_type,
                "label": label,
                "modifier": None,
                "columns": columns,
            }
        )

    has_multiple_columns = any(len(s["columns"]) > 1 for s in surfaces)

    return {
        "surfaces": surfaces,
        "hasMultipleSurfaces": len(surfaces) > 1,
        "hasMultipleColumns": has_multiple_columns,
    }


def _parse_db_line(db_line: dict) -> dict | None:
    """Parse a single DB row into a structured line object."""
    raw_atf = (db_line.get("raw_atf") or "").strip()
    line_number = db_line.get("line_number") or ""
    is_ruling = bool(db_line.get("is_ruling"))
    is_blank = bool(db_line.get("is_blank"))

    # State/dollar lines stored in raw_atf
    if raw_atf.startswith("$"):
        return {"type": "state", "text": raw_atf[1:].strip()}

    # Blank and ruling lines → state
    if is_blank and raw_atf:
        return {"type": "state", "text": raw_atf.lstrip("$ ").strip()}
    if is_blank:
        return None
    if is_ruling:
        return {"type": "state", "text": "ruling"}

    # Content line
    line_num_str = str(line_number)
    is_prime = "'" in line_num_str

    # Normalize line number to have trailing dot
    num_display = line_num_str.rstrip(".")
    if num_display:
        num_display += "."

    # Check for composite reference in content
    composite = None
    content = raw_atf
    composite_match = re.search(r">>(Q\d+)\s+(.+)$", content)
    if composite_match:
        composite = {
            "q_number": composite_match.group(1),
            "line": composite_match.group(2).strip(),
        }
        content = content[: composite_match.start()].strip()

    words = parse_words(content)

    return {
        "type": "content",
        "number": num_display,
        "raw": raw_atf,
        "words": words,
        "isPrime": is_prime,
        "composite": composite,
        "translations": {},
    }


def parse_words(text: str) -> list[dict]:
    """Tokenize ATF line content into word objects."""
    words = []
    pos = 0
    length = len(text)

    while pos < length:
        # Skip whitespace
        while pos < length and text[pos].isspace():
            pos += 1
        if pos >= length:
            break

        word, pos = _extract_next_word(text, pos)
        if word is not None:
            words.append(word)

    return words


def _extract_next_word(text: str, pos: int) -> tuple[dict | None, int]:
    """Extract the next word/token from text at given position."""
    length = len(text)
    if pos >= length:
        return None, pos

    char = text[pos]

    # Punctuation
    if char in (",", ".", ";", ":"):
        return {"type": "punctuation", "text": char, "lookup": None}, pos + 1

    # Broken text: [...]
    if char == "[":
        end = text.find("]", pos)
        if end != -1:
            content = text[pos : end + 1]
            return {
                "type": "broken",
                "text": content,
                "lookup": None,
                "inner": content.strip("[]"),
            }, end + 1

    # Logogram: _text_
    if char == "_":
        end = text.find("_", pos + 1)
        if end != -1:
            content = text[pos + 1 : end]
            return {
                "type": "logogram",
                "text": content,
                "lookup": normalize_lookup(content),
                "display": content,
            }, end + 1

    # Prefix determinative: {d}word
    if char == "{":
        end = text.find("}", pos)
        if end != -1:
            det = text[pos + 1 : end]
            new_pos = end + 1
            following, new_pos = _extract_word_chars(text, new_pos)

            det_info = DETERMINATIVES.get(
                det,
                {
                    "type": "other",
                    "label": det,
                    "display": f"({det})",
                },
            )

            return {
                "type": "determinative",
                "text": following,
                "lookup": normalize_lookup(following),
                "determinative": det,
                "detType": det_info["type"],
                "detLabel": det_info["label"],
                "detDisplay": det_info["display"],
                "position": "prefix",
            }, new_pos

    # Regular word (may have trailing determinative or damage markers)
    word, pos = _extract_word_chars(text, pos)
    if not word:
        # Skip unknown character
        return None, pos + 1

    # Check for trailing determinative: word{ki}
    if pos < length and text[pos] == "{":
        end = text.find("}", pos)
        if end != -1:
            det = text[pos + 1 : end]
            pos = end + 1

            det_info = DETERMINATIVES.get(
                det,
                {
                    "type": "other",
                    "label": det,
                    "display": f"({det})",
                },
            )

            return {
                "type": "determinative",
                "text": word,
                "lookup": normalize_lookup(word),
                "determinative": det,
                "detType": det_info["type"],
                "detLabel": det_info["label"],
                "detDisplay": det_info["display"],
                "position": "suffix",
            }, pos

    # Check if this is a numeric/metrological token (e.g. 1(N01), 3(disz))
    if _NUMERIC_PATTERN.match(word):
        return {
            "type": "word",
            "text": word,
            "lookup": None,
            "damaged": word.endswith("#"),
            "uncertain": False,
            "corrected": False,
        }, pos

    # Parse damage markers from end
    damaged = False
    uncertain = False
    corrected = False
    clean = word

    if clean.endswith("#"):
        damaged = True
        clean = clean.rstrip("#")
    if clean.endswith("?"):
        uncertain = True
        clean = clean.rstrip("?")
    if clean.endswith("!"):
        corrected = True
        clean = clean.rstrip("!")

    # Detect logograms by uppercase convention (all-caps, no hyphens)
    is_upper = clean == clean.upper() and clean.isalpha() and len(clean) > 1
    if is_upper:
        return {
            "type": "logogram",
            "text": word,
            "lookup": normalize_lookup(clean),
            "display": word,
        }, pos

    return {
        "type": "word",
        "text": word,
        "lookup": normalize_lookup(clean),
        "damaged": damaged,
        "uncertain": uncertain,
        "corrected": corrected,
    }, pos


def _extract_word_chars(text: str, pos: int) -> tuple[str, int]:
    """Extract consecutive word characters from position."""
    start = pos
    length = len(text)
    while pos < length and _WORD_CHARS.match(text[pos]):
        pos += 1
    return text[start:pos], pos


def normalize_lookup(word: str) -> str | None:
    """Normalize a word for dictionary lookup."""
    if not word:
        return None

    # Remove damage markers
    word = re.sub(r"[#?!*]", "", word)

    # Remove subscript digits
    word = word.translate(_SUBSCRIPT_MAP)

    # Remove sign variants (~a, @g, etc.)
    word = re.sub(r"[~@][a-z0-9]+", "", word)

    # Remove pipe notation for complex signs
    word = word.replace("|", "").replace("×", "")

    # Lowercase
    word = word.lower()

    return word if word else None


def build_raw_atf(lines: list[dict]) -> str:
    """Reconstruct raw ATF text from flat DB lines, grouped by surface and column."""
    # Group by (surface, column), preserving order
    surface_columns: OrderedDict[str, OrderedDict[int, list[dict]]] = OrderedDict()
    for line in lines:
        st = line.get("surface_type") or "obverse"
        col = line.get("column_number", 0)
        if st not in surface_columns:
            surface_columns[st] = OrderedDict()
        if col not in surface_columns[st]:
            surface_columns[st][col] = []
        surface_columns[st][col].append(line)

    parts = []
    for surface_type, col_groups in surface_columns.items():
        parts.append(f"@{surface_type}")
        for col_num, col_lines in col_groups.items():
            if col_num > 0:
                parts.append(f"@column {col_num}")
            for db_line in col_lines:
                raw = db_line.get("raw_atf") or ""
                line_num = db_line.get("line_number") or ""
                if raw.startswith("$"):
                    parts.append(raw)
                elif db_line.get("is_blank"):
                    parts.append(raw if raw else "$ blank")
                elif db_line.get("is_ruling"):
                    parts.append("$ ruling")
                else:
                    parts.append(f"{line_num} {raw}")
    return "\n".join(parts)


def get_legend_items(surfaces: list[dict]) -> list[dict]:
    """Scan parsed surfaces for features present → return legend entries."""
    legend = [
        {"class": "has-definition", "label": "Has definition", "symbol": ""},
        {"class": "no-definition", "label": "No definition", "symbol": ""},
    ]

    flags = {
        "damage": False,
        "uncertain": False,
        "broken": False,
        "logogram": False,
        "divine": False,
        "place": False,
        "inline_translation": False,
    }

    for surface in surfaces:
        for col in surface.get("columns", []):
            for line in col.get("lines", []):
                if line.get("type") != "content":
                    continue
                if line.get("translations"):
                    flags["inline_translation"] = True
                for word in line.get("words", []):
                    wtype = word.get("type")
                    if wtype == "broken":
                        flags["broken"] = True
                    elif wtype == "logogram":
                        flags["logogram"] = True
                    elif wtype == "determinative":
                        dt = word.get("detType")
                        if dt == "divine":
                            flags["divine"] = True
                        elif dt in ("place", "city", "land"):
                            flags["place"] = True
                    elif wtype == "word":
                        if word.get("damaged"):
                            flags["damage"] = True
                        if word.get("uncertain"):
                            flags["uncertain"] = True

    if flags["divine"]:
        legend.append(
            {"class": "det-divine", "label": "Divine name", "symbol": "\u1d48"}
        )
    if flags["place"]:
        legend.append(
            {"class": "det-place", "label": "Place name", "symbol": "\u1d4f\u2071"}
        )
    if flags["logogram"]:
        legend.append({"class": "logogram", "label": "Logogram", "symbol": "_text_"})
    if flags["damage"]:
        legend.append({"class": "damaged", "label": "Damaged", "symbol": "#"})
    if flags["uncertain"]:
        legend.append({"class": "uncertain", "label": "Uncertain", "symbol": "?"})
    if flags["broken"]:
        legend.append({"class": "broken", "label": "Broken", "symbol": "[...]"})
    if flags["inline_translation"]:
        legend.append(
            {"class": "translation", "label": "Line translation", "symbol": "\u2502"}
        )

    return legend
