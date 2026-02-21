# Collections Import Summary

**Date:** 2026-02-20
**Script:** `source-data/import-tools/20_import_collections.py`

## Results

✅ Successfully ported collections from v0.1 SQLite database to v2 PostgreSQL database

### Statistics
- **Collections:** 14 ported (100%)
- **Cover Images:** 13 collections with cover images (93%)
- **Tablet Associations:** 335 out of 340 (98.5%)

### Collections Ported

| Collection | Tablets | Cover Image |
|-----------|---------|-------------|
| Gilgamesh | 128 | ✓ |
| Esarhaddon's Superstitions | 30 | ✓ |
| View Testing | 11 | ✗ |
| Enuma Elish | 7 | ✓ |
| Flood Stories | 3 | ✓ |
| Descent of Ishtar | 20 | ✓ |
| Tavern Songs & Hymns to Beer | 13 | ✓ |
| Poetry & Literature | 30 | ✓ |
| Complaint Letters | 30 | ✓ |
| Curses & Insults | 3 | ✓ |
| Royal Propaganda | 20 | ✓ |
| School Texts | 20 | ✓ |
| Rare Medical Texts | 1 | ✓ |
| Self Help & Wisdom | 19 | ✓ |

### Missing Artifacts (5 total)

The following 5 artifact references could not be ported because they don't exist in the artifacts table:

1. **P388265** (View Testing) - Test artifact, not in CDLI catalog
2. **Q000795** (Self Help & Wisdom) - Composite text (Q-number), belongs in composites table

Note: Q-numbers represent composite texts (reconstructed from multiple fragments) and should be handled separately from individual artifacts (P-numbers).

### Cover Photos

All cover photos were successfully ported and copied to the web app:
- **Source:** `app-v0.1/public_html/assets/images/collections/`
- **Destination:** `app/static/images/collections/`
- **Web path:** `/static/images/collections/Collection – [Name].jpg`
- **Status:** ✅ All 13 images verified and accessible

### Script Features

The import script (`20_import_collections.py`):
- ✅ Idempotent - safe to re-run
- ✅ Dry-run mode for previewing changes
- ✅ Handles missing artifacts gracefully
- ✅ Preserves all metadata (names, descriptions, images, timestamps)
- ✅ Maps old collection IDs to new ones
- ✅ Converts image paths from `/assets/` to `/static/`
- ✅ Reports detailed progress and errors

### Next Steps

- Consider importing Q000795 once composite texts are in the database
- Review "View Testing" collection - likely a development artifact
