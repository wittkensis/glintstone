# Answers to Planning Questions

## Glossary Caching (from 05-GLOSSARY-CACHING-STRATEGY.md)

### Q: What's best method for caching here?

**Recommendation: In-memory JavaScript Map with single fetch on app init**

**Why this approach:**
1. **Size is trivial** - 40KB uncompressed, ~10KB gzipped for top 53 entries
2. **Read-heavy workload** - Glossary lookups happen constantly, writes never
3. **Perfect hit rate** - Top 53 entries cover vast majority of lookups
4. **No complexity** - No cache invalidation, expiration, or synchronization needed

**Implementation:**
```javascript
// At app startup (one-time fetch)
async function initGlossaryCache() {
  const response = await fetch('/api/glossary/critical'); // Top 53 entries
  const entries = await response.json();

  // Store in Map for O(1) lookups by citation_form
  const glossaryCache = new Map(
    entries.map(e => [e.citation_form, e])
  );

  return glossaryCache;
}

// Usage (instant, no network)
const entry = glossaryCache.get('lugal'); // O(1)
if (entry) {
  showTooltip(entry.guide_word, entry.senses);
}
```

**Alternative (not recommended):**
- **localStorage**: Requires JSON serialization, slower than in-memory Map, no real benefit since data is static
- **IndexedDB**: Overkill for 40KB of data
- **Service Worker cache**: Unnecessary complexity for data that fits in memory

### Q: Is this caching expensive for frontend?

**No - it's extremely cheap:**

**Memory cost:**
- 40KB (uncompressed) = **0.04 MB**
- Modern browsers allocate **hundreds of MB** per tab
- This is 0.01% of typical available memory
- Negligible impact

**Performance cost:**
- **One-time fetch** at startup: ~50ms network + ~5ms parsing
- **Lookup time**: ~0.0001ms (single Map.get())
- **No GC pressure**: Static data, no allocations during lookups

**Comparison:**
- Single high-res image: 500KB-2MB (50x larger)
- Typical React component tree: 1-5MB (25-125x larger)
- Your glossary cache: 40KB (tiny)

**Best practice:**
```javascript
// Preload during app initialization
const [glossaryCache, artifacts] = await Promise.all([
  initGlossaryCache(),  // 40KB, instant lookups
  fetchArtifactList()   // Likely 100KB+
]);
```

---

## Composite Texts (from 04-COMPOSITE-TEXTS-DISPLAY.md)

### Q: How can/should we populate composite_designation? What's the difference between this and q_number?

**Difference:**
- **q_number**: Unique identifier (e.g., `Q000057`)
- **composite_designation**: Human-readable name (e.g., `"Diri Tablet 3"`)

**Current state:**
- `q_number` is populated for all 2,476 composites
- `composite_designation` is NULL for most/all composites

**How to populate:**

**Option 1: Import from ORACC composite catalogs**
```bash
# ORACC composite catalogs exist at:
/source-data/sources/ORACC/dcclt/json/dcclt/catalog/Q*.json

# Each contains:
{
  "designation": "Diri Tablet 3",
  "project": "dcclt",
  "ancient_author": null,
  "genre": "Lexical"
}
```

**SQL to populate:**
```sql
UPDATE composites
SET designation = %s
WHERE q_number = %s;
```

**Option 2: Generate from first exemplar designation**
If no catalog entry exists, use first exemplar's designation:
```sql
UPDATE composites c
SET designation = (
  SELECT CONCAT('Composite of ', a.designation)
  FROM artifact_composites ac
  JOIN artifacts a ON ac.p_number = a.p_number
  WHERE ac.q_number = c.q_number
  LIMIT 1
)
WHERE c.designation IS NULL;
```

**Recommendation:** Use Option 1 (ORACC catalogs) as primary, Option 2 as fallback.

### Q: Why are composites associated with line numbers?

**Purpose: Line-level attribution in composite text reconstruction**

**Context:**
A composite text is a **scholarly reconstruction** of an ideal text based on multiple damaged exemplars. The `line_ref` field tracks **which exemplar provides evidence for which line**.

**Example:**
```
Composite Q000057 "Diri Tablet 3"
  Line 1: "diri = šababum"
    ├─ P229672 (obverse 1): "diri = sza-ba-bu-um" ← line_ref = "o 1"
    ├─ P230451 (obverse 1): "diri = sza-ba-[bu]"  ← line_ref = "o 1"
    └─ P231802 (damaged, no line 1 preserved)    ← line_ref = NULL

  Line 2: "diri = nahallum"
    ├─ P229672 (obverse 2): "[di-ri] = na-hal-lum" ← line_ref = "o 2"
    └─ P231802 (obverse 1): "diri = na-ha-lum"    ← line_ref = "o 1" (different!)
```

