-- Migration 024: Add unique constraints required by v2 ingestion connectors
--
-- Each of these tables was created by the v1 import pipeline without a unique
-- constraint on the natural key. The v2 connectors call upsert_batch() which
-- generates ON CONFLICT (<col>) DO NOTHING — Postgres requires a matching unique
-- or exclusion constraint. This migration safe-deduplicates existing data first,
-- then adds the constraints.
--
-- Also tightens lexical_norm_forms: drops the 3-column (norm_id, written_form, source)
-- constraint and replaces it with 2-column (norm_id, written_form), eliminating
-- duplicate written-form rows that differed only by source.

BEGIN;

-- ── 1. lexical_norm_forms: drop 3-column constraint, add 2-column ──────────
-- Keep the row with the highest attestation_count per (norm_id, written_form).
-- Ties broken by lowest id (earliest imported).
ALTER TABLE lexical_norm_forms
  DROP CONSTRAINT lexical_norm_forms_norm_id_written_form_source_key;

DELETE FROM lexical_norm_forms lnf1
USING lexical_norm_forms lnf2
WHERE lnf1.norm_id     = lnf2.norm_id
  AND lnf1.written_form = lnf2.written_form
  AND (lnf1.attestation_count < lnf2.attestation_count
       OR (lnf1.attestation_count = lnf2.attestation_count AND lnf1.id > lnf2.id));

ALTER TABLE lexical_norm_forms
  ADD CONSTRAINT lexical_norm_forms_norm_id_written_form_key UNIQUE (norm_id, written_form);

GRANT SELECT, INSERT, UPDATE, DELETE ON lexical_norm_forms TO glintstone;

-- ── 2. annotation_runs: unique(source_name) ───────────────────────────────
-- Each canonical annotation source should appear exactly once.
-- Keep the earliest (lowest id) record per source_name.
DELETE FROM annotation_runs ar1
USING annotation_runs ar2
WHERE ar1.source_name = ar2.source_name
  AND ar1.id > ar2.id;

ALTER TABLE annotation_runs
  ADD CONSTRAINT annotation_runs_source_name_key UNIQUE (source_name);

GRANT SELECT, INSERT, UPDATE, DELETE ON annotation_runs TO glintstone;

-- ── 3. scholars: unique(name) ─────────────────────────────────────────────
-- Scholars connector normalizes names to NFC and deduplicates via Python set,
-- so duplicates are unlikely — but safe-dedup before adding the constraint.
-- For any duplicate, remap FKs to the canonical (lowest-id) scholar, then delete.
DO $$
DECLARE
    kept_name  text;
    keep_id    integer;
    dup_id     integer;
BEGIN
    FOR kept_name, keep_id IN
        SELECT name, MIN(id) AS keep_id
        FROM scholars
        GROUP BY name
        HAVING COUNT(*) > 1
    LOOP
        FOR dup_id IN
            SELECT id FROM scholars
            WHERE name = kept_name AND id <> keep_id
        LOOP
            -- Remap references that carry attribution (point to canonical scholar)
            UPDATE annotation_runs      SET scholar_id  = keep_id WHERE scholar_id  = dup_id;
            UPDATE publication_authors  SET scholar_id  = keep_id WHERE scholar_id  = dup_id;
            UPDATE scholar_merge_log    SET kept_scholar_id = keep_id WHERE kept_scholar_id = dup_id;

            -- NULL out optional decision/evidence attribution columns
            UPDATE artifact_edition_decisions      SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE artifact_edition_evidence       SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE artifact_identifier_decisions   SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE artifact_identifier_evidence    SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE authority_reconciliation_disputes SET scholar_id = NULL WHERE scholar_id = dup_id;
            UPDATE discussion_posts                SET scholar_id = NULL WHERE scholar_id = dup_id;
            UPDATE entity_aliases                  SET merged_by  = NULL WHERE merged_by  = dup_id;
            UPDATE entity_mention_decisions        SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE entity_mention_evidence         SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE entity_relationship_decisions   SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE entity_relationship_evidence    SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE fragment_join_decisions         SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE fragment_join_evidence          SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE lemmatization_decisions         SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE lemmatization_evidence          SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE scholarly_annotation_evidence   SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE sign_annotation_evidence        SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE token_reading_decisions         SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE token_reading_evidence          SET added_by   = NULL WHERE added_by   = dup_id;
            UPDATE translation_decisions           SET decided_by = NULL WHERE decided_by = dup_id;
            UPDATE translation_evidence            SET added_by   = NULL WHERE added_by   = dup_id;

            DELETE FROM scholars WHERE id = dup_id;
        END LOOP;
    END LOOP;
END $$;

ALTER TABLE scholars
  ADD CONSTRAINT scholars_name_key UNIQUE (name);

GRANT SELECT, INSERT, UPDATE, DELETE ON scholars TO glintstone;

-- ── 4. sign_values: unique(sign_id, value) ─────────────────────────────────
-- Keep the lowest id per (sign_id, value) pair.
DELETE FROM sign_values sv1
USING sign_values sv2
WHERE sv1.sign_id = sv2.sign_id
  AND sv1.value   = sv2.value
  AND sv1.id      > sv2.id;

ALTER TABLE sign_values
  ADD CONSTRAINT sign_values_sign_id_value_key UNIQUE (sign_id, value);

GRANT SELECT, INSERT, UPDATE, DELETE ON sign_values TO glintstone;

-- ── 5. glossary_forms: unique(entry_id, form) ──────────────────────────────
-- Keep the lowest id per (entry_id, form) pair.
DELETE FROM glossary_forms gf1
USING glossary_forms gf2
WHERE gf1.entry_id = gf2.entry_id
  AND gf1.form     = gf2.form
  AND gf1.id       > gf2.id;

ALTER TABLE glossary_forms
  ADD CONSTRAINT glossary_forms_entry_id_form_key UNIQUE (entry_id, form);

GRANT SELECT, INSERT, UPDATE, DELETE ON glossary_forms TO glintstone;

-- ── 6. token_readings: unique(token_id) ────────────────────────────────────
-- Phase-A heuristic connector writes exactly one reading per token (is_consensus=1).
-- Competing scholarly interpretations (the Glintstone feature) will use separate
-- annotation_run_ids; this constraint only affects the heuristic read.
-- Keep the reading with highest confidence; break ties by lowest id.
DELETE FROM token_readings tr1
USING token_readings tr2
WHERE tr1.token_id   = tr2.token_id
  AND (tr1.confidence < tr2.confidence
       OR (tr1.confidence = tr2.confidence AND tr1.id > tr2.id));

ALTER TABLE token_readings
  ADD CONSTRAINT token_readings_token_id_key UNIQUE (token_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON token_readings TO glintstone;

COMMIT;
