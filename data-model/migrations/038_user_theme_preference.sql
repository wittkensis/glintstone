-- Migration 038: user theme preference
--
-- Adds a 'theme' column to users.
-- Valid values match the CSS data-theme slugs:
--   'default'          — existing dark warm-gold system (tokens.css as-is)
--   'lapis-clay'       — deep excavation, lapis + clay two-accent
--   'scholars-studio'  — light editorial, verdigris, ink on stone
--   'instrument-panel' — cool dark, amber phosphor signal

BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS theme TEXT NOT NULL DEFAULT 'default'
    CHECK (theme IN ('default', 'lapis-clay', 'scholars-studio', 'instrument-panel'));

GRANT UPDATE (theme) ON users TO glintstone;

COMMIT;
