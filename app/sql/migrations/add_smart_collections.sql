-- Migration: Add Smart Collections feature
-- Description: Creates smart_collections table for parameter-based dynamic collections
-- Date: 2026-02-07

-- Create smart_collections table
CREATE TABLE IF NOT EXISTS smart_collections (
    smart_collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT, -- emoji or icon identifier
    query_type TEXT NOT NULL, -- 'mixed', 'pipeline', 'temporal', 'literary', 'quality', 'connectivity', 'custom'
    query_params TEXT NOT NULL, -- JSON string storing filter criteria and thresholds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_system INTEGER DEFAULT 1 -- 1 = system-created (manual), 0 = user-created (future)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_smart_collections_system ON smart_collections(is_system);

-- Insert initial system Smart Collections

-- 1. Noteworthy Works (mixed criteria: literary + quality + connectivity)
INSERT INTO smart_collections (name, description, icon, query_type, query_params) VALUES (
    'Noteworthy Works',
    'Tablets from significant literary works, high-quality exemplars, and highly-connected manuscripts that represent the best of the collection',
    '⭐',
    'mixed',
    '{"criteria": ["literary_works", "high_quality", "high_connectivity"], "literary_patterns": ["Gilgamesh", "Enuma", "Atrahasis", "Hammurabi"], "quality_threshold": 0.8, "composite_threshold": 2, "limit_per_criteria": 4}'
);

-- 2. Ready for Translation (pipeline status: has image, no ATF)
INSERT INTO smart_collections (name, description, icon, query_type, query_params) VALUES (
    'Ready for Translation',
    'High-quality images awaiting transcription - the biggest opportunity for contribution',
    '🎯',
    'pipeline',
    '{"has_image": 1, "has_atf": 0, "quality_threshold": 0.3}'
);

-- 3. Recently Active (temporal: updated in last 30 days)
INSERT INTO smart_collections (name, description, icon, query_type, query_params) VALUES (
    'Recently Active',
    'Tablets updated in the last 30 days showing active research progress',
    '⚡',
    'temporal',
    '{"days_ago": 30, "require_content": true}'
);

-- Verify inserts
SELECT 'Smart Collections migration complete. ' || COUNT(*) || ' collections created.' as result
FROM smart_collections;
