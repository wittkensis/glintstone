# Library Browser - Verification Steps

Quick guide to verify the Phase 1 implementation is working correctly.

## 1. Database Setup ✅

The migration has already been run. Verify it worked:

```bash
cd "/Volumes/Portable Storage/CUNEIFORM"

# Check tables exist
sqlite3 database/glintstone.db "
SELECT name FROM sqlite_master
WHERE type='table' AND (
  name LIKE 'glossary_%' OR
  name LIKE 'semantic_%' OR
  name LIKE 'sign_word%' OR
  name LIKE 'cad_%'
)
ORDER BY name;
"
```

**Expected**: 8 table names

## 2. Populate Data Tables

Run the data population scripts:

```bash
cd data-tools/import

# Populate sign-word usage (1-2 minutes)
python3 populate_sign_word_usage.py

# Expected output: ~1,000-5,000 relationships created

# Populate Sumerian↔Akkadian relationships (30 seconds)
python3 populate_relationships.py --min-freq 50

# Expected output: ~400-1,000 relationships created
```

**Verify population worked:**

```bash
cd "/Volumes/Portable Storage/CUNEIFORM"

# Check sign usage
sqlite3 database/glintstone.db "SELECT COUNT(*) as sign_usage_count FROM sign_word_usage;"

# Check relationships
sqlite3 database/glintstone.db "SELECT COUNT(*) as relationship_count FROM glossary_relationships;"

# Sample a few relationships
sqlite3 database/glintstone.db "
SELECT
    ge1.headword || '[' || ge1.guide_word || ']' as sux,
    ge2.headword as akk
FROM glossary_relationships gr
JOIN glossary_entries ge1 ON gr.from_entry_id = ge1.entry_id
JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
WHERE ge1.language = 'sux' AND ge2.language LIKE 'akk%'
LIMIT 5;
"
```

## 3. Test Frontend Pages

Open these URLs in your browser:

### Dictionary Browser
**URL**: http://localhost/library/
- [ ] Page loads without errors
- [ ] Search bar present
- [ ] Filters work (Language: Sumerian, then Akkadian)
- [ ] Entry cards display with headword, guide word, badges
- [ ] Pagination works
- [ ] Click an entry → navigates to word detail

### Word Detail
**URL**: http://localhost/library/word/o0032435
(or click any word from browse)
- [ ] Page loads with word data
- [ ] Header shows headword and guide word
- [ ] Badges display (POS, language, frequency)
- [ ] Sections render: Meanings, Variants, Signs, Related Words
- [ ] Help tooltips work (click ⓘ icons)
- [ ] Sign links work (click sign → navigates to sign detail)
- [ ] "Back to Dictionary Browser" button works

### Sign Grid
**URL**: http://localhost/library/signs.php
- [ ] Grid loads with cuneiform characters
- [ ] Filters work (sign type, frequency)
- [ ] Search finds signs (try "KA" or "LUGAL")
- [ ] Clicking sign → navigates to sign detail
- [ ] Pagination works

### Sign Detail
**URL**: http://localhost/library/sign/KA
(or click any sign from grid)
- [ ] Page loads with sign data
- [ ] Large cuneiform character displays
- [ ] Statistics show (total values, types, occurrences)
- [ ] Values grouped (logographic, syllabic, determinative)
- [ ] Words using sign listed with links
- [ ] Word links work → navigate to word detail
- [ ] "Back to Sign Library" button works

### Glossary Reference
**URL**: http://localhost/library/glossary.php
- [ ] Page loads
- [ ] Navigation links work (scroll to sections)
- [ ] POS table shows all 24 codes
- [ ] Language table shows all 12 codes
- [ ] Field explanations render
- [ ] "Back to Dictionary Browser" link works

## 4. Test ATF Viewer Integration

**URL**: http://localhost/tablets/detail.php?p=P100001
(or any tablet with ATF)

- [ ] Tablet detail page loads normally
- [ ] ATF viewer renders transliteration
- [ ] Click "Open knowledge sidebar" button (top right)
- [ ] Click any word in the transliteration
- [ ] Knowledge sidebar opens with Dictionary tab active
- [ ] Word detail displays using new renderer
- [ ] **"View in Library →" button appears at bottom**
- [ ] Click "View in Library" → opens word detail in new tab
- [ ] Help tooltips work in sidebar (click ⓘ icons)
- [ ] Browse mode still works (click different tabs)

