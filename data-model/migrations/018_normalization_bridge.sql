-- Migration 018: Normalization Bridge
-- Enables: written_form → normalized_form → lemma → glosses
-- Primary use: Akkadian syllabic readings (e.g., ra-man-šú-nu → ramānšunu → ramānu "self")
-- Source data: ORACC glossary norms[] arrays (~110k norms, ~150k norm-forms)

BEGIN;

-- Normalized forms, each linked to a parent lemma (citation form)
-- One lemma has many norms (morphological variants: šarru, šarri, šarram, etc.)
CREATE TABLE IF NOT EXISTS lexical_norms (
    id SERIAL PRIMARY KEY,
    norm TEXT NOT NULL,
    lemma_id INTEGER NOT NULL REFERENCES lexical_lemmas(id) ON DELETE CASCADE,
    attestation_count INTEGER DEFAULT 0,
    attestation_pct SMALLINT DEFAULT 0,
    source TEXT NOT NULL,
    source_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(norm, lemma_id, source)
);

CREATE INDEX IF NOT EXISTS idx_lexical_norms_norm ON lexical_norms(norm);
CREATE INDEX IF NOT EXISTS idx_lexical_norms_lemma ON lexical_norms(lemma_id);
CREATE INDEX IF NOT EXISTS idx_lexical_norms_source ON lexical_norms(source);
CREATE INDEX IF NOT EXISTS idx_lexical_norms_freq ON lexical_norms(attestation_count DESC);

-- Written/orthographic spellings per norm
-- One norm has many written forms (spelling variants: a-ba-ku, ab-ba-ku, etc.)
CREATE TABLE IF NOT EXISTS lexical_norm_forms (
    id SERIAL PRIMARY KEY,
    norm_id INTEGER NOT NULL REFERENCES lexical_norms(id) ON DELETE CASCADE,
    written_form TEXT NOT NULL,
    attestation_count INTEGER DEFAULT 0,
    source TEXT NOT NULL,
    UNIQUE(norm_id, written_form, source)
);

CREATE INDEX IF NOT EXISTS idx_lexical_norm_forms_written ON lexical_norm_forms(written_form);
CREATE INDEX IF NOT EXISTS idx_lexical_norm_forms_norm ON lexical_norm_forms(norm_id);

-- Optional FK from lemmatizations to lexical_norms (nullable, non-breaking)
-- Backfilled after import; existing step 11 continues writing norm as TEXT
ALTER TABLE lemmatizations ADD COLUMN IF NOT EXISTS norm_id INTEGER
    REFERENCES lexical_norms(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_lemmatizations_norm_id ON lemmatizations(norm_id);

-- Permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON lexical_norms TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE lexical_norms_id_seq TO glintstone;
GRANT SELECT, INSERT, UPDATE, DELETE ON lexical_norm_forms TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE lexical_norm_forms_id_seq TO glintstone;

COMMIT;
