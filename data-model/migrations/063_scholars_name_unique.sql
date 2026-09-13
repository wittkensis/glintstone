-- Migration 063: scholars.name UNIQUE — back the connector's ON CONFLICT (name)
--
-- Issue #1644. Found while building the #1612 ORACC project-team connector,
-- which had to sidestep `upsert_batch` with an explicit NOT EXISTS gate.
--
-- ── THE BUG ────────────────────────────────────────────────────────────────
-- `ingestion/connectors/scholars.py` loads via:
--
--     upsert_batch(ctx.db, table="scholars", rows=rows,
--                  unique_key=["name"], policy=ConflictPolicy.SKIP)
--
-- which `ingestion/loader.py` renders as
-- `INSERT INTO scholars (name) VALUES (%s) ON CONFLICT (name) DO NOTHING`.
--
-- Postgres resolves an ON CONFLICT *inference* clause at PLAN time against the
-- table's unique indexes. `scholars` has unique indexes on `id` (pkey) and
-- `orcid` only — nothing on `name`. So this statement does NOT merely misbehave
-- on a collision; it raises on the FIRST execution, every time:
--
--     ERROR:  there is no unique or exclusion constraint matching the
--             ON CONFLICT specification
--
-- The scholars connector's load() is therefore dead code today. Nothing is
-- currently blocked only because no live run reaches it.
--
-- ── WHY THE CONSTRAINT IS MISSING (migration 024 drifted) ──────────────────
-- Migration 024 (`024_connector_unique_constraints.sql`) already intended to
-- add `scholars_name_key UNIQUE (name)`. It is recorded in `public._migrations`
-- as applied (2026-05-18) but FIVE of its six constraints are absent from the
-- database:
--
--     lexical_norm_forms_norm_id_written_form_key   MISSING (old 3-col
--                                                   ..._source_key still there)
--     scholars_name_key                             MISSING  <-- this migration
--     sign_values_sign_id_value_key                 MISSING
--     glossary_forms_entry_id_form_key              MISSING
--     token_readings_token_id_key                   MISSING
--     annotation_runs_source_name_key               present
--
-- i.e. 024 is a recorded-but-not-effective migration. This file fixes only the
-- `scholars` slice (the scope of #1644); the other four tables have the exact
-- same latent ON CONFLICT bug and are tracked separately. Re-running 024 as-is
-- would NOT work: its hardcoded FK-remap list predates artifact_contributors,
-- project_contributors, scholar_claims, scholar_overrides and
-- interaction_feedback, so it would now fail on a foreign-key violation. Hence
-- a fresh, catalog-guarded migration rather than a re-apply.
--
-- ── WHY `name` IS THE RIGHT DEDUP KEY ──────────────────────────────────────
-- `scholars` is a registry of author-name STRINGS harvested from free-text
-- CDLI/ORACC catalogue fields. It has no external identifier to key on: of
-- 86,511 rows, `institution` is 0% populated, `active_since` 0%, and `orcid`
-- 0.5% (421 rows). A composite key is therefore not implementable — and
-- specifically `(name, orcid)` would be WORSE than useless, because a unique
-- index treats NULLs as distinct, so 99.5% of rows would never conflict and
-- the connector could insert the same name without limit.
--
-- The connector itself already treats the name string as identity (it collects
-- into a Python `set[str]` before yielding). This migration only makes the
-- database enforce the invariant the ingest code already assumes.
--
-- CAVEAT, stated plainly (CLAUDE.md: "competing interpretations are a
-- feature"): two genuinely different people CAN share a name, and after this
-- migration the schema cannot represent that. That trade is accepted for now
-- because the data model has no disambiguator to represent it with either —
-- today two same-named scholars are already indistinguishable. When ORCID
-- coverage grows enough to tell them apart, splitting them needs a real
-- identity column (not a wider unique key), plus the existing
-- `scholar_claims` / `scholar_overrides` machinery. Until then, an enforced
-- one-row-per-name registry is more accurate than silent partial duplicates.
--
-- ── UNICODE: NFC FIRST, OR THE CONSTRAINT DOESN'T ACTUALLY HELP ────────────
-- A unique index compares bytes. The connector NFC-normalizes every name it
-- emits (`_normalize_name`), but 268 existing rows are stored in a
-- non-NFC (decomposed) form. Without normalizing first, the connector would
-- keep inserting a composed twin of each decomposed row forever and
-- ON CONFLICT would never fire — the bug would be "fixed" but not actually
-- fixed. NFC is a canonical, lossless equivalence ("Édouard" composed and
-- decomposed are the same string, not two spellings), so normalizing is safe.
-- Precedent: migration 032 did the same for the lexical columns.
--
-- On the dev database this collapses three name groups into exact duplicates
-- (Önder İpek, Rocío Da Riva, Šárka Velhartická) which step 2 then merges.
--
-- NOT handled here, deliberately: four further groups differ only by LETTER
-- CASE (Turkish dotted/dotless I and Greek capitalisation — e.g. "İbrahim
-- Üngör" vs "Ibrahim Üngör"). Case folding is a lossy identity judgement, not
-- a canonical equivalence, so this migration does not merge them. They remain
-- as separate rows and are logged as a follow-up data-quality finding.
--
-- ── SAFETY ─────────────────────────────────────────────────────────────────
--  * Idempotent: if a unique index on `name` already exists (e.g. prod really
--    did get 024), steps 1 and 2 are skipped and step 3 is a no-op.
--  * Every merge is written to `scholar_merge_log` — the table migration 017
--    created for exactly this and which already holds 18,017 merges. No
--    scholar row is ever deleted without an audit row naming it.
--  * Attribution is REMAPPED to the surviving scholar, never NULLed. (024
--    NULLed out the nullable `decided_by`/`added_by` columns, which destroys
--    who made a decision — wrong for an attribution system when the two rows
--    are the same person.)
--  * Catalog guard: step 0 aborts if any FK points at scholars(id) that the
--    remap block below does not handle, so this migration can never silently
--    orphan attribution as the schema grows.
--  * Blast-radius guard: step 2 aborts if it finds more than 50 duplicate name
--    groups. On dev there is exactly 1 (3 after NFC). A much larger number
--    would mean the "name is identity" assumption is wrong at scale, and that
--    is a human judgement call, not something a migration should mass-resolve.
--
-- Deliberately NOT using CREATE INDEX CONCURRENTLY: the migration runner wraps
-- each file in a transaction and CONCURRENTLY cannot run inside one.

BEGIN;

-- ── Step 0: guard — every FK into scholars(id) must be known to step 2 ─────
DO $$
DECLARE
    unhandled text;
BEGIN
    SELECT string_agg(ref, ', ' ORDER BY ref) INTO unhandled
    FROM (
        SELECT c.conrelid::regclass::text || '.' || a.attname AS ref
        FROM pg_constraint c
        JOIN pg_attribute a
          ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
        WHERE c.contype = 'f'
          AND c.confrelid = 'public.scholars'::regclass
    ) refs
    WHERE ref NOT IN (
        'annotation_runs.scholar_id',
        'artifact_contributors.scholar_id',
        'artifact_edition_decisions.decided_by',
        'artifact_edition_evidence.added_by',
        'artifact_identifier_decisions.decided_by',
        'artifact_identifier_evidence.added_by',
        'authority_reconciliation_disputes.scholar_id',
        'discussion_posts.scholar_id',
        'entity_aliases.merged_by',
        'entity_mention_decisions.decided_by',
        'entity_mention_evidence.added_by',
        'entity_relationship_decisions.decided_by',
        'entity_relationship_evidence.added_by',
        'fragment_join_decisions.decided_by',
        'fragment_join_evidence.added_by',
        'interaction_feedback.scholar_id',
        'lemmatization_decisions.decided_by',
        'lemmatization_evidence.added_by',
        'project_contributors.scholar_id',
        'publication_authors.scholar_id',
        'scholar_claims.scholar_id',
        'scholar_merge_log.kept_scholar_id',
        'scholar_overrides.scholar_id',
        'scholarly_annotation_evidence.added_by',
        'sign_annotation_evidence.added_by',
        'token_reading_decisions.decided_by',
        'token_reading_evidence.added_by',
        'translation_decisions.decided_by',
        'translation_evidence.added_by'
    );

    IF unhandled IS NOT NULL THEN
        RAISE EXCEPTION
            'migration 063: unhandled foreign key(s) into scholars(id): %. '
            'Add them to the remap block in step 2 before applying.', unhandled;
    END IF;
END $$;

-- ── Steps 1 + 2: NFC-normalize, then audited merge of exact-duplicate names ─
DO $$
DECLARE
    name_attnum smallint;
    dup_groups  bigint;
    grp         record;
    dup_id      integer;
    normalized  bigint;
    merged      bigint := 0;
BEGIN
    SELECT attnum INTO name_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.scholars'::regclass AND attname = 'name';

    IF EXISTS (
        SELECT 1 FROM pg_index
        WHERE indrelid = 'public.scholars'::regclass
          AND indisunique
          AND indnkeyatts = 1
          AND indkey[0] = name_attnum
    ) THEN
        RAISE NOTICE
            'migration 063: scholars already carries a unique index on name; '
            'skipping normalize + merge.';
        RETURN;
    END IF;

    -- Step 1: canonical Unicode form, so the byte-comparing unique index below
    -- actually matches what the connector emits.
    UPDATE scholars
       SET name = normalize(name, NFC)
     WHERE name <> normalize(name, NFC);
    GET DIAGNOSTICS normalized = ROW_COUNT;
    RAISE NOTICE 'migration 063: NFC-normalized % scholar name(s).', normalized;

    -- Step 2 blast-radius guard.
    SELECT count(*) INTO dup_groups
    FROM (SELECT name FROM scholars GROUP BY name HAVING count(*) > 1) d;

    IF dup_groups > 50 THEN
        RAISE EXCEPTION
            'migration 063: found % duplicate scholar-name groups (threshold 50). '
            'That many collisions means "name is identity" does not hold for this '
            'data and the duplicates need human review before a unique index is '
            'imposed. Aborting rather than mass-merging scholar records.',
            dup_groups;
    END IF;

    RAISE NOTICE 'migration 063: merging % duplicate name group(s).', dup_groups;

    FOR grp IN
        SELECT name AS dup_name, min(id) AS keep_id
        FROM scholars
        GROUP BY name
        HAVING count(*) > 1
    LOOP
        FOR dup_id IN
            SELECT id FROM scholars
            WHERE name = grp.dup_name AND id <> grp.keep_id
            ORDER BY id
        LOOP
            -- 2a. Junctions with a unique index that includes scholar_id: drop
            -- the duplicate's row where the survivor already has the identical
            -- link, otherwise the remap below would violate that index.
            -- Plain `=` (not IS NOT DISTINCT FROM) mirrors unique-index
            -- semantics, where NULLs never collide.
            DELETE FROM artifact_contributors d
             WHERE d.scholar_id = dup_id
               AND EXISTS (
                   SELECT 1 FROM artifact_contributors k
                    WHERE k.scholar_id    = grp.keep_id
                      AND k.p_number      = d.p_number
                      AND k.role          = d.role
                      AND k.oracc_project = d.oracc_project);

            DELETE FROM project_contributors d
             WHERE d.scholar_id = dup_id
               AND EXISTS (
                   SELECT 1 FROM project_contributors k
                    WHERE k.scholar_id    = grp.keep_id
                      AND k.oracc_project = d.oracc_project
                      AND k.role          = d.role);

            DELETE FROM publication_authors d
             WHERE d.scholar_id = dup_id
               AND EXISTS (
                   SELECT 1 FROM publication_authors k
                    WHERE k.scholar_id     = grp.keep_id
                      AND k.publication_id = d.publication_id
                      AND k.role           = d.role);

            -- scholar_claims carries two PARTIAL unique indexes:
            --   (scholar_id) WHERE status = 'approved'
            --   (user_id, scholar_id) WHERE status = 'pending'
            DELETE FROM scholar_claims d
             WHERE d.scholar_id = dup_id
               AND d.status = 'approved'
               AND EXISTS (
                   SELECT 1 FROM scholar_claims k
                    WHERE k.scholar_id = grp.keep_id AND k.status = 'approved');

            DELETE FROM scholar_claims d
             WHERE d.scholar_id = dup_id
               AND d.status = 'pending'
               AND EXISTS (
                   SELECT 1 FROM scholar_claims k
                    WHERE k.scholar_id = grp.keep_id
                      AND k.status     = 'pending'
                      AND k.user_id    = d.user_id);

            -- 2b. Remap every remaining reference onto the surviving scholar.
            -- Attribution is preserved, never NULLed: the two rows are the same
            -- person, so "who decided this" stays answerable.
            UPDATE annotation_runs                   SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE artifact_contributors             SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE artifact_edition_decisions        SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE artifact_edition_evidence         SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE artifact_identifier_decisions     SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE artifact_identifier_evidence      SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE authority_reconciliation_disputes SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE discussion_posts                  SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE entity_aliases                    SET merged_by  = grp.keep_id WHERE merged_by  = dup_id;
            UPDATE entity_mention_decisions          SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE entity_mention_evidence           SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE entity_relationship_decisions     SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE entity_relationship_evidence      SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE fragment_join_decisions           SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE fragment_join_evidence            SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE interaction_feedback              SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE lemmatization_decisions           SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE lemmatization_evidence            SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE project_contributors              SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE publication_authors               SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE scholar_claims                    SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE scholar_merge_log                 SET kept_scholar_id = grp.keep_id WHERE kept_scholar_id = dup_id;
            UPDATE scholar_overrides                 SET scholar_id = grp.keep_id WHERE scholar_id = dup_id;
            UPDATE scholarly_annotation_evidence     SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE sign_annotation_evidence          SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE token_reading_decisions           SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE token_reading_evidence            SET added_by   = grp.keep_id WHERE added_by   = dup_id;
            UPDATE translation_decisions             SET decided_by = grp.keep_id WHERE decided_by = dup_id;
            UPDATE translation_evidence              SET added_by   = grp.keep_id WHERE added_by   = dup_id;

            -- 2c. Audit, then drop the duplicate row.
            INSERT INTO scholar_merge_log
                (kept_scholar_id, merged_scholar_id, merged_name, merge_reason)
            VALUES
                (grp.keep_id, dup_id, grp.dup_name,
                 'migration 063 (#1644): exact duplicate name after NFC '
                 'normalization; merged to enable scholars_name_key UNIQUE(name)');

            DELETE FROM scholars WHERE id = dup_id;
            merged := merged + 1;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'migration 063: merged % duplicate scholar row(s).', merged;
END $$;

-- ── Step 3: the constraint the connector's ON CONFLICT (name) needs ────────
DO $$
DECLARE
    name_attnum smallint;
BEGIN
    SELECT attnum INTO name_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.scholars'::regclass AND attname = 'name';

    IF EXISTS (
        SELECT 1 FROM pg_index
        WHERE indrelid = 'public.scholars'::regclass
          AND indisunique
          AND indnkeyatts = 1
          AND indkey[0] = name_attnum
    ) THEN
        RAISE NOTICE 'migration 063: unique index on scholars(name) already present.';
    ELSE
        EXECUTE 'ALTER TABLE scholars '
                'ADD CONSTRAINT scholars_name_key UNIQUE (name)';
    END IF;
END $$;

COMMENT ON CONSTRAINT scholars_name_key ON scholars IS
    'One row per scholar name. Backs ON CONFLICT (name) in '
    'ingestion/connectors/scholars.py via upsert_batch(unique_key=["name"]). '
    'Names are stored NFC-normalized. Added by migration 063 (#1644) after '
    'migration 024 was recorded as applied without taking effect.';

-- IMPORTANT: app connects as glintstone; tables are owned by wittkensis.
GRANT SELECT, INSERT, UPDATE, DELETE ON scholars TO glintstone;
GRANT SELECT, INSERT, UPDATE, DELETE ON scholar_merge_log TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE scholar_merge_log_id_seq TO glintstone;

COMMIT;