## 5. Test Educational Help System

### First-Time Welcome
- [ ] Clear localStorage: Open browser console and run `localStorage.clear()`
- [ ] Visit `/library/`
- [ ] Welcome overlay appears
- [ ] User level selection works (click Student/Scholar/Expert)
- [ ] "Start browsing" dismisses overlay

### Help Toggle
- [ ] Help toggle button in site header works
- [ ] Clicking toggle hides/shows help icons (ⓘ)
- [ ] User level persists across page reloads
- [ ] Help content adapts to user level

## 6. Test Cross-Browser

Test in at least 2 browsers:
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if on macOS)

## 7. Quick Performance Check

### Query Speed
```bash
cd "/Volumes/Portable Storage/CUNEIFORM"

# Time a filtered browse query
time sqlite3 database/glintstone.db "
SELECT * FROM glossary_entries
WHERE language = 'sux' AND pos = 'N' AND icount >= 50
ORDER BY icount DESC LIMIT 50;
"
```
**Expected**: < 0.2 seconds

### Page Load
- Open browser DevTools → Network tab
- Visit `/library/`
- Check total load time
**Expected**: < 2 seconds (first load), < 1 second (cached)

## 8. Sample Verification Queries

### Check Top Translation Pairs
```sql
SELECT
    ge1.headword || '[' || ge1.guide_word || ']' as sumerian,
    ge2.headword as akkadian,
    ge1.icount as sux_freq,
    ge2.icount as akk_freq
FROM glossary_relationships gr
JOIN glossary_entries ge1 ON gr.from_entry_id = ge1.entry_id
JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
WHERE ge1.language = 'sux'
  AND ge2.language LIKE 'akk%'
  AND gr.relationship_type = 'translation'
ORDER BY ge1.icount DESC
LIMIT 20;
```

### Check Sign Usage Distribution
```sql
SELECT value_type, COUNT(*) as count
FROM sign_word_usage
GROUP BY value_type
ORDER BY count DESC;
```

### Top Signs by Word Count
```sql
SELECT
    s.sign_id,
    s.utf8,
    COUNT(DISTINCT swu.entry_id) as word_count,
    SUM(swu.usage_count) as total_uses
FROM sign_word_usage swu
JOIN signs s ON swu.sign_id = s.sign_id
GROUP BY s.sign_id
ORDER BY word_count DESC
LIMIT 10;
```

## Common Issues & Solutions

### "No entries match your filters"
- Check that glossary_entries table has data
- Try removing all filters
- Check database connection

### "No definition found" in ATF viewer
- Word may not be in ORACC glossaries
- Check lemmas table has data for that tablet
- Verify API endpoints return data

### Cuneiform characters not displaying
- Check that Noto Sans Cuneiform font is loaded
- Verify UTF-8 characters in database
- Check CSS font-family declarations

### "View in Library" button missing
- Check that integration script loaded (check browser console for errors)
- Verify educational-help.js and word-detail-renderer.js loaded first
- Check that API returned entry_id field

## Success Criteria

**Minimum to call it working:**
- ✅ Dictionary browser loads and shows entries
- ✅ Can filter by language (Sumerian/Akkadian)
- ✅ Can click entry → see word detail
- ✅ Sign grid loads and shows signs
- ✅ ATF viewer sidebar shows "View in Library" button

**Full success:**
- ✅ All pages load without errors
- ✅ All filters work
- ✅ All navigation links work
- ✅ Educational tooltips work
- ✅ Data populated (relationships, sign usage)
- ✅ ATF integration seamless

## Next Steps After Verification

If everything works:
1. ✅ Mark Phase 1 complete
2. Plan Phase 2 features (semantic fields, CAD data, advanced search)
3. Gather user feedback
4. Iterate on UX improvements

If issues found:
1. Document the issue
2. Check LIBRARY_IMPLEMENTATION_COMPLETE.md for troubleshooting
3. Review relevant code section
4. Fix and re-verify
