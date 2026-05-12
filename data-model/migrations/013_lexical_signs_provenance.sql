-- ============================================================================
-- Migration 013: Add Unicode metadata and provenance tracking to lexical_signs
-- ============================================================================
-- Adds columns for Unicode code points, official Unicode names, and a JSONB
-- column to track which source contributed each field value. Supports the
-- merge-with-provenance strategy for multi-source sign data.
--
-- Date: 2026-02-23
-- ============================================================================

ALTER TABLE lexical_signs ADD COLUMN IF NOT EXISTS unicode_codepoint TEXT;
ALTER TABLE lexical_signs ADD COLUMN IF NOT EXISTS unicode_name TEXT;
ALTER TABLE lexical_signs ADD COLUMN IF NOT EXISTS source_contributions JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_lexical_signs_codepoint ON lexical_signs(unicode_codepoint);

COMMENT ON COLUMN lexical_signs.unicode_codepoint IS 'Unicode code point (e.g., U+12000)';
COMMENT ON COLUMN lexical_signs.unicode_name IS 'Official Unicode character name (e.g., CUNEIFORM SIGN A)';
COMMENT ON COLUMN lexical_signs.source_contributions IS 'Tracks which source contributed each field: {"sign_number": "ebl-sign-list", "unicode_char": "epsd2-sl"}';
