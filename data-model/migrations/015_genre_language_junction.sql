-- Migration 015: Genre and language junction tables
-- Decompose compound genre/language strings into many-to-many relationships
-- with confidence scores (1.0 = certain, 0.7 = uncertain, 0.5 = pseudo)

-- ── Canonical genre lookup (deduplicated, ~20 rows) ──
CREATE TABLE IF NOT EXISTS canonical_genres (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- ── Junction: artifact <-> genre (many-to-many) ──
CREATE TABLE IF NOT EXISTS artifact_genres (
    p_number TEXT NOT NULL REFERENCES artifacts(p_number),
    genre_id INTEGER NOT NULL REFERENCES canonical_genres(id),
    confidence REAL NOT NULL DEFAULT 1.0,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (p_number, genre_id)
);
CREATE INDEX IF NOT EXISTS idx_ag_genre ON artifact_genres(genre_id);

-- ── Canonical language lookup (deduplicated, ~22 rows) ──
CREATE TABLE IF NOT EXISTS canonical_languages (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    oracc_code TEXT,
    family TEXT
);

-- ── Junction: artifact <-> language (many-to-many) ──
CREATE TABLE IF NOT EXISTS artifact_languages (
    p_number TEXT NOT NULL REFERENCES artifacts(p_number),
    language_id INTEGER NOT NULL REFERENCES canonical_languages(id),
    confidence REAL NOT NULL DEFAULT 1.0,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (p_number, language_id)
);
CREATE INDEX IF NOT EXISTS idx_al_lang ON artifact_languages(language_id);
