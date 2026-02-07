# Implementation Notes and Design Decisions

## Document Purpose

This document records technical design decisions, database schema trade-offs, educational philosophy, and implementation rationale for the CUNEIFORM Library Browser.

**Date Created**: 2026-02-07
**Related Implementation**: All `/library/` components and database migrations

---

## Core Design Principles

### 1. System Integration Over Silos

**Decision**: Knowledge Dictionary Sidebar and Library Browser share data model, APIs, and UI components.

**Rationale**:
- Consistent user experience across contexts
- Single source of truth for dictionary data
- Reduced maintenance burden (one codebase)
- Seamless navigation between tablet reading and dictionary exploration

**Implementation**:
- Shared JavaScript modules: `word-detail-renderer.js`, `dictionary-search.js`, `educational-help.js`
- Shared CSS components: `word-detail.css`, `educational-help.css`
- Same API endpoints: `/api/glossary.php`, `/api/library/word-detail.php`
- Bidirectional links: Sidebar → "View in Library", Library → "View on Tablet"

### 2. Progressive Disclosure for All Skill Levels

**Decision**: Educational tooltips with user-level adaptation (Student/Scholar/Expert).

**Rationale**:
- Serves both casual learners and academic researchers
- Doesn't overwhelm experts with beginner content
- Encourages exploration through contextual help
- Builds confidence for new users

**Implementation**:
- User level stored in localStorage
- Help toggle in site header
- Three rendering modes:
  - **Student**: Full explanations with examples
  - **Scholar**: Concise technical definitions
  - **Expert**: No tooltips (can be enabled on demand)

### 3. Academic Standards Compliance

**Decision**: Follow ORACC CBD 2.0 format and CAD entry structures.

**Rationale**:
- Compatibility with existing scholarly resources
- Familiar to Assyriologists and cuneiform scholars
- Enables future data exchange with ORACC projects
- Maintains scholarly credibility

**Standards Followed**:
- Entry IDs (ORACC format: `o0023086`)
- Field naming (headword, citation_form, guide_word, pos, language, icount)
- POS codes (N, V, AJ, AV, DP, etc.)
- Language codes (sux, akk, akk-x-stdbab, etc.)
- Sign list (OGSL compatibility)

---

## Database Schema Decisions

### Choice: SQLite vs PostgreSQL

**Decision**: Continue with SQLite.

**Rationale**:
- **Pros**:
  - Simple deployment (single file)
  - Excellent read performance for dictionary lookups
  - Zero configuration required
  - Perfect for personal/local apps (target use case)
  - Full-text search via FTS5 extension
- **Cons**:
  - Write contention under high concurrency (not a concern for single-user app)
  - Limited geospatial features (not needed)
- **Conclusion**: SQLite perfectly suits use case

### Table: `glossary_relationships`

**Decision**: Separate junction table instead of embedded JSON.

**Rationale**:
- **Pros**:
  - Queryable (find all synonyms, all translations)
  - Indexable (fast lookups)
  - Flexible relationship types
  - Bidirectional queries easy
- **Cons**:
  - Additional table to manage
  - Slightly more complex queries
- **Conclusion**: Relational model wins for querying needs

**Schema**:
```sql
CREATE TABLE glossary_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entry_id TEXT NOT NULL,
    to_entry_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- synonym, translation, cognate, etc.
    notes TEXT,
    confidence TEXT DEFAULT 'verified',
    FOREIGN KEY (from_entry_id) REFERENCES glossary_entries(entry_id),
    FOREIGN KEY (to_entry_id) REFERENCES glossary_entries(entry_id),
    UNIQUE (from_entry_id, to_entry_id, relationship_type)
);
```

**Trade-off**: More tables, but cleaner queries and better performance.

### Table: `glossary_senses`

**Decision**: Separate table for polysemy instead of JSON column.

**Rationale**:
- **Pros**:
  - Structured data (sense_number, definition, usage_context)
  - Supports percentage calculations
  - Can link to example lemmas
  - Extensible (add fields without schema changes to main table)
- **Cons**:
  - Most entries have only one sense (overhead for simple cases)
