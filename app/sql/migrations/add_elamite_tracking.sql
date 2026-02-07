-- Migration: Add Elamite tracking and improve inscriptions deduplication
-- Date: 2025-02-05

-- Add source column to inscriptions for deduplication (if not exists)
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE
-- The import script handles this gracefully

-- Create unique index for inscriptions to prevent duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_inscriptions_p_source ON inscriptions(p_number, source);

-- Elamite tablets view for easy querying
DROP VIEW IF EXISTS elamite_tablets;
CREATE VIEW elamite_tablets AS
SELECT
    a.p_number,
    a.designation,
    a.museum_no,
    a.period,
    a.provenience,
    a.language,
    CASE WHEN LOWER(a.language) = 'elamite' THEN 1 ELSE 0 END as is_primary_elamite,
    CASE WHEN a.language LIKE '%;%' THEN 1 ELSE 0 END as is_multilingual,
    CASE WHEN i.atf IS NOT NULL AND i.atf != '' THEN 1 ELSE 0 END as has_transliteration,
    ps.has_image,
    ps.quality_score
FROM artifacts a
LEFT JOIN inscriptions i ON a.p_number = i.p_number
LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
WHERE LOWER(a.language) LIKE '%elamite%';

-- Index for language searches (if not exists)
CREATE INDEX IF NOT EXISTS idx_artifacts_language_lower ON artifacts(LOWER(language));
