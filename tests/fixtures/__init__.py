"""Curated record fixtures for tests and demos.

Source of truth: `.claude/skills/gs-curator-artifacts/catalog.yaml`.

When you add a new record there, also add a named constant to `fixtures.py`
so tests can reference the same record without re-running discovery queries.

`gs-curator-docs` flags drift between catalog.yaml and fixtures.py on push.
"""

from .fixtures import *  # noqa: F401, F403
