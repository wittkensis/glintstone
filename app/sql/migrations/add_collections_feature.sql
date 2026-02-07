-- Migration: Add Collections Feature
-- Date: 2026-02-07
-- Description: Create tables for user collections to organize tablets

-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name);
CREATE INDEX IF NOT EXISTS idx_collections_created ON collections(created_at DESC);

-- Collection members (many-to-many relationship between collections and artifacts)
CREATE TABLE IF NOT EXISTS collection_members (
    collection_id INTEGER NOT NULL,
    p_number TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, p_number),
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id) ON DELETE CASCADE,
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_collection_members_collection ON collection_members(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_members_added ON collection_members(collection_id, added_at);
