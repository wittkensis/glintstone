-- CAD (Chicago Assyrian Dictionary) Tables Migration
-- Run with: sqlite3 ../glintstone.db < add_cad_tables.sql

-- Core CAD entries
CREATE TABLE IF NOT EXISTS cad_entries (
    id INTEGER PRIMARY KEY,
    headword TEXT NOT NULL,
    headword_normalized TEXT,  -- lowercase, no diacritics for search
    part_of_speech TEXT,
    volume TEXT NOT NULL,      -- e.g., 'A1', 'B', 'K'
    page_start INTEGER,
    page_end INTEGER,
    raw_text TEXT,             -- original extracted text for verification
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Meanings/definitions (one entry can have multiple meanings)
CREATE TABLE IF NOT EXISTS cad_meanings (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES cad_entries(id) ON DELETE CASCADE,
    position TEXT,             -- e.g., 'a', 'b', '1\'', '2\''
    definition TEXT NOT NULL,
    semantic_domain TEXT,      -- e.g., 'legal', 'medical', 'astronomical'
    context TEXT               -- e.g., 'in glass texts', 'in med. texts'
);

-- Attestations/citations (each meaning can have multiple attestations)
CREATE TABLE IF NOT EXISTS cad_attestations (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES cad_entries(id) ON DELETE CASCADE,
    meaning_id INTEGER REFERENCES cad_meanings(id) ON DELETE CASCADE,
    text_reference TEXT,       -- e.g., 'CT 25 50:3', 'TCL 4 105:5'
    akkadian_text TEXT,        -- the Akkadian text quoted
    translation TEXT,          -- English translation if provided
    period TEXT                -- e.g., 'OB', 'SB', 'NA', 'NB'
);

-- Cross-references between entries
CREATE TABLE IF NOT EXISTS cad_cross_references (
    id INTEGER PRIMARY KEY,
    from_entry_id INTEGER NOT NULL REFERENCES cad_entries(id) ON DELETE CASCADE,
    to_headword TEXT NOT NULL, -- target headword (may not exist yet)
    to_entry_id INTEGER REFERENCES cad_entries(id) ON DELETE SET NULL,  -- resolved link
    reference_type TEXT        -- 'see', 'cf.', 'compare', 'variant'
);

-- Logograms (Sumerian equivalents)
CREATE TABLE IF NOT EXISTS cad_logograms (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES cad_entries(id) ON DELETE CASCADE,
    sumerian_form TEXT NOT NULL,  -- e.g., 'A.BÁR', 'ŠU.KAL'
    pronunciation TEXT,           -- reading/pronunciation gloss
    context TEXT                  -- usage context
);

-- Full-text search index
CREATE VIRTUAL TABLE IF NOT EXISTS cad_fts USING fts5(
    headword,
    definition,
    akkadian_text,
    translation,
    content='',  -- external content mode
    tokenize='unicode61'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cad_entries_headword ON cad_entries(headword);
CREATE INDEX IF NOT EXISTS idx_cad_entries_headword_norm ON cad_entries(headword_normalized);
CREATE INDEX IF NOT EXISTS idx_cad_entries_volume ON cad_entries(volume);
CREATE INDEX IF NOT EXISTS idx_cad_meanings_entry ON cad_meanings(entry_id);
CREATE INDEX IF NOT EXISTS idx_cad_attestations_entry ON cad_attestations(entry_id);
CREATE INDEX IF NOT EXISTS idx_cad_attestations_meaning ON cad_attestations(meaning_id);
CREATE INDEX IF NOT EXISTS idx_cad_attestations_period ON cad_attestations(period);
CREATE INDEX IF NOT EXISTS idx_cad_cross_refs_from ON cad_cross_references(from_entry_id);
CREATE INDEX IF NOT EXISTS idx_cad_cross_refs_to ON cad_cross_references(to_headword);
CREATE INDEX IF NOT EXISTS idx_cad_logograms_entry ON cad_logograms(entry_id);
CREATE INDEX IF NOT EXISTS idx_cad_logograms_sumerian ON cad_logograms(sumerian_form);

-- View for easy entry lookup with first definition
CREATE VIEW IF NOT EXISTS cad_entries_summary AS
SELECT
    e.id,
    e.headword,
    e.part_of_speech,
    e.volume,
    (SELECT m.definition FROM cad_meanings m WHERE m.entry_id = e.id ORDER BY m.id LIMIT 1) as first_definition,
    (SELECT COUNT(*) FROM cad_meanings m WHERE m.entry_id = e.id) as meaning_count,
    (SELECT COUNT(*) FROM cad_attestations a WHERE a.entry_id = e.id) as attestation_count
FROM cad_entries e;

-- Trigger to populate FTS index
CREATE TRIGGER IF NOT EXISTS cad_fts_insert AFTER INSERT ON cad_entries
BEGIN
    INSERT INTO cad_fts(rowid, headword, definition, akkadian_text, translation)
    SELECT
        NEW.id,
        NEW.headword,
        (SELECT GROUP_CONCAT(definition, '; ') FROM cad_meanings WHERE entry_id = NEW.id),
        (SELECT GROUP_CONCAT(akkadian_text, ' ') FROM cad_attestations WHERE entry_id = NEW.id),
        (SELECT GROUP_CONCAT(translation, ' ') FROM cad_attestations WHERE entry_id = NEW.id);
END;
