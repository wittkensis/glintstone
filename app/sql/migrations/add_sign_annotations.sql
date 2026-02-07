-- Migration: Add sign_annotations table for OCR bounding box data
-- Sources: eBL cuneiform-ocr-data, CompVis sign-detection-dataset

CREATE TABLE IF NOT EXISTS sign_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    p_number TEXT NOT NULL,
    sign_label TEXT,              -- Sign name/class (MZL number or eBL label)
    bbox_x REAL NOT NULL,         -- X position as percentage (0-100)
    bbox_y REAL NOT NULL,         -- Y position as percentage (0-100)
    bbox_width REAL NOT NULL,     -- Width as percentage (0-100)
    bbox_height REAL NOT NULL,    -- Height as percentage (0-100)
    confidence REAL,              -- Detection confidence (0-1)
    surface TEXT,                 -- 'obverse', 'reverse', etc.
    atf_line INTEGER,             -- Associated ATF line number (if computed)
    source TEXT NOT NULL,         -- 'compvis', 'ebl', 'manual', 'ml'
    image_type TEXT DEFAULT 'photo', -- 'photo' or 'lineart'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (p_number) REFERENCES artifacts(p_number)
);

-- Index for fast lookups by tablet
CREATE INDEX IF NOT EXISTS idx_sign_annotations_p_number ON sign_annotations(p_number);

-- Index for filtering by source
CREATE INDEX IF NOT EXISTS idx_sign_annotations_source ON sign_annotations(source);

-- View to get annotation counts per tablet
CREATE VIEW IF NOT EXISTS annotation_coverage AS
SELECT
    a.p_number,
    a.designation,
    COUNT(sa.id) as annotation_count,
    GROUP_CONCAT(DISTINCT sa.source) as sources
FROM artifacts a
LEFT JOIN sign_annotations sa ON a.p_number = sa.p_number
GROUP BY a.p_number;
