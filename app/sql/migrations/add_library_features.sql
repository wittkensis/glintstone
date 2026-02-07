-- Migration: Add Library Browser Features
-- Date: 2026-02-07
-- Description: Create tables for cross-references, polysemy, semantic fields,
--              sign-word relationships, and CAD integration

-- =============================================================================
-- 1. GLOSSARY RELATIONSHIPS TABLE
-- =============================================================================
-- Purpose: Track cross-references between dictionary entries
-- Relationship types: synonym, antonym, translation, cognate, etymology_source,
--                     semantic_field, compound_contains, see_also

CREATE TABLE IF NOT EXISTS glossary_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entry_id TEXT NOT NULL,
    to_entry_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    notes TEXT,
    confidence TEXT DEFAULT 'verified',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_entry_id) REFERENCES glossary_entries(entry_id),
    FOREIGN KEY (to_entry_id) REFERENCES glossary_entries(entry_id),
    UNIQUE (from_entry_id, to_entry_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_rel_from ON glossary_relationships(from_entry_id);
CREATE INDEX IF NOT EXISTS idx_rel_to ON glossary_relationships(to_entry_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON glossary_relationships(relationship_type);

-- =============================================================================
-- 2. GLOSSARY SENSES TABLE
-- =============================================================================
-- Purpose: Handle polysemy (multiple meanings per word)

CREATE TABLE IF NOT EXISTS glossary_senses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    sense_number INTEGER NOT NULL,
    guide_word TEXT NOT NULL,
    definition TEXT,
    usage_context TEXT,
    semantic_category TEXT,
    frequency_percentage REAL,
    example_lemma_ids TEXT,
    FOREIGN KEY (entry_id) REFERENCES glossary_entries(entry_id),
    UNIQUE (entry_id, sense_number)
);

CREATE INDEX IF NOT EXISTS idx_sense_entry ON glossary_senses(entry_id);

-- =============================================================================
-- 3. SEMANTIC FIELDS TABLES
-- =============================================================================
-- Purpose: Organize words into conceptual domains

CREATE TABLE IF NOT EXISTS semantic_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parent_field_id INTEGER,
    FOREIGN KEY (parent_field_id) REFERENCES semantic_fields(id)
);

CREATE TABLE IF NOT EXISTS glossary_semantic_fields (
    entry_id TEXT NOT NULL,
    field_id INTEGER NOT NULL,
    PRIMARY KEY (entry_id, field_id),
    FOREIGN KEY (entry_id) REFERENCES glossary_entries(entry_id),
    FOREIGN KEY (field_id) REFERENCES semantic_fields(id)
);

CREATE INDEX IF NOT EXISTS idx_gsf_entry ON glossary_semantic_fields(entry_id);
CREATE INDEX IF NOT EXISTS idx_gsf_field ON glossary_semantic_fields(field_id);

-- =============================================================================
-- 4. SIGN WORD USAGE TABLE
-- =============================================================================
-- Purpose: Track which signs appear in which words with what values

CREATE TABLE IF NOT EXISTS sign_word_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sign_id TEXT NOT NULL,
    sign_value TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    value_type TEXT,  -- logographic, syllabic, determinative
    FOREIGN KEY (sign_id) REFERENCES signs(sign_id),
    FOREIGN KEY (entry_id) REFERENCES glossary_entries(entry_id),
    UNIQUE (sign_id, entry_id, sign_value)
);

CREATE INDEX IF NOT EXISTS idx_swu_sign ON sign_word_usage(sign_id);
CREATE INDEX IF NOT EXISTS idx_swu_entry ON sign_word_usage(entry_id);

-- =============================================================================
-- 5. CAD ENTRIES TABLES (Phase 1: Basic)
-- =============================================================================
-- Purpose: Chicago Assyrian Dictionary integration

CREATE TABLE IF NOT EXISTS cad_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    volume TEXT NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER,
    headword TEXT NOT NULL,
    headword_normalized TEXT,
    transliteration_variants TEXT,  -- JSON array
    cuneiform TEXT,
    etymology TEXT,
    semantic_notes TEXT,
    bibliography TEXT,  -- JSON array
    compounds TEXT,     -- JSON array
    related_forms TEXT, -- JSON array
    oracc_entry_id TEXT,
    pdf_url TEXT,
    extraction_quality REAL,
    human_verified INTEGER DEFAULT 0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    FOREIGN KEY (oracc_entry_id) REFERENCES glossary_entries(entry_id)
);

CREATE INDEX IF NOT EXISTS idx_cad_headword ON cad_entries(headword);
CREATE INDEX IF NOT EXISTS idx_cad_normalized ON cad_entries(headword_normalized);
CREATE INDEX IF NOT EXISTS idx_cad_volume ON cad_entries(volume);
CREATE INDEX IF NOT EXISTS idx_cad_oracc ON cad_entries(oracc_entry_id);

