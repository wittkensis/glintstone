# Composite Text Display Strategy

## Q4: How Should Joined Fragments Be Displayed?

### Answer: Multiple Approaches Based on Context

The database contains **2,476 composite linkages** between physical tablets (P-numbers) and ideal composite texts (Q-numbers). Additionally, some tablets are **joined fragments** indicated by `+` in the designation.

---

## Types of Composites

### Type 1: Exemplar → Composite (P→Q Linkage)

**Concept:** Multiple physical tablets are witnesses to a single ideal text.

**Example from Database:**
```
P000001 (CDLI Lexical 000002, ex. 065) → Q000002
P000002 (CDLI Lexical 000002, ex. 066) → Q000002
P000004 (CDLI Lexical 000002, ex. 051) → Q000002
P000005 (CDLI Lexical 000002, ex. 172) → Q000002
```

- **P-number:** Physical artifact (e.g., a tablet in British Museum)
- **Q-number:** Composite/ideal text (e.g., "Standard version of Enūma Eliš")
- **Relationship:** P-number is an "exemplar" of Q-number

**Database Structure:**
```sql
SELECT
    ac.p_number,
    a.designation as artifact_designation,
    ac.q_number,
    c.designation as composite_designation,
    ac.line_ref
FROM artifact_composites ac
JOIN artifacts a ON ac.p_number = a.p_number
JOIN composites c ON ac.q_number = c.q_number
WHERE ac.p_number = 'P229672';
```

**Result for P229672:**
```
p_number: P229672
q_number: Q000057
composite_designation: (NULL - not populated) # @wittkensis: How can/should we populate this? What's the difference bt this and q_number?
line_ref: (NULL - not populated) # @wittkensis: Why are composites associated with line numbers?
```

---

### Type 2: Joined Fragments (Physical Joins)

**Concept:** Multiple fragments have been physically identified as belonging to the same original tablet.

**Identified by `+` in designation:**
```sql
SELECT p_number, designation
FROM artifacts
WHERE designation LIKE '%+%'
LIMIT 10;
```

**Examples:**
```
P229672: K 03254 + K 03779
P231592: K 06928 + Sm 1896
P231625: K 06977 + K 09764 + K 10740
P231663: K 07031 + K 11884
P231697: K 07079 + K 12051
```

**Meaning:**
- Museum fragments K 03254 and K 03779 are now recognized as parts of the same tablet
- They should be treated as a single logical artifact for display
- P-number (P229672) is the canonical identifier for the joined piece

---

## Display Approaches

### Approach 1: Exemplar Badge (Recommended for P→Q)

**When:** Viewing a physical tablet (P-number) that is an exemplar of a composite

**Display:**
```
┌─────────────────────────────────────────┐
│ P229672: K 03254 + K 03779              │
│                                         │
│ [Exemplar Badge]                        │
│ This tablet is an exemplar of Q000057   │
│ See 12 other exemplars ›                │
└─────────────────────────────────────────┘
```

**Component:**
```html
<div class="translation-pipeline__exemplar-badge">
  <div class="exemplar-badge">
    <span class="exemplar-badge__label">Exemplar</span>
    <span class="exemplar-badge__composite-link">
      <a href="/composites/Q000057">Q000057</a>
    </span>
    <span class="exemplar-badge__count">
      See 12 other exemplars ›
    </span>
  </div>
</div>
```

**Interaction:**
- Click badge → Navigate to composite view (Q-number page)
- Click "See exemplars" → List all P-numbers for this composite
- Subtle, non-intrusive placement (header or sidebar)

---

### Approach 2: Join Metadata Display (Recommended for Physical Joins)

**When:** Viewing a joined fragment (designation contains `+`)

**Display:**
```
┌─────────────────────────────────────────┐
│ K 03254 + K 03779                       │
│ P229672                                 │
│                                         │
│ [Join Information]                      │
│ This tablet is a join of 2 fragments:   │
│ • K 03254 (museum number)               │
│ • K 03779 (museum number)               │
│                                         │
│ Joined: (date unknown)                  │
│ Join type: Physical                     │
└─────────────────────────────────────────┘
```