**Why it matters:**
- Different tablets have different line numbering (damage, breaks)
- `line_ref` maps composite line → exemplar line
- Enables critical apparatus display: "Line 1: P229672 (o 1) reads X, P230451 (o 1) reads Y"

**Current state:**
- `line_ref` is NULL for most/all entries
- This is **advanced scholarly metadata** not always available
- ORACC composite projects may have this data in line-level JSON

**Recommendation:**
- **Phase 1:** Display composites without line-level attribution (just list exemplars)
- **Phase 2:** Import line_ref from ORACC composite line data if available
- **Phase 3:** Build editor for scholars to curate line-level attributions

### Q: What is a Critical Apparatus?

**Definition:**
A **critical apparatus** is a scholarly notation system that documents **textual variants** between different manuscripts/exemplars of the same work.

**Example:**
```
Composite Text (Reconstructed):
1. diri = šababum

Critical Apparatus:
1. šababum] P229672, P230451; šabābu P231802 (orthographic variant);
   sza-ba-[bu] P230455 (damaged ending); om. P230500 (line missing)
```

**Translation:**
- Line 1 reads "šababum"
- P229672 and P230451 both support this reading
- P231802 has variant spelling "šabābu"
- P230455 is damaged: "sza-ba-[bu]" with ending missing
- P230500 omits this line entirely (tablet damaged)

**For UI Display:**
```html
<div class="critical-apparatus">
  <h4>Line 1 Variants</h4>
  <ul>
    <li>
      <span class="reading">šababum</span>
      <span class="witnesses">P229672, P230451</span>
    </li>
    <li>
      <span class="reading">šabābu</span>
      <span class="witnesses">P231802</span>
      <span class="note">(orthographic variant)</span>
    </li>
    <li>
      <span class="reading">sza-ba-[bu]</span>
      <span class="witnesses">P230455</span>
      <span class="note">(damaged ending)</span>
    </li>
  </ul>
</div>
```

**Why it's important:**
- Shows which tablets support each reading
- Flags damaged/uncertain sections
- Documents scholarly reconstruction decisions
- Enables reader to assess reliability

**Implementation priority:**
- **Phase 1:** Not needed (just show individual tablets)
- **Phase 2:** Show exemplar list with links
- **Phase 3:** Build critical apparatus from line-level comparisons

---

## Must-Have Features

### Composite Text View for Translation

**Your note:** "Must have a view like this, but facilitate translation (not just a list of tablets)"

**Recommended UI:**

```
┌─────────────────────────────────────────────────────────────┐
│ Q000057: Diri Tablet 3                             [Translate Mode] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Split View]                                                │
│ ┌──────────────────────┬──────────────────────────────────┐ │
│ │ Composite Text       │ Exemplar Evidence                │ │
│ ├──────────────────────┼──────────────────────────────────┤ │
│ │ 1. diri = šababum    │ • P229672 (o 1): sza-ba-bu-um    │ │
│ │    "to walk"         │   [intact] Neo-Assyrian          │ │
│ │                      │ • P230451 (o 1): sza-ba-[bu]     │ │
│ │ [+ Add Translation]  │   [damaged] Neo-Assyrian         │ │
│ │                      │                                  │ │
│ │ 2. diri = nahallum   │ • P229672 (o 2): [di-ri]=na-ha   │ │
│ │    [No translation]  │   [damaged] Neo-Assyrian         │ │
│ │                      │ • P231802 (o 1): diri=na-ha-lum  │ │
│ │ [+ Add Translation]  │   [intact] Neo-Babylonian        │ │
│ └──────────────────────┴──────────────────────────────────┘ │
│                                                             │
│ [Export to ATF] [Save Draft] [Publish Translation]          │
└─────────────────────────────────────────────────────────────┘
```

**Key features:**
1. **Split view:** Composite (left) + Evidence (right)
2. **Inline translation:** Edit translations directly in composite view
3. **Exemplar references:** Click to see full tablet
4. **Damage indicators:** Show which readings are certain vs. damaged
5. **Export:** Generate ATF file with translations
6. **Versioning:** Save draft translations, publish when complete

