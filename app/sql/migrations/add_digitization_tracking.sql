-- Migration: Add sign annotation tracking to pipeline_status
-- Distinguishes machine OCR (sign annotations) from human transcription (ATF)

-- Add column for sign annotation tracking
ALTER TABLE pipeline_status ADD COLUMN has_sign_annotations INTEGER DEFAULT 0;

-- Populate from existing sign_annotations data
UPDATE pipeline_status
SET has_sign_annotations = 1
WHERE p_number IN (SELECT DISTINCT p_number FROM sign_annotations);

-- Update quality score calculation to include sign annotations
-- Quality now considers: image, human ATF, machine OCR, lemmas, translation
UPDATE pipeline_status
SET quality_score = (
    COALESCE(has_image, 0) * 0.15 +
    COALESCE(has_atf, 0) * 0.25 +
    COALESCE(has_sign_annotations, 0) * 0.15 +
    COALESCE(has_lemmas, 0) * 0.20 +
    COALESCE(has_translation, 0) * 0.25
);

-- Create index for filtering
CREATE INDEX IF NOT EXISTS idx_pipeline_sign_annotations ON pipeline_status(has_sign_annotations);

-- View for digitization status overview
CREATE VIEW IF NOT EXISTS digitization_overview AS
SELECT
    COUNT(*) as total_tablets,
    SUM(CASE WHEN has_atf = 1 THEN 1 ELSE 0 END) as human_transcription,
    SUM(CASE WHEN has_sign_annotations = 1 THEN 1 ELSE 0 END) as machine_ocr,
    SUM(CASE WHEN has_atf = 1 AND has_sign_annotations = 1 THEN 1 ELSE 0 END) as both,
    SUM(CASE WHEN has_atf = 1 OR has_sign_annotations = 1 THEN 1 ELSE 0 END) as any_digitization
FROM pipeline_status;
