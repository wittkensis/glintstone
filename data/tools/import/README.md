# Data Population Scripts

Scripts to populate the Library Browser database tables with relationships and usage statistics.

## Prerequisites

- Python 3.7 or later
- SQLite database at `../../database/glintstone.db`
- Tables created via migration: `add_library_features.sql`

## Scripts

### 1. `populate_sign_word_usage.py`

Analyzes `lemmas` table to determine which cuneiform signs appear in which words, then populates the `sign_word_usage` table.

**What it does:**
- Parses word forms to extract individual signs (e.g., "ka-la-am" → ["ka", "la", "am"])
- Determines sign type (logographic, syllabic, determinative)
- Counts occurrences in corpus
- Creates sign_id ↔ entry_id relationships

**Usage:**
```bash
# Dry run (see what would happen)
python3 populate_sign_word_usage.py --dry-run

# Actually populate the table
python3 populate_sign_word_usage.py
```

**Expected output:**
- ~1,000-5,000 sign-word relationships
- Statistics on logographic vs syllabic vs determinative usage
- List of signs not found in database (for debugging)

### 2. `populate_relationships.py`

Creates cross-references between dictionary entries, focusing on Sumerian ↔ Akkadian translation pairs.

**What it does:**
- Matches Sumerian and Akkadian words via identical guide words
- Filters by part of speech (POS) to ensure accuracy
- Creates bidirectional translation relationships
- Focuses on high-frequency words (min-freq parameter)

**Usage:**
```bash
# Dry run with minimum frequency 50 (default)
python3 populate_relationships.py --dry-run

# Populate with minimum frequency 100 (stricter)
python3 populate_relationships.py --min-freq 100

# Populate with default settings
python3 populate_relationships.py
```

**Expected output:**
- ~200-500 translation pairs (400-1000 bidirectional relationships)
- Sample pairs showing Sumerian ↔ Akkadian equivalents
- Statistics by relationship type and confidence level

**Confidence levels:**
- `inferred_guidword`: Matched via guide word + POS (most common)
- `verified`: Manually verified (for future use)
- `attested_lexical_list`: From ancient lexical lists like Ura = hubullu (for future use)

## Execution Order

Run scripts in this order:

```bash
# 1. Populate sign usage first (independent)
python3 populate_sign_word_usage.py

# 2. Populate relationships second
python3 populate_relationships.py

# 3. Verify results
sqlite3 ../../database/glintstone.db "SELECT COUNT(*) FROM sign_word_usage"
sqlite3 ../../database/glintstone.db "SELECT COUNT(*) FROM glossary_relationships"
```

## Data Quality

### Sign-Word Usage

**Known limitations:**
- Complex compound signs may not parse correctly
- Some rare signs may not be in the `signs` table
- Phonetic complements may cause duplicate entries

**Quality indicators:**
- Check "signs not found" list in output
- Verify value_type distribution (should have mix of logographic/syllabic)
- Spot-check a few entries in database

### Relationships

**Known limitations:**
- Guide word matching is imperfect (semantic overlap ≠ exact translation)
- Does not account for polysemy (multiple meanings per word)
- Cultural concepts may not have one-to-one equivalents

**Quality indicators:**
- High-frequency words should have matches (lugal ↔ šarru)
- POS matching reduces false positives
- Manual verification recommended for top 100 pairs

## Re-running Scripts

Both scripts clear existing data before inserting new data:
- `populate_sign_word_usage.py`: Deletes all from `sign_word_usage`
- `populate_relationships.py`: Deletes inferred relationships only (preserves manual ones)

## Future Enhancements

### Sign-Word Usage
- [ ] Parse multi-character signs (e.g., "1(BAN₂)")
- [ ] Handle variant sign forms (@g, @t)
- [ ] Detect phonetic complements vs. main signs
- [ ] Track sign position within word (prefix, stem, suffix)

### Relationships
- [ ] Parse ancient lexical lists (Ura = hubullu, Aa = naqu)
- [ ] Add synonym detection within same language
- [ ] Add cognate relationships (Semitic language family)
- [ ] Add semantic field relationships
- [ ] Manual curation interface for verification

### Semantic Fields
- [ ] Create `populate_semantic_fields.py`
- [ ] Tag words with categories (kinship, royalty, agriculture, etc.)
- [ ] Support hierarchical field structure (parent_field_id)

## Troubleshooting

### "signs not found" warnings
- Some word forms may use sign IDs not in the `signs` table
- Check if signs exist: `sqlite3 ../../database/glintstone.db "SELECT * FROM signs WHERE sign_id = 'KA'"`
- May need to add missing signs to `signs` table

### Low relationship count
- Check min-freq parameter (lower = more relationships but lower quality)
- Verify guide words exist: `sqlite3 ../../database/glintstone.db "SELECT COUNT(*) FROM glossary_entries WHERE guide_word IS NOT NULL"`
- Check language distribution: Most Akkadian should be `akk` or `akk-x-*`

### Duplicate key errors
- Scripts use `INSERT OR IGNORE` to handle duplicates gracefully
- If persistent, check `UNIQUE` constraints on tables
- May indicate data quality issues (same relationship inserted twice)

## Verification Queries

After running scripts, verify data quality:

```sql
-- Check sign usage distribution
SELECT value_type, COUNT(*) as cnt
FROM sign_word_usage
GROUP BY value_type;

-- Top signs by word count
SELECT s.sign_id, s.utf8, COUNT(DISTINCT swu.entry_id) as word_count
FROM sign_word_usage swu
JOIN signs s ON swu.sign_id = s.sign_id
GROUP BY s.sign_id
ORDER BY word_count DESC
LIMIT 10;

-- Translation pairs
SELECT
    ge1.headword as sux_word,
    ge1.guide_word,
    ge2.headword as akk_word,
    ge2.language as akk_lang
FROM glossary_relationships gr
JOIN glossary_entries ge1 ON gr.from_entry_id = ge1.entry_id
JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
WHERE ge1.language = 'sux'
  AND ge2.language LIKE 'akk%'
  AND gr.relationship_type = 'translation'
ORDER BY ge1.icount DESC
LIMIT 20;
```

## Support

For issues or questions:
1. Check script output for error messages
2. Verify database schema matches migration
3. Check data quality with verification queries above
4. Review `Research/Implementation-Notes.md` for design decisions