**Component:**
```html
<div class="translation-pipeline__join-info">
  <div class="join-info">
    <h3 class="join-info__title">Joined Fragments</h3>
    <ul class="join-info__fragments">
      <li class="join-info__fragment">K 03254</li>
      <li class="join-info__fragment">K 03779</li>
    </ul>
  </div>
</div>
```

**Extraction Logic:**
```javascript
function parseJoinedFragments(designation) {
  // Split on '+' and trim whitespace
  if (!designation.includes('+')) return null;

  const fragments = designation
    .split('+')
    .map(f => f.trim())
    .filter(f => f.length > 0);

  return {
    type: 'physical_join',
    fragments: fragments,
    count: fragments.length
  };
}

// Example:
parseJoinedFragments('K 03254 + K 03779');
// Returns: { type: 'physical_join', fragments: ['K 03254', 'K 03779'], count: 2 }
```

---

### Approach 3: Composite Text View (Future)

**When:** Viewing a composite text (Q-number page)

**Display:**
```
┌─────────────────────────────────────────┐
│ Q000057: Diri Tablet 3                  │ # @wittkensis: Must have a view like this, but faciltiate translation (not just a list of tablets)
│                                         │
│ [Composite View]                        │
│                                         │
│ Exemplars (12):                         │
│ • P229672 (K 03254 + K 03779) - Neo-Ass │
│ • P230451 (K 04556) - Neo-Assyrian      │
│ • P231802 (BM 45678) - Neo-Assyrian     │
│                                         │
│ [Composite Text]                        │
│ 1. diri ~ ($ blank) = šababum           │
│ 2. diri ~ ($ blank) = nahallum          │
│                                         │
│ [Critical Apparatus]                    │ # @wittkensis: What is a Critical Apparatus?
│ Line 1: P229672 reads "sza-ba-bu-um"    │
│         P230451 reads "sza-ba-[bu]"     │
└─────────────────────────────────────────┘
```

**Components:**
- Exemplar list (clickable P-numbers)
- Composite text reconstruction
- Critical apparatus showing variant readings
- Source attributions per line

**Database Queries:**
```sql
-- Get all exemplars for a composite
SELECT
    ac.p_number,
    a.designation,
    a.period,
    a.provenience,
    ac.line_ref
FROM artifact_composites ac
JOIN artifacts a ON ac.p_number = a.p_number
WHERE ac.q_number = 'Q000057'
ORDER BY a.period, a.designation;

-- Get composite metadata
SELECT *
FROM composites
WHERE q_number = 'Q000057';
```

---

### Approach 4: Inline Variant Indicators

**When:** Viewing a line that has multiple exemplar readings

**Display:**
```
Line 3 (obverse):
  ATF: # diri ~ ($ blank) = %a sza-ba-bu-um
  Translation: "to walk"

  [Other Exemplars:]                            # @wittkensis: Must have; identify similar/identical tablets
  • P230451: "sza-ba-[bu]" (damaged ending)
  • P231802: "sza-ba-bu-u2" (variant orthography)
```

**Component:**
```html
<div class="translation-line__variants">
  <div class="line-variants">
    <h4 class="line-variants__title">Other Exemplars</h4>
    <ul class="line-variants__list">
      <li class="line-variant">
        <a href="/artifacts/P230451" class="line-variant__link">P230451</a>:
        <span class="line-variant__reading">sza-ba-[bu]</span>
        <span class="line-variant__note">(damaged ending)</span>
      </li>
    </ul>
  </div>
</div>
```

---

## Implementation Priorities

### Phase 1: Basic Join Display (Now)

1. ✅ Detect `+` in designation
2. ✅ Parse fragment names
3. ✅ Display join metadata in header
4. ✅ Link to fragment museum numbers if available

**Effort:** Low
**Impact:** Medium (clear communication of joined status)

### Phase 2: Exemplar Badges (Short-term)

