-- Migration: Add filter stats tables for hierarchical filtering
-- These are permanent aggregation tables updated during data import

-- Language hierarchy with counts
CREATE TABLE IF NOT EXISTS language_stats (
    language TEXT PRIMARY KEY,
    root_language TEXT NOT NULL,  -- "Akkadian", "Sumerian", "Elamite", etc.
    tablet_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_language_stats_root ON language_stats(root_language);

-- Period stats with counts
CREATE TABLE IF NOT EXISTS period_stats (
    period TEXT PRIMARY KEY,
    period_group TEXT,            -- Optional grouping (e.g., "Third Millennium", "Second Millennium")
    sort_order INTEGER,           -- For chronological ordering
    tablet_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_period_stats_group ON period_stats(period_group);

-- Provenience hierarchy with counts
CREATE TABLE IF NOT EXISTS provenience_stats (
    provenience TEXT PRIMARY KEY,
    region TEXT NOT NULL,          -- "Babylonia", "Assyria", "Elam", etc.
    subregion TEXT,                -- Optional subdivision
    tablet_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_provenience_stats_region ON provenience_stats(region);

-- Genre hierarchy with counts
CREATE TABLE IF NOT EXISTS genre_stats (
    genre TEXT PRIMARY KEY,
    category TEXT NOT NULL,        -- "Administrative", "Scientific", "Literary", etc.
    tablet_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_genre_stats_category ON genre_stats(category);