- **Conclusion**: Future-proofing justifies overhead

**Alternative Considered**: JSON column in `glossary_entries`
- Simpler for single-sense words
- But harder to query/aggregate across senses
- Rejected for maintainability

### Table: `sign_word_usage`

**Decision**: Pre-compute sign-word relationships instead of parsing on demand.

**Rationale**:
- **Pros**:
  - Fast lookups ("which words use sign KA?")
  - Supports frequency statistics
  - Enables value-type filtering (logographic vs syllabic)
- **Cons**:
  - Requires initial population from lemmas
  - Must update when new lemmas added
- **Conclusion**: Query performance critical for user experience

**Population Strategy**:
1. Parse all `lemmas.form` values to extract signs
2. Match signs to `signs.sign_id`
3. Determine value_type (logographic vs syllabic) from context
4. Insert into `sign_word_usage` with usage counts
5. Re-run when corpus updated

**Challenge**: Sign boundary detection in transliterations
- Heuristics needed: "ka-la-am" → ["KA", "LA", "AM"]
- Multi-character signs: "1(BAN₂)" is single sign
- Determinatives: "{d}inana" → ["{d}", "INANA"]

---

## API Design Decisions

### REST vs GraphQL

**Decision**: REST APIs with structured JSON responses.

**Rationale**:
- **Pros**:
  - Simpler for PHP backend
  - Easier caching (standard HTTP)
  - Predictable response shapes
  - Lower learning curve
- **Cons**:
  - Potential over-fetching (get more data than needed)
  - Multiple requests for complex views
- **Conclusion**: REST adequate for dictionary browsing use case

### Response Format: Nested vs Flat

**Decision**: Nested JSON for related data.

**Example**:
```json
{
  "entry_id": "o0032435",
  "headword": "lugal",
  "variants": [
    {"form": "lugal", "count": 189},
    {"form": "lugal-la", "count": 24}
  ],
  "related_words": {
    "translations": [
      {"entry_id": "a0015234", "headword": "šarru", "language": "akk"}
    ]
  }
}
```

**Rationale**:
- Reduces request count (one API call vs many)
- Easier client-side rendering
- Matches UI structure (sections on word detail page)

**Trade-off**: Larger responses, but acceptable with HTTP/2 compression.

### Search: Single Endpoint vs Multiple

**Decision**: Unified `/api/search.php` with category ranking.

**Rationale**:
- **Pros**:
  - Single search bar UI
  - Smart cross-category results
  - Automatic prioritization
- **Cons**:
  - Complex scoring logic
  - Harder to optimize per-category
- **Conclusion**: User experience justifies complexity

**Enhancement for Library**: Dedicated `/api/library/word-detail.php` for rich word data.

---

## UI/UX Design Philosophy

### Educational Layer

**Decision**: Optional tooltips with progressive disclosure.

**Rationale**:
- **Target Audiences**:
  1. Students learning cuneiform (need comprehensive guidance)
  2. Scholars doing research (want efficiency, minimal friction)
  3. Casual curious users (need gentle introduction)

**Approach**:
- Default to "Student" mode (help enabled)
- One-click toggle to "Expert" mode (help hidden)
- Help icons (ⓘ) always present but unobtrusive
- First-time welcome overlay (dismissible)

**Content Strategy**:
- **Student**: Full explanations with analogies
  - "The headword is like looking up 'go' instead of 'going' in an English dictionary"
- **Scholar**: Technical definition only
  - "Citation form (CF) for scholarly references"
- **Expert**: No text (tooltip hidden)

### Navigation: Breadth vs Depth

**Decision**: Card-based browse with deep detail pages.

**Rationale**:
- **Browse View** (breadth):
  - Show many words at once (grid/list)
  - Quick scanning for recognition
  - Filters for narrowing results
- **Detail View** (depth):
  - All information for single word
  - Multiple sections (expandable)
  - Links to related words

**Pattern**: Similar to e-commerce (product grid → product page).

### Filtering: Client-side vs Server-side

**Decision**: Server-side filtering with URL state.

