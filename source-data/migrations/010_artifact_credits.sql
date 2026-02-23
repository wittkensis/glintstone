-- ============================================================================
-- Migration 010: ORACC Per-Text Credits
-- ============================================================================
-- Stores ORACC credits strings per artifact per project.
-- Credits contain structured prose: "Created by X. Lemmatized by Y."
-- An artifact can appear in multiple ORACC projects, each with its own credits.
--
-- Date: 2026-02-22
-- ============================================================================

CREATE TABLE IF NOT EXISTS artifact_credits (
    id SERIAL PRIMARY KEY,
    p_number TEXT NOT NULL REFERENCES artifacts(p_number),
    oracc_project TEXT NOT NULL,
    credits_text TEXT NOT NULL,
    UNIQUE(p_number, oracc_project)
);

CREATE INDEX IF NOT EXISTS idx_artifact_credits_p_number ON artifact_credits(p_number);