**Database changes needed:**
```sql
-- New table for composite translations
CREATE TABLE composite_translations (
  id SERIAL PRIMARY KEY,
  q_number TEXT NOT NULL,
  line_number TEXT NOT NULL,
  translation TEXT NOT NULL,
  language TEXT DEFAULT 'en',
  translator_id INTEGER,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(q_number, line_number, language)
);
```

### Identify Similar/Identical Tablets

**Your note:** "Must have; identify similar/identical tablets"

**Feature: Tablet Similarity Finder**

**Use cases:**
1. **Find parallel exemplars** - "Show me other tablets with line 'diri = šababum'"
2. **Find composite relationships** - "What composites is this tablet part of?"
3. **Find joins** - "Does this fragment join with others?"
4. **Find duplicate texts** - "Are there other copies of this text?"

**Implementation:**

**UI Component:**
```html
<div class="tablet-similarity">
  <h3>Related Tablets</h3>

  <div class="similarity-section">
    <h4>Composite Exemplars (12)</h4>
    <p>Other witnesses to <a href="/composites/Q000057">Q000057</a></p>
    <ul>
      <li><a href="/tablets/P230451">P230451</a> - 87% overlap, Neo-Assyrian</li>
      <li><a href="/tablets/P231802">P231802</a> - 65% overlap, Neo-Babylonian</li>
    </ul>
  </div>

  <div class="similarity-section">
    <h4>Joined Fragments (2)</h4>
    <p>Physical joins (indicated by + in designation)</p>
    <ul>
      <li>K 03254 (this fragment)</li>
      <li>K 03779 (joined fragment)</li>
    </ul>
  </div>

  <div class="similarity-section">
    <h4>Content Matches (5)</h4>
    <p>Tablets with similar line sequences</p>
    <ul>
      <li><a href="/tablets/P240123">P240123</a> - 3 matching lines</li>
    </ul>
  </div>
</div>
```

**Database queries:**

```sql
-- 1. Find composite siblings
SELECT
  ac2.p_number,
  a.designation,
  a.period,
  COUNT(*) as shared_composite_lines
FROM artifact_composites ac1
JOIN artifact_composites ac2 ON ac1.q_number = ac2.q_number
JOIN artifacts a ON ac2.p_number = a.p_number
WHERE ac1.p_number = 'P229672'
  AND ac2.p_number != 'P229672'
GROUP BY ac2.p_number, a.designation, a.period
ORDER BY shared_composite_lines DESC;

-- 2. Find content similarity (via lemma sequences)
WITH target_lemmas AS (
  SELECT l.citation_form, l.guide_word, t.position
  FROM lemmatizations l
  JOIN tokens t ON l.token_id = t.id
  JOIN text_lines tl ON t.line_id = tl.id
  WHERE tl.p_number = 'P229672'
)
SELECT
  tl.p_number,
  COUNT(*) as matching_lemmas,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM target_lemmas), 1) as pct_match
FROM target_lemmas tg
JOIN lemmatizations l2 ON tg.citation_form = l2.citation_form
JOIN tokens t ON l2.token_id = t.id
JOIN text_lines tl ON t.line_id = tl.id
WHERE tl.p_number != 'P229672'
GROUP BY tl.p_number
HAVING COUNT(*) >= 3  -- At least 3 matching lemmas
ORDER BY matching_lemmas DESC
LIMIT 20;

-- 3. Find physical joins (parse designation)
SELECT p_number, designation
FROM artifacts
WHERE designation LIKE '%+%'
  AND designation LIKE '%K 03254%';  -- Find joins to K 03254
```

**Implementation priority:**
- **Phase 1:** Show composite exemplars (already have data)
- **Phase 2:** Show physical joins (parse designation)
- **Phase 3:** Content similarity via lemma matching

---

## Summary of Answers

| Question | Answer | Implementation |
|----------|--------|----------------|
| Best caching method? | In-memory JavaScript Map | Single fetch on init |
| Is caching expensive? | No - 40KB is negligible | ~0.01% of typical memory |
| Populate composite_designation? | Import from ORACC catalogs | Step 20+ import script |
| Why line_ref? | Line-level attribution for variants | Advanced scholarly feature |
| What's critical apparatus? | Variant readings documentation | Phase 3 feature |
| Translation view? | Split view: composite + evidence | New composite_translations table |
| Similar tablets? | 3 types: composite, joins, content | Queries ready, needs UI |

All features are technically feasible with current database. Priority: composite siblings → joins → content matching → critical apparatus.
