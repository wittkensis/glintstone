-- Add metadata cache columns to composites table
-- These columns store aggregated metadata from tablets to avoid expensive joins on every page load

-- Add cache columns for aggregated metadata
ALTER TABLE composites ADD COLUMN periods_cache TEXT;
ALTER TABLE composites ADD COLUMN proveniences_cache TEXT;
ALTER TABLE composites ADD COLUMN genres_cache TEXT;
ALTER TABLE composites ADD COLUMN exemplar_count_cache INTEGER DEFAULT 0;
ALTER TABLE composites ADD COLUMN metadata_updated_at TIMESTAMP;

-- Note: These columns will be populated on-demand when getCompositesWithMetadata() is called
-- The cache is refreshed when exemplar_count_cache doesn't match the current tablet count