-- CAD meanings (polysemy support)
CREATE TABLE IF NOT EXISTS cad_meanings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cad_entry_id INTEGER NOT NULL,
    sense_number INTEGER NOT NULL,
    definition TEXT NOT NULL,
    usage_context TEXT,
    semantic_category TEXT,
    FOREIGN KEY (cad_entry_id) REFERENCES cad_entries(id),
    UNIQUE (cad_entry_id, sense_number)
);

CREATE INDEX IF NOT EXISTS idx_cad_meanings_entry ON cad_meanings(cad_entry_id);

-- CAD examples (attestations from dictionary)
CREATE TABLE IF NOT EXISTS cad_examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cad_meaning_id INTEGER NOT NULL,
    example_text TEXT NOT NULL,
    translation TEXT,
    citation TEXT,
    citation_expanded TEXT,
    p_number TEXT,
    FOREIGN KEY (cad_meaning_id) REFERENCES cad_meanings(id),
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number)
);

CREATE INDEX IF NOT EXISTS idx_cad_ex_meaning ON cad_examples(cad_meaning_id);
CREATE INDEX IF NOT EXISTS idx_cad_ex_tablet ON cad_examples(p_number);

-- =============================================================================
-- 6. ENHANCEMENTS TO EXISTING TABLES
-- =============================================================================

-- Add columns to glossary_entries
ALTER TABLE glossary_entries ADD COLUMN normalized_headword TEXT;
ALTER TABLE glossary_entries ADD COLUMN semantic_category TEXT;

CREATE INDEX IF NOT EXISTS idx_glossary_normalized ON glossary_entries(normalized_headword);

-- Add columns to signs
ALTER TABLE signs ADD COLUMN sign_type TEXT;  -- simple, compound, variant
ALTER TABLE signs ADD COLUMN most_common_value TEXT;

-- Add columns to sign_values
ALTER TABLE sign_values ADD COLUMN value_type TEXT;  -- logographic, syllabic, determinative
ALTER TABLE sign_values ADD COLUMN frequency INTEGER DEFAULT 0;

-- =============================================================================
-- 7. DATABASE VIEWS
-- =============================================================================

-- Enriched glossary with counts and basic stats
CREATE VIEW IF NOT EXISTS glossary_enriched AS
SELECT
    ge.*,
    COUNT(DISTINCT gf.form) as variant_count,
    COUNT(DISTINCT l.p_number) as tablet_count
FROM glossary_entries ge
LEFT JOIN glossary_forms gf ON ge.entry_id = gf.entry_id
LEFT JOIN lemmas l ON (ge.citation_form = l.cf AND ge.language = l.lang)
GROUP BY ge.entry_id;

-- Sign usage summary
CREATE VIEW IF NOT EXISTS sign_usage_summary AS
SELECT
    s.sign_id,
    s.utf8,
    COUNT(DISTINCT sv.value) as value_count,
    COUNT(DISTINCT swu.entry_id) as word_count,
    SUM(swu.usage_count) as total_occurrences
FROM signs s
LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
GROUP BY s.sign_id;

-- =============================================================================
-- 8. INITIAL SEMANTIC FIELDS DATA
-- =============================================================================

INSERT OR IGNORE INTO semantic_fields (id, name, description, parent_field_id) VALUES
    (1, 'Kinship & Family', 'Family relationships and kinship terms', NULL),
    (2, 'Royalty & Authority', 'Kings, rulers, government officials', NULL),
    (3, 'Divine & Religious', 'Gods, goddesses, temples, religious practices', NULL),
    (4, 'Material Culture', 'Objects, tools, buildings, artifacts', NULL),
    (5, 'Agriculture & Food', 'Farming, crops, food production, consumption', NULL),
    (6, 'Water & Liquids', 'Water, rivers, beverages', NULL),
    (7, 'Animals & Nature', 'Domestic and wild animals, natural phenomena', NULL),
    (8, 'Numbers & Mathematics', 'Counting, measurement, calculation', NULL),
    (9, 'Body Parts', 'Anatomical terms', NULL),
    (10, 'Actions & Verbs', 'Common actions and activities', NULL),
    (11, 'Abstract Concepts', 'Justice, wisdom, power, etc.', NULL),
    (12, 'Geographic Features', 'Mountains, cities, regions', NULL);

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Verify migration success
SELECT
    'glossary_relationships' as table_name,
    COUNT(*) as row_count
FROM glossary_relationships
UNION ALL
SELECT 'glossary_senses', COUNT(*) FROM glossary_senses
UNION ALL
SELECT 'semantic_fields', COUNT(*) FROM semantic_fields
UNION ALL
SELECT 'sign_word_usage', COUNT(*) FROM sign_word_usage
UNION ALL
SELECT 'cad_entries', COUNT(*) FROM cad_entries;