**Rationale**:
- **Pros**:
  - Handles 21K+ entries efficiently
  - Shareable filter URLs
  - Works without JavaScript (progressive enhancement)
  - Simpler client-side code
- **Cons**:
  - Page reload on filter change (but fast with SQLite)
- **Conclusion**: Performance and shareability more important than SPA feel

**URL Format**: `/library/?lang=sux&pos=N&freq=50-500&page=2`

---

## Positional Semantics Implementation

### Decision: Optional "Word Position & Grammar" section

**Rationale**:
- Not all words have positional semantics
- Advanced feature (mark with "Advanced" badge)
- Useful for verbs, particles, and specific grammatical categories

**Display Logic**:
```php
// word.php
if (hasPositionalNotes($entry)) {
    renderPositionalSemanticsSection($entry);
}
```

**Data Source**:
- Manual curation for now (add notes to `glossary_notes` table)
- Future: Extract from grammatical analysis

**Example Implementation**:
```
dug₄ [speak] V

⚠️ Positional Note: This verb typically appears in final position
in Sumerian sentences (SOV order).

Example: "lugal e₂ dù" = "king house build" = "the king builds a house"

<details>
  <summary>Learn more about Sumerian word order</summary>
  Sumerian follows strict SOV (Subject-Object-Verb) order...
</details>
```

---

## CAD Integration Strategy

### Phased Approach

**Decision**: Three-phase digitization (priority words → full volumes → enhancement).

**Rationale**:
- **Phase 1** (100 words): Quick value delivery, test workflow
- **Phase 2** (8,000 words): Complete coverage, requires resources
- **Phase 3** (enhancement): Cross-linking and semantic enrichment

**Resource Estimation**:
- Phase 1: ~$50-100 API costs, 10-20 hours human time
- Phase 2: ~$2-3K API costs, 80-120 hours human time
- Phase 3: 40-60 hours curation

**Acceptable Trade-off**: Start small, prove value, then scale.

### Claude PDF Extraction vs OCR Pipeline

**Decision**: Use Claude Opus for PDF extraction.

**Rationale**:
- **Claude Pros**:
  - Handles specialized fonts (cuneiform, diacritics)
  - Understands structure (etymology, meanings, citations)
  - High accuracy for complex layouts
  - Returns structured JSON
- **OCR Pipeline Cons**:
  - Poor quality on specialized fonts
  - Requires extensive post-processing
  - Misses semantic structure
- **Conclusion**: Quality justifies API cost

**Quality Control**:
- Human review every 50th entry
- Extraction quality score (0.0-1.0)
- Flag low-confidence extractions for manual verification

---

## Performance Considerations

### Database Indexing

**Decision**: Index all filterable and foreign key columns.

**Indexes Created**:
```sql
-- glossary_entries
CREATE INDEX idx_glossary_headword ON glossary_entries(headword);
CREATE INDEX idx_glossary_language ON glossary_entries(language);
CREATE INDEX idx_glossary_pos ON glossary_entries(pos);
CREATE INDEX idx_glossary_icount ON glossary_entries(icount);

-- glossary_relationships
CREATE INDEX idx_rel_from ON glossary_relationships(from_entry_id);
CREATE INDEX idx_rel_to ON glossary_relationships(to_entry_id);
CREATE INDEX idx_rel_type ON glossary_relationships(relationship_type);

-- sign_word_usage
CREATE INDEX idx_swu_sign ON sign_word_usage(sign_id);
CREATE INDEX idx_swu_entry ON sign_word_usage(entry_id);
```

**Trade-off**: Storage overhead for faster queries (acceptable).

### Caching Strategy

**Decision**: No additional caching layer initially.

**Rationale**:
- SQLite already fast for reads (<200ms for filtered queries)
- Database fits in memory on modern systems
- Premature optimization avoided
- Can add Redis/Memcached later if needed

**Future Enhancement**: Cache common queries (top 100 words, recent searches).

---

## Educational Content Management

### Storage: JSON vs Database vs PHP Files

**Decision**: PHP array in `includes/educational-content.php`.

**Rationale**:
- **Pros**:
  - Easy to edit (no database migration for content changes)
  - Version controlled (git)
  - Fast (compiled by OPcache)
  - Simple deployment
