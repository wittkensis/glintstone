-- Migration 035: audit CompVis sign_annotations for orphan linkages
--
-- CompVis bounding-box annotations link to a SurfaceImage -> Surface -> Artifact.
-- The FK chain *enforces* surface_image_id today, but two layers can still
-- silently break the Tablet Viewer overlay:
--   1. surface_images whose surface_id is NULL or points to a missing surface
--   2. sign_annotations whose line_number doesn't match a real line on the
--      annotated surface (no FK — relationship is positional)
--
-- This migration:
--   - Repairs surface_images.surface_id orphans (SET NULL — they can't point
--     to a surface that doesn't exist).
--   - Reports counts of positional-mismatch sign_annotations so the Tablet
--     Viewer team can decide whether to delete or quarantine. We don't delete
--     here because annotation_run_id (attribution) survives even when a
--     position is off, and CLAUDE.md says we never silently overwrite.
--
-- See issue #18.

BEGIN;

-- ── Repair surface_images with stranded surface_id ─────────────────────────
UPDATE surface_images si
   SET surface_id = NULL
 WHERE si.surface_id IS NOT NULL
   AND NOT EXISTS (
     SELECT 1 FROM surfaces s WHERE s.id = si.surface_id
   );

-- ── Index for the positional join below + future viewer queries ────────────
CREATE INDEX IF NOT EXISTS idx_sign_annotations_run
  ON sign_annotations(annotation_run_id);
CREATE INDEX IF NOT EXISTS idx_sign_annotations_surface_image
  ON sign_annotations(surface_image_id);

-- ── Report positional orphans ──────────────────────────────────────────────
DO $$
DECLARE
  n_no_image       integer;
  n_image_no_surf  integer;
  n_line_mismatch  integer;
BEGIN
  SELECT COUNT(*) INTO n_no_image
    FROM sign_annotations
    WHERE surface_image_id IS NULL;

  SELECT COUNT(*) INTO n_image_no_surf
    FROM sign_annotations sa
    JOIN surface_images si ON si.id = sa.surface_image_id
    WHERE si.surface_id IS NULL;

  -- Lines exist for the surface? Positional join — no FK enforces this.
  -- text_lines.line_number is TEXT (ATF labels like "1", "1'", "1.a"); compare
  -- the integer prefix.
  SELECT COUNT(*) INTO n_line_mismatch
    FROM sign_annotations sa
    JOIN surface_images si ON si.id = sa.surface_image_id
    JOIN surfaces s        ON s.id = si.surface_id
    WHERE sa.line_number IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM text_lines tl
        WHERE tl.surface_id = s.id
          AND substring(tl.line_number from '^\d+')::int = sa.line_number
      );

  IF n_no_image + n_image_no_surf + n_line_mismatch > 0 THEN
    RAISE NOTICE 'CompVis sign_annotations orphans — surface_image=%, image_no_surface=%, line_mismatch=%',
      n_no_image, n_image_no_surf, n_line_mismatch;
  END IF;
END $$;

COMMIT;
