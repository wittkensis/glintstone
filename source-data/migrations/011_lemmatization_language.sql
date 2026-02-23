-- Migration 011: Add per-word language to lemmatizations
--
-- ORACC CDL data includes language codes per lemma (e.g., sux, akk, akk-x-oldbab).
-- The import script (11_import_lemmatizations.py) already extracts this but discards it.
-- This column captures per-word language to enable:
--   - Bilingual tablet display (Sumerian vs Akkadian word coloring)
--   - Akkadogram/sumerogram identification (foreign-language logograms)
--
-- Values: ISO-style codes from ORACC (sux, akk, akk-x-oldbab, akk-x-stdbab, hit, etc.)

ALTER TABLE lemmatizations ADD COLUMN IF NOT EXISTS language TEXT;

-- Index for efficient language-based queries on bilingual tablets
CREATE INDEX IF NOT EXISTS idx_lemmatizations_language ON lemmatizations(language);
