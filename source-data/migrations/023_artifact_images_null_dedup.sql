-- Migration 023: Prevent duplicate rows when cdli_reader_id IS NULL
--
-- Migration 022 declared:
--     UNIQUE (p_number, image_type, cdli_reader_id)
--
-- but Postgres treats NULL as distinct from NULL in standard UNIQUE constraints,
-- so two rows for the same artifact + image_type with cdli_reader_id IS NULL
-- (which is the case for every image inserted by ops/scripts/upload_local_images.py,
-- where the CDLI reader ID isn't known until the HTML attribution backfill runs)
-- would NOT collide. Re-running the upload script could create duplicate rows.
--
-- Fix: a partial unique index covering exactly the NULL case.

CREATE UNIQUE INDEX IF NOT EXISTS artifact_images_unique_null_reader_idx
    ON artifact_images (p_number, image_type)
    WHERE cdli_reader_id IS NULL;

COMMENT ON INDEX artifact_images_unique_null_reader_idx IS
    'Closes the NULL-distinct gap in artifact_images_unique_source. Lets the '
    'attribution backfill (which fills in cdli_reader_id) re-run safely.';
