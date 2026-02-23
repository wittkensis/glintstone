-- Migration 017: Scholar deduplication infrastructure
-- Adds normalized_name, author_type, and merge audit log

-- Normalized name for deduplication (e.g., "frayne_dr")
ALTER TABLE scholars ADD COLUMN IF NOT EXISTS normalized_name TEXT;
CREATE INDEX IF NOT EXISTS idx_scholars_normalized_name ON scholars(normalized_name);

-- Distinguish persons from institutions/projects/unknowns
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'scholars' AND column_name = 'author_type'
    ) THEN
        ALTER TABLE scholars ADD COLUMN author_type TEXT DEFAULT 'person';
        ALTER TABLE scholars ADD CONSTRAINT chk_author_type
            CHECK (author_type IN ('person', 'institution', 'project', 'unknown'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_scholars_author_type ON scholars(author_type);

-- Audit trail for merge operations
CREATE TABLE IF NOT EXISTS scholar_merge_log (
    id SERIAL PRIMARY KEY,
    kept_scholar_id INTEGER NOT NULL REFERENCES scholars(id),
    merged_scholar_id INTEGER NOT NULL,
    merged_name TEXT NOT NULL,
    merge_reason TEXT NOT NULL,
    merged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scholar_merge_log_kept ON scholar_merge_log(kept_scholar_id);
CREATE INDEX IF NOT EXISTS idx_scholar_merge_log_merged ON scholar_merge_log(merged_scholar_id);