1. ✅ Check `artifact_composites` for Q-number linkage
2. ✅ Display exemplar badge with composite link
3. ✅ Count total exemplars for composite
4. ⬜ Link to composite page (if implemented)

**Effort:** Low
**Impact:** High (enables scholarly navigation)

### Phase 3: Composite Text Pages (Long-term)

1. ⬜ Create Q-number routes (`/composites/{q_number}`)
2. ⬜ Fetch all exemplars for composite
3. ⬜ Reconstruct composite text from exemplars
4. ⬜ Display critical apparatus with variant readings
5. ⬜ Line-level source attribution

**Effort:** High
**Impact:** Very High (core scholarly feature)

### Phase 4: Variant Indicators (Future)

1. ⬜ Compare readings across exemplars
2. ⬜ Detect variant orthographies
3. ⬜ Display inline variant notices
4. ⬜ Scholarly discussion integration

**Effort:** Very High
**Impact:** Very High (advanced scholarly tool)

---

## Data Availability

### What Exists in Database

```sql
-- artifact_composites table: 2,476 rows
SELECT COUNT(*) FROM artifact_composites;
-- Result: 2,476

-- Composites with multiple exemplars
SELECT q_number, COUNT(*) as exemplar_count
FROM artifact_composites
GROUP BY q_number
HAVING COUNT(*) > 1
ORDER BY exemplar_count DESC
LIMIT 10;
```

### What's Missing

- ❌ `composites.designation` mostly NULL (not populated)
- ❌ `artifact_composites.line_ref` mostly NULL (no line-level attribution)
- ❌ No composite text reconstruction (would require manual curation)
- ❌ No critical apparatus data (variants not systematically tracked)

**Conclusion:** Can display **basic composite linkages** now, but **full composite text views** require significant data curation.

---

## UI Component Examples

### Join Info Component (Simple)

```javascript
function renderJoinInfo(artifact) {
  const join = parseJoinedFragments(artifact.designation);
  if (!join) return null;

  return `
    <div class="join-info">
      <h3 class="join-info__title">Joined Fragments (${join.count})</h3>
      <ul class="join-info__fragments">
        ${join.fragments.map(frag => `
          <li class="join-info__fragment">${frag}</li>
        `).join('')}
      </ul>
    </div>
  `;
}
```

### Exemplar Badge Component

```javascript
async function renderExemplarBadge(pNumber) {
  // Fetch composite linkages
  const composites = await fetch(`/api/artifacts/${pNumber}/composites`);
  if (!composites.length) return null;

  const composite = composites[0]; // Primary composite
  const exemplarCount = await fetch(`/api/composites/${composite.q_number}/exemplars/count`);

  return `
    <div class="exemplar-badge">
      <span class="exemplar-badge__label">Exemplar of</span>
      <a href="/composites/${composite.q_number}" class="exemplar-badge__link">
        ${composite.q_number}
      </a>
      <span class="exemplar-badge__count">
        (${exemplarCount} exemplars)
      </span>
    </div>
  `;
}
```

---

## Recommendations

### For Current UI

1. **Implement Join Info Display** (Phase 1)
   - Parse designation for `+`
   - Display fragment list in header
   - Low effort, immediate value

2. **Add Exemplar Badge** (Phase 2)
   - Query `artifact_composites` table
   - Display Q-number link
   - Enable navigation to related exemplars

3. **Defer Composite Pages** (Phase 3+)
   - Requires data curation
   - Requires line-level attribution
   - Plan for future scholarly feature

### For API Design

**New Endpoints Needed:**
```
GET /api/artifacts/{p_number}/composites
GET /api/composites/{q_number}
GET /api/composites/{q_number}/exemplars
GET /api/composites/{q_number}/exemplars/count
```

---

## Conclusion

**Implement Phases 1 & 2 now:**
- ✅ Join fragment display (parse `+` in designation)
- ✅ Exemplar badge (query `artifact_composites`)

**Defer to future:**
- ⬜ Composite text reconstruction (requires curation)
- ⬜ Critical apparatus (requires variant tracking)
