-- Remove Smart Collections Feature
-- Migration: 003_remove_smart_collections
-- Date: 2026-02-10

-- Drop smart collections table and indexes
DROP INDEX IF EXISTS idx_smart_collections_system;
DROP TABLE IF EXISTS smart_collections;
