-- Migration 033: expand surfaces.surface_type CHECK to cover all ATF artifact shapes
--
-- The ATF spec declares physical artifact surfaces via `@<surface-name>`:
-- obverse, reverse, edges (existing) PLUS envelope, prism, cylinder, cone, brick,
-- bulla, tablet, object. The parser currently maps the latter group to NULL,
-- which means every line under those markers loses its surface_id — sign
-- annotations on envelopes and prism faces orphan from their surface.
--
-- See issue #19. The ATF parser SURFACE_MAP is updated in the same change.

BEGIN;

ALTER TABLE surfaces
  DROP CONSTRAINT IF EXISTS surfaces_surface_type_check;

ALTER TABLE surfaces
  ADD CONSTRAINT surfaces_surface_type_check
  CHECK (surface_type = ANY (ARRAY[
    'obverse'::text,
    'reverse'::text,
    'left_edge'::text,
    'right_edge'::text,
    'top_edge'::text,
    'bottom_edge'::text,
    'seal'::text,
    'envelope'::text,
    'tablet'::text,
    'object'::text,
    'prism'::text,
    'cylinder'::text,
    'brick'::text,
    'cone'::text,
    'bulla'::text,
    'column'::text,
    'face'::text
  ]));

COMMIT;
