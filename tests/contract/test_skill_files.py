"""Sanity test: the gs-expert-agentic skill files exist and have YAML headers."""

from pathlib import Path

import pytest

_SKILL_DIR = (
    Path(__file__).resolve().parents[2] / ".claude" / "skills" / "gs-expert-agentic"
)

_REQUIRED_FILES = [
    "SKILL.md",
    "envelope.md",
    "citation-contract.md",
    "hero-tools.md",
    "learning-loop.md",
    "decisions.md",
    "prompts/synthesis.v1.md",
    "prompts/interpret-token.v1.md",
]


@pytest.mark.parametrize("relpath", _REQUIRED_FILES)
def test_skill_file_exists(relpath: str):
    path = _SKILL_DIR / relpath
    assert path.exists(), f"missing skill file: {relpath}"


@pytest.mark.parametrize("relpath", _REQUIRED_FILES)
def test_skill_file_has_yaml_header(relpath: str):
    path = _SKILL_DIR / relpath
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{relpath} missing YAML frontmatter"
    end = text.find("\n---", 4)
    assert end > 0, f"{relpath} frontmatter is not closed"
    header = text[4:end]
    # Required fields
    assert "question:" in header
    assert "created:" in header
    assert "modified:" in header
