-- Glintstone Database Schema (SQLite)
-- Local POC version

-- Core artifact metadata from CDLI
CREATE TABLE IF NOT EXISTS artifacts (
    p_number TEXT PRIMARY KEY,
    designation TEXT,
    museum_no TEXT,
    excavation_no TEXT,
    findspot_square TEXT,
    material TEXT,
    object_type TEXT,
    period TEXT,
    provenience TEXT,
    genre TEXT,
    language TEXT,
    width REAL,
    height REAL,
    thickness REAL,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inscriptions and ATF text
CREATE TABLE IF NOT EXISTS inscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    p_number TEXT NOT NULL,
    atf TEXT,
    transliteration_clean TEXT,
    is_latest INTEGER DEFAULT 1,
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number)
);

-- Composite texts (Q-numbers)
CREATE TABLE IF NOT EXISTS composites (
    q_number TEXT PRIMARY KEY,
    designation TEXT,
    artifact_comments TEXT,
    created_by INTEGER
);

-- Artifact-Composite mapping
CREATE TABLE IF NOT EXISTS artifact_composites (
    p_number TEXT,
    q_number TEXT,
    line_ref TEXT,
    PRIMARY KEY (p_number, q_number),
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number),
    FOREIGN KEY (q_number) REFERENCES composites(q_number)
);

-- OGSL Sign inventory
CREATE TABLE IF NOT EXISTS signs (
    sign_id TEXT PRIMARY KEY,
    utf8 TEXT,
    unicode_hex TEXT,
    unicode_decimal INTEGER,
    uphase TEXT,
    uname TEXT
);

-- Sign readings/values
CREATE TABLE IF NOT EXISTS sign_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sign_id TEXT NOT NULL,
    value TEXT NOT NULL,
    sub_index INTEGER,
    FOREIGN KEY (sign_id) REFERENCES signs(sign_id)
);

-- Sign variants (modifiers like @g, @t)
CREATE TABLE IF NOT EXISTS sign_variants (
    variant_id TEXT PRIMARY KEY,
    base_sign TEXT,
    modifiers TEXT,
    FOREIGN KEY (base_sign) REFERENCES signs(sign_id)
);

-- Glossary entries (from ORACC)
CREATE TABLE IF NOT EXISTS glossary_entries (
    entry_id TEXT PRIMARY KEY,
    headword TEXT,
    citation_form TEXT,
    guide_word TEXT,
    language TEXT,
    pos TEXT,
    icount INTEGER,
    project TEXT
);

-- Glossary forms (variant spellings)
CREATE TABLE IF NOT EXISTS glossary_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    form TEXT NOT NULL,
    count INTEGER,
    FOREIGN KEY (entry_id) REFERENCES glossary_entries(entry_id)
);

-- Pipeline status tracking (per tablet)
CREATE TABLE IF NOT EXISTS pipeline_status (
    p_number TEXT PRIMARY KEY,
    has_image INTEGER DEFAULT 0,
    has_ocr INTEGER DEFAULT 0,
    ocr_confidence REAL,
    ocr_model TEXT,
    has_atf INTEGER DEFAULT 0,
    atf_source TEXT,
    has_lemmas INTEGER DEFAULT 0,
    lemma_coverage REAL,
    has_translation INTEGER DEFAULT 0,
    translation_consensus REAL,
    quality_score REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number)
);

-- External resource links
CREATE TABLE IF NOT EXISTS external_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    p_number TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    resource_key TEXT,
    base_url TEXT,
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_artifacts_designation ON artifacts(designation);
CREATE INDEX IF NOT EXISTS idx_artifacts_period ON artifacts(period);
CREATE INDEX IF NOT EXISTS idx_artifacts_language ON artifacts(language);
CREATE INDEX IF NOT EXISTS idx_artifacts_genre ON artifacts(genre);
CREATE INDEX IF NOT EXISTS idx_inscriptions_p_number ON inscriptions(p_number);
CREATE INDEX IF NOT EXISTS idx_signs_utf8 ON signs(utf8);
CREATE INDEX IF NOT EXISTS idx_sign_values_sign_id ON sign_values(sign_id);
CREATE INDEX IF NOT EXISTS idx_sign_values_value ON sign_values(value);
CREATE INDEX IF NOT EXISTS idx_glossary_headword ON glossary_entries(headword);
CREATE INDEX IF NOT EXISTS idx_glossary_language ON glossary_entries(language);
CREATE INDEX IF NOT EXISTS idx_pipeline_quality ON pipeline_status(quality_score);
