-- Migration 034: citation FK integrity audit + ON DELETE policy
--
-- Some annotation_runs rows reference publication_id or scholar_id values that
-- no longer exist (orphan FKs). This produces broken citation links in the
-- Research tab. Tightens nullable FKs with ON DELETE SET NULL so future deletes
-- can't strand references, adds missing indexes for efficient orphan lookup,
-- and repairs current orphans.
--
-- NOT NULL referencing columns (publication_authors.*, artifact_editions.*,
-- scholar_merge_log.*) are *not* touched — orphans there indicate a write-time
-- bug, not a delete-time race; they need targeted manual review. RAISE NOTICE
-- reports any so the operator can investigate.
--
-- See issue #20.

BEGIN;

-- ── Indexes for efficient orphan lookup ────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_annotation_runs_publication
  ON annotation_runs(publication_id);
CREATE INDEX IF NOT EXISTS idx_annotation_runs_scholar
  ON annotation_runs(scholar_id);
CREATE INDEX IF NOT EXISTS idx_publications_supersedes
  ON publications(supersedes_id);

-- ── Repair nullable orphans → SET NULL ─────────────────────────────────────
UPDATE annotation_runs ar
   SET publication_id = NULL
 WHERE ar.publication_id IS NOT NULL
   AND NOT EXISTS (
     SELECT 1 FROM publications p WHERE p.id = ar.publication_id
   );

UPDATE annotation_runs ar
   SET scholar_id = NULL
 WHERE ar.scholar_id IS NOT NULL
   AND NOT EXISTS (
     SELECT 1 FROM scholars s WHERE s.id = ar.scholar_id
   );

UPDATE publications p
   SET supersedes_id = NULL
 WHERE p.supersedes_id IS NOT NULL
   AND NOT EXISTS (
     SELECT 1 FROM publications p2 WHERE p2.id = p.supersedes_id
   );

-- ── Replace FK constraints with ON DELETE SET NULL on nullable FKs ─────────
ALTER TABLE annotation_runs
  DROP CONSTRAINT IF EXISTS annotation_runs_scholar_id_fkey;
ALTER TABLE annotation_runs
  ADD CONSTRAINT annotation_runs_scholar_id_fkey
  FOREIGN KEY (scholar_id) REFERENCES scholars(id) ON DELETE SET NULL;

ALTER TABLE annotation_runs
  DROP CONSTRAINT IF EXISTS fk_annotation_runs_publication;
ALTER TABLE annotation_runs
  ADD CONSTRAINT fk_annotation_runs_publication
  FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE SET NULL;

ALTER TABLE publications
  DROP CONSTRAINT IF EXISTS publications_supersedes_id_fkey;
ALTER TABLE publications
  ADD CONSTRAINT publications_supersedes_id_fkey
  FOREIGN KEY (supersedes_id) REFERENCES publications(id) ON DELETE SET NULL;

-- ── Report NOT NULL orphans (manual review) ────────────────────────────────
DO $$
DECLARE
  n_pa_pub  integer;
  n_pa_sch  integer;
  n_ae_pub  integer;
BEGIN
  SELECT COUNT(*) INTO n_pa_pub FROM publication_authors pa
    WHERE NOT EXISTS (SELECT 1 FROM publications p WHERE p.id = pa.publication_id);
  SELECT COUNT(*) INTO n_pa_sch FROM publication_authors pa
    WHERE NOT EXISTS (SELECT 1 FROM scholars s WHERE s.id = pa.scholar_id);
  SELECT COUNT(*) INTO n_ae_pub FROM artifact_editions ae
    WHERE NOT EXISTS (SELECT 1 FROM publications p WHERE p.id = ae.publication_id);
  IF n_pa_pub + n_pa_sch + n_ae_pub > 0 THEN
    RAISE NOTICE 'NOT NULL orphans (manual review): publication_authors.publication_id=%, publication_authors.scholar_id=%, artifact_editions.publication_id=%',
      n_pa_pub, n_pa_sch, n_ae_pub;
  END IF;
END $$;

COMMIT;