- **Cons**:
  - Not editable via admin UI (but not needed)
- **Conclusion**: Simplicity wins

**Structure**:
```php
// includes/educational-content.php
return [
    'field_help' => [
        'headword' => [
            'student' => 'The headword is the standard dictionary form...',
            'scholar' => 'Dictionary lemma for reference.',
            'expert' => null
        ],
        // ... other fields
    ],
    'pos_codes' => [
        'N' => ['label' => 'Noun', 'definition' => '...'],
        // ... all POS codes
    ],
    'language_codes' => [
        'sux' => ['label' => 'Sumerian', 'description' => '...'],
        // ... all language codes
    ]
];
```

---

## Testing & Verification Strategy

### Phase 1 Testing Checklist

**Database**:
- [ ] All tables created
- [ ] Views return correct data
- [ ] Indexes improve query performance
- [ ] Relationships populated (100+ entries)
- [ ] Sign_word_usage populated (1000+ entries)

**APIs**:
- [ ] glossary-browse returns filtered results
- [ ] word-detail returns complete data
- [ ] signs-browse returns sign grid
- [ ] sign-detail returns values and words

**Frontend**:
- [ ] Dictionary browser loads
- [ ] Search returns results
- [ ] Filters update results
- [ ] Pagination works
- [ ] Word detail page renders all sections
- [ ] Signs grid displays cuneiform
- [ ] Sign detail shows values

**Integration**:
- [ ] Sidebar → Library link works
- [ ] Library → Tablet link works
- [ ] Educational tooltips toggle
- [ ] User level persists

**Cross-browser**:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari

---

## Future Enhancements

### Phase 2+

1. **Semantic Network Visualization**
   - Interactive graph of word relationships
   - D3.js or similar library
   - Filter by relationship type

2. **Advanced Search**
   - Multi-field form
   - Regular expression support
   - Boolean operators

3. **Sign Visual Search**
   - Draw sign to find matches
   - Image-based lookup
   - ML model for recognition

4. **Collaborative Features**
   - User annotations
   - Suggest cross-references
   - Report errors

5. **Export & Citation**
   - Export search results to CSV
   - Generate bibliographic citations
   - Print-friendly word detail view

---

## Security Considerations

### SQL Injection Prevention

**Implementation**:
- **Always** use prepared statements
- **Never** concatenate user input into SQL
- Validate/sanitize input types

**Example**:
```php
// GOOD
$stmt = $db->prepare("SELECT * FROM glossary_entries WHERE headword = :word");
$stmt->bindValue(':word', $userInput, SQLITE3_TEXT);

// BAD (vulnerable)
$sql = "SELECT * FROM glossary_entries WHERE headword = '$userInput'";
```

### XSS Prevention

**Implementation**:
- Escape all user-generated content: `htmlspecialchars()`
- Use Content-Security-Policy headers
- Sanitize before rendering

**Example**:
```php
// GOOD
echo '<span>' . htmlspecialchars($entry['headword'], ENT_QUOTES, 'UTF-8') . '</span>';

// BAD (vulnerable)
echo '<span>' . $entry['headword'] . '</span>';
```

---

## Lessons Learned

### What Worked Well

1. **Research-First Approach**
   - Documented standards before implementation
   - Avoided rework and design thrash

2. **Shared Components**
   - Sidebar + Library using same code
   - Reduced bugs, easier maintenance

3. **Progressive Enhancement**
   - Works without JavaScript
   - Educational layer optional

### What to Improve

1. **Sign Parsing Complexity**
   - Underestimated difficulty of extracting signs from transliterations
   - Need robust parser with edge case handling

2. **Testing Early**
   - Should have written unit tests for API endpoints
   - Manual testing time-consuming

3. **Documentation**
   - Research docs created early = good
   - Code comments = need more inline documentation

---

*Last Updated: 2026-02-07*
*Related Documents:*
- `Research/Dictionary-Standards.md` - Academic foundation
- `Research/Sign-Libraries.md` - Sign implementation details
- `Research/Multilingual-Navigation.md` - Cross-linguistic features
