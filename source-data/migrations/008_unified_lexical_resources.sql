-- ============================================================================
-- Migration 008: Unified Lexical Resource Architecture
-- ============================================================================
-- Purpose: Create three-dimensional lexical model organized by linguistic
--          dimensions (Glyphs, Lemmas, Meanings) rather than arbitrary sources
--
-- Strategic Vision: Coherent lexical platform for exploring cuneiform data
--                   across multiple dimensions with proper source attribution
--
-- Key Features:
--   - Source attribution as structural requirement (academic credit)
--   - Bidirectional navigation (Sign↔Lemmas↔Senses)
--   - Modular definitions (TEXT[] for separate editing)
--   - Dialect/period/region tracking
--   - Pre-computed tablet associations (performance)
--   - Multi-source support (ePSD2, ORACC projects)
--
-- Date: 2026-02-21
-- ============================================================================

-- ============================================================================
-- DIMENSION 1: GLYPHS (Graphemic)
-- ============================================================================
-- Signs represent the graphemic dimension - cuneiform characters and their
-- various readings/values across languages, dialects, and time periods.
-- ============================================================================

CREATE TABLE IF NOT EXISTS lexical_signs (
    id SERIAL PRIMARY KEY,

    -- Core sign data
    sign_name TEXT NOT NULL,                -- 'LUGAL', 'LU', 'GU4'
    unicode_char TEXT,                       -- '𒈗', '𒇽', '𒃲'
    sign_number TEXT,                        -- Borger/Labat reference number

    -- Sign classification
    shape_category TEXT,                     -- 'simple', 'composite', 'variant'
    component_signs TEXT[],                  -- For composites: ['LU', 'GAL']

    -- Sign values (readings)
    logographic_values TEXT[],               -- ['lugal', 'šarru']
    syllabic_values TEXT[],                  -- ['lu', 'lug']
    determinative_function TEXT,             -- Semantic classifier function

    -- Language/Dialect/Period tracking
    language_codes TEXT[],                   -- ['sux', 'akk', 'elx', 'hit']
    dialects TEXT[],                         -- ['emesal', 'emegir'] or NULL
    periods TEXT[],                          -- ['ur3', 'oldakkadian', 'middlebabylonian']
    regions TEXT[],                          -- ['lagash', 'ur', 'nippur']

    -- SOURCE ATTRIBUTION (structural requirement for academic credit)
    source TEXT NOT NULL,                    -- 'epsd2-sl', 'oracc-sl', 'borger2010'
    source_citation TEXT,                    -- Full bibliographic citation
    source_url TEXT,                         -- Link to original source

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_lexical_signs_name ON lexical_signs(sign_name);
CREATE INDEX idx_lexical_signs_unicode ON lexical_signs(unicode_char);
CREATE INDEX idx_lexical_signs_values_log ON lexical_signs USING GIN(logographic_values);
CREATE INDEX idx_lexical_signs_values_syll ON lexical_signs USING GIN(syllabic_values);
CREATE INDEX idx_lexical_signs_language ON lexical_signs USING GIN(language_codes);
CREATE INDEX idx_lexical_signs_period ON lexical_signs USING GIN(periods);
CREATE INDEX idx_lexical_signs_source ON lexical_signs(source);

COMMENT ON TABLE lexical_signs IS 'Cuneiform signs with readings, values, and graphemic metadata';
COMMENT ON COLUMN lexical_signs.logographic_values IS 'Word/concept values (e.g., LUGAL → lugal, šarru)';
COMMENT ON COLUMN lexical_signs.syllabic_values IS 'Phonetic syllable values (e.g., DU → du, gin)';
COMMENT ON COLUMN lexical_signs.source IS 'Attribution to original source (epsd2-sl, oracc-sl, etc.)';

-- ============================================================================
-- DIMENSION 2: LEMMAS (Lexemic)
-- ============================================================================
-- Lemmas represent the lexemic dimension - citation forms across languages
-- with morphological metadata, attestation tracking, and cross-references.
-- ============================================================================

CREATE TABLE IF NOT EXISTS lexical_lemmas (
    id SERIAL PRIMARY KEY,

    -- Core lemma data
    citation_form TEXT NOT NULL,             -- 'lugal', 'šarru', 'du'
    guide_word TEXT,                         -- 'king', 'go', 'ox'
    pos TEXT,                                -- 'N', 'V', 'AJ', 'AV', 'DP'
    language_code TEXT NOT NULL,             -- 'sux', 'akk', 'elx', 'hit'

    -- Morphological metadata
    base_form TEXT,                          -- For irregular forms
    verbal_class TEXT,                       -- For verbs (hamtu/marû)
    nominal_pattern TEXT,                    -- For nouns (qatal, qutil, etc.)

    -- Dialect/Period/Region context
    dialect TEXT,                            -- 'emesal', 'standard-babylonian'
    period TEXT,                             -- 'ur3', 'oldakkadian', 'neo-babylonian'
    region TEXT,                             -- 'lagash', 'ur', 'nippur'

    -- Cross-references
    cognates JSONB,                          -- {akk: 'šarru', hit: 'šarra-'}
    derived_from TEXT,                       -- Etymology reference

    -- Usage frequency (pre-computed from token_readings)
    attestation_count INTEGER DEFAULT 0,     -- Total occurrences in corpus
    tablet_count INTEGER DEFAULT 0,          -- Number of distinct tablets

    -- SOURCE ATTRIBUTION (structural requirement)
    source TEXT NOT NULL,                    -- 'epsd2', 'oracc/dcclt', 'oracc/saao'
    source_citation TEXT,                    -- Full bibliographic citation
    source_url TEXT,                         -- Link to original source

    -- Composite key for deduplication across sources
    cf_gw_pos TEXT GENERATED ALWAYS AS (
        citation_form || '[' || COALESCE(guide_word, '') || ']' || COALESCE(pos, '')
    ) STORED,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_lexical_lemmas_cf ON lexical_lemmas(citation_form);
CREATE INDEX idx_lexical_lemmas_gw ON lexical_lemmas(guide_word);
CREATE INDEX idx_lexical_lemmas_lang ON lexical_lemmas(language_code);
CREATE INDEX idx_lexical_lemmas_pos ON lexical_lemmas(pos);
CREATE INDEX idx_lexical_lemmas_dialect ON lexical_lemmas(dialect);
CREATE INDEX idx_lexical_lemmas_period ON lexical_lemmas(period);
CREATE INDEX idx_lexical_lemmas_source ON lexical_lemmas(source);
CREATE INDEX idx_lexical_lemmas_attestation ON lexical_lemmas(attestation_count DESC);

-- Composite unique constraint: allow same cf[gw]pos from different sources
CREATE UNIQUE INDEX idx_lexical_lemmas_composite ON lexical_lemmas(cf_gw_pos, source);

COMMENT ON TABLE lexical_lemmas IS 'Citation forms across languages with morphological and contextual metadata';
COMMENT ON COLUMN lexical_lemmas.cf_gw_pos IS 'Composite key: citation_form[guide_word]POS for deduplication';
COMMENT ON COLUMN lexical_lemmas.attestation_count IS 'Pre-computed from token_readings (updated nightly)';
COMMENT ON COLUMN lexical_lemmas.source IS 'Attribution to dictionary/glossary source';

-- ============================================================================
-- DIMENSION 3: MEANINGS (Semantic)
-- ============================================================================
-- Senses represent the semantic dimension - meaning distinctions (polysemy),
-- contextual usage, and translation equivalents. Linked to parent lemmas.
-- ============================================================================

CREATE TABLE IF NOT EXISTS lexical_senses (
    id SERIAL PRIMARY KEY,

    -- Parent lemma (CASCADE delete - senses belong to lemmas)
    lemma_id INTEGER NOT NULL REFERENCES lexical_lemmas(id) ON DELETE CASCADE,

    -- Polysemy tracking
    sense_number INTEGER DEFAULT 1,          -- 1, 2, 3 for multiple meanings

    -- MODULAR DEFINITIONS (array for separate editing)
    definition_parts TEXT[],                 -- ['king', 'ruler', 'master']
    usage_notes TEXT,                        -- 'Used in royal titles'
    semantic_domain TEXT,                    -- 'governance', 'agriculture', 'religion'

    -- Contextual information
    typical_context TEXT,                    -- 'administrative texts', 'literary'
    example_passages TEXT[],                 -- P-numbers with context

    -- Cross-language equivalents (modular, easily updated)
    translations JSONB,                      -- {en: ['king', 'ruler'], de: ['König'], akk: ['šarru']}

    -- Context frequency (pre-computed)
    context_distribution JSONB,              -- {administrative: 45, royal: 30, literary: 25}

    -- SOURCE ATTRIBUTION (structural requirement)
    source TEXT NOT NULL,                    -- 'epsd2', 'oracc/dcclt'
    source_citation TEXT,                    -- Full bibliographic citation
    source_url TEXT,                         -- Link to original source

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_lexical_senses_lemma ON lexical_senses(lemma_id);
CREATE INDEX idx_lexical_senses_domain ON lexical_senses(semantic_domain);
CREATE INDEX idx_lexical_senses_source ON lexical_senses(source);

COMMENT ON TABLE lexical_senses IS 'Semantic meanings and contextual usage for lemmas';
COMMENT ON COLUMN lexical_senses.definition_parts IS 'Array of definition components for modular editing';
COMMENT ON COLUMN lexical_senses.sense_number IS 'Polysemy tracking: 1, 2, 3 for multiple meanings';
COMMENT ON COLUMN lexical_senses.translations IS 'Cross-language equivalents as JSONB: {en: [...], de: [...]}';

-- ============================================================================
-- ASSOCIATIONS: Signs ↔ Lemmas (Many-to-Many)
-- ============================================================================
-- Join table connecting signs to lemmas with reading type classification.
-- Enables bidirectional navigation: Sign→Lemmas and Lemma→Signs.
-- ============================================================================

CREATE TABLE IF NOT EXISTS lexical_sign_lemma_associations (
    id SERIAL PRIMARY KEY,

    -- Foreign keys (CASCADE delete - associations depend on both entities)
    sign_id INTEGER NOT NULL REFERENCES lexical_signs(id) ON DELETE CASCADE,
    lemma_id INTEGER NOT NULL REFERENCES lexical_lemmas(id) ON DELETE CASCADE,

    -- Reading type classification
    reading_type TEXT NOT NULL,              -- 'logographic', 'syllabic', 'determinative'

    -- Frequency & Context (pre-computed from token_readings)
    frequency INTEGER DEFAULT 0,             -- How common is this sign→lemma mapping
    context_distribution JSONB,              -- {administrative: 45, literary: 30}

    -- SOURCE ATTRIBUTION
    source TEXT NOT NULL,                    -- 'epsd2-sl', 'manual', 'computed'
    source_citation TEXT,                    -- Full citation
    source_url TEXT,                         -- Link to source

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: same sign→lemma with same reading type from same source
    UNIQUE(sign_id, lemma_id, reading_type, source)
);

-- Performance indexes
CREATE INDEX idx_lexical_sign_lemma_sign ON lexical_sign_lemma_associations(sign_id);
CREATE INDEX idx_lexical_sign_lemma_lemma ON lexical_sign_lemma_associations(lemma_id);
CREATE INDEX idx_lexical_sign_lemma_type ON lexical_sign_lemma_associations(reading_type);
CREATE INDEX idx_lexical_sign_lemma_freq ON lexical_sign_lemma_associations(frequency DESC);

COMMENT ON TABLE lexical_sign_lemma_associations IS 'M:N relationship connecting signs to lemmas with reading type';
COMMENT ON COLUMN lexical_sign_lemma_associations.reading_type IS 'Classification: logographic (word), syllabic (sound), determinative (classifier)';
COMMENT ON COLUMN lexical_sign_lemma_associations.frequency IS 'Pre-computed usage frequency (updated nightly)';

-- ============================================================================
-- TABLET OCCURRENCES: Pre-computed Associations
-- ============================================================================
-- Pre-computed table linking signs/lemmas/senses to tablets where they appear.
-- Strategic performance optimization - avoids expensive JOINs at request time.
-- Updated via background job (nightly or on-demand).
-- ============================================================================

CREATE TABLE IF NOT EXISTS lexical_tablet_occurrences (
    id SERIAL PRIMARY KEY,

    -- What (at least one must be set)
    sign_id INTEGER REFERENCES lexical_signs(id) ON DELETE CASCADE,
    lemma_id INTEGER REFERENCES lexical_lemmas(id) ON DELETE CASCADE,
    sense_id INTEGER REFERENCES lexical_senses(id) ON DELETE CASCADE,

    -- Where (tablet)
    p_number TEXT NOT NULL REFERENCES artifacts(p_number),

    -- How many times
    occurrence_count INTEGER DEFAULT 1,

    -- When computed
    computed_at TIMESTAMP DEFAULT NOW(),

    -- Constraint: at least one entity must be specified
    CHECK (sign_id IS NOT NULL OR lemma_id IS NOT NULL OR sense_id IS NOT NULL)
);

-- Performance indexes
CREATE INDEX idx_tablet_occ_sign ON lexical_tablet_occurrences(sign_id);
CREATE INDEX idx_tablet_occ_lemma ON lexical_tablet_occurrences(lemma_id);
CREATE INDEX idx_tablet_occ_sense ON lexical_tablet_occurrences(sense_id);
CREATE INDEX idx_tablet_occ_p_number ON lexical_tablet_occurrences(p_number);

COMMENT ON TABLE lexical_tablet_occurrences IS 'Pre-computed tablet associations for performance (updated nightly)';
COMMENT ON COLUMN lexical_tablet_occurrences.computed_at IS 'Timestamp of last computation';

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Next Steps:
--   1. Run this migration: psql -U <user> -d glintstone_data -f 008_unified_lexical_resources.sql
--   2. Verify tables created: \dt (should show 5 new tables)
--   3. Verify indexes created: \di (should show multiple indexes per table)
--   4. Proceed to Phase 3: Import ePSD2 data
-- ============================================================================
