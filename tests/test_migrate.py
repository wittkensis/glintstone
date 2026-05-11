"""Tests for data-model/migrate.py — discovery, checksum, idempotent application."""

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-model"))


def _migrate_module():
    if "migrate" in sys.modules:
        del sys.modules["migrate"]
    return importlib.import_module("migrate")


def test_discover_returns_sorted_migrations():
    m = _migrate_module()
    migrations = m.discover()
    assert len(migrations) > 0
    versions = [v for v, _, _ in migrations]
    assert versions == sorted(versions)


def test_discover_skips_non_migration_files(tmp_path, monkeypatch):
    m = _migrate_module()
    fake_dir = tmp_path / "migrations"
    fake_dir.mkdir()
    (fake_dir / "001_first.sql").write_text("SELECT 1;")
    (fake_dir / "002a_letter.sql").write_text("SELECT 1;")
    (fake_dir / "README.md").write_text("readme")
    (fake_dir / "broken_no_number.sql").write_text("SELECT 1;")
    monkeypatch.setattr(m, "MIGRATIONS_DIR", fake_dir)
    versions = [v for v, _, _ in m.discover()]
    assert versions == ["001", "002a"]


def test_file_checksum_stable_across_calls(tmp_path):
    m = _migrate_module()
    f = tmp_path / "test.sql"
    f.write_text("SELECT 42;")
    h1 = m.file_checksum(f)
    h2 = m.file_checksum(f)
    assert h1 == h2
    assert len(h1) == 16


def test_file_checksum_changes_with_content(tmp_path):
    m = _migrate_module()
    f = tmp_path / "test.sql"
    f.write_text("SELECT 42;")
    h1 = m.file_checksum(f)
    f.write_text("SELECT 43;")
    h2 = m.file_checksum(f)
    assert h1 != h2


def test_baseline_already_applied_on_neon(has_database_url):
    m = _migrate_module()
    import psycopg

    with psycopg.connect(m.conninfo(), row_factory=psycopg.rows.dict_row) as conn:
        m.ensure_tracking(conn)
        applied = m.applied_versions(conn)
        assert "000" in applied, "Baseline migration should be applied on Neon"


def test_migration_pattern_matches_expected_formats():
    m = _migrate_module()
    assert m.MIGRATION_PATTERN.match("000_baseline.sql")
    assert m.MIGRATION_PATTERN.match("008a_alter.sql")
    assert m.MIGRATION_PATTERN.match("019_ingestion_v2.sql")
    assert not m.MIGRATION_PATTERN.match("baseline.sql")
    assert not m.MIGRATION_PATTERN.match("8_short.sql")
