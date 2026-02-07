-- Migration: Add reference image dimensions to sign_annotations
-- These store the dimensions of the image the annotations were computed against,
-- enabling accurate scaling when displayed on differently-sized CDLI images.

ALTER TABLE sign_annotations ADD COLUMN ref_image_width INTEGER;
ALTER TABLE sign_annotations ADD COLUMN ref_image_height INTEGER;

-- Create index for efficient lookup by p_number (already exists, but ensure it's there)
CREATE INDEX IF NOT EXISTS idx_sign_annotations_p_number ON sign_annotations(p_number);
