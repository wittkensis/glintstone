# J5: CDLI Integration Demonstration Journey

**Document Type:** Journey PRD
**Priority:** P1 (Should Have)
**Status:** Ready
**Estimated Complexity:** S
**Dependencies:** L1-L3 (Design System, Dummy Data, Tablet Components)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| User Type | All (primarily Academic stakeholders) |
| Journey Scope | Integration Landing -> Tablet Lookup Demo -> Export Preview |
| UX Strategy Reference | Section 2.5: Secondary Path W-E3 (Explore Tablets Archive) |
| Ecosystem Reference | ecosystem-research-report.md Section 5.2 (CDLI Integration Strategy) |

---

## Journey Narrative

A CDLI representative, academic stakeholder, or curious scholar wants to understand how Glintstone integrates with the existing cuneiform digital ecosystem. They explore a demonstration of how Glintstone tablets link to CDLI P-numbers, how data flows between systems, and what "integration" actually means in practice.

This journey builds trust with the academic community by demonstrating:
1. Respect for existing infrastructure (CDLI is the source of truth)
2. Data interoperability (P-numbers, ATF format)
3. No duplication of effort (Glintstone as acceleration layer)
4. Bidirectional value (CDLI provides metadata, Glintstone provides transcriptions)

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Experience | Integration concept is clear | > 85% understanding |
| Trust | Perceived as complementary, not competing | Qualitative positive |
| Behavior | Visitors complete demo walkthrough | > 50% |
| Outcome | Academic stakeholder interest | Qualitative |

---

## Journey Map

### Stage 1: Integration Landing

**User Goal:** Understand Glintstone's ecosystem position

**System Response:**
- Clear positioning statement
- Visual diagram of data flow
- Entry to interactive demo

**Integration Landing Page:**

```
+--------------------------------------------------+
|  [Logo]  Contribute  Explore  Learn  [Profile]   |
+--------------------------------------------------+
|                                                   |
|   ECOSYSTEM INTEGRATION                           |
|                                                   |
|   Glintstone works with the tools you trust.      |
|   Not instead of them.                            |
|                                                   |
+--------------------------------------------------+
|                                                   |
|   HOW GLINTSTONE FITS IN                          |
|                                                   |
|   +-------------------------------------------+   |
|   |                                           |   |
|   |  +--------+      +-------------+          |   |
|   |  |  CDLI  | ---> | GLINTSTONE  |          |   |
|   |  +--------+      +-------------+          |   |
|   |    Catalog         Acceleration           |   |
|   |    Metadata        Transcription          |   |
|   |    Images          Translation            |   |
|   |                    Crowd + AI             |   |
|   |                         |                 |   |
|   |                         v                 |   |
|   |                   +----------+            |   |
|   |                   |  ORACC   |            |   |
|   |                   +----------+            |   |
|   |                   Publication             |   |
|   |                   Lemmatization           |   |
|   |                   Scholarly Editions      |   |
|   +-------------------------------------------+   |
|                                                   |
|            [Try the Integration Demo]             |
|                                                   |
+--------------------------------------------------+
```

**Key Positioning Messages:**

| Message | Explanation |
|---------|-------------|
| "Complementary, not competing" | CDLI remains the catalog of record |
| "Acceleration layer" | Glintstone adds speed, not duplication |
| "Your workflow, enhanced" | Export to ORACC, familiar formats |
| "P-numbers everywhere" | CDLI identifiers are our foreign keys |

**Acceptance Criteria:**
- [ ] Data flow diagram is clear and accurate
- [ ] CDLI positioned as upstream source
- [ ] ORACC positioned as downstream destination
- [ ] Glintstone's role is explicitly "acceleration"
- [ ] Demo CTA is prominent

---

### Stage 2: Tablet Lookup Demo

**User Goal:** See how CDLI linking works

**System Response:**
- P-number search interface
- Demo lookup of known tablet
- Display of linked metadata

**Lookup Interface:**

```
+--------------------------------------------------+
|  CDLI TABLET LOOKUP                               |
+--------------------------------------------------+
|                                                   |
|   Enter a CDLI P-number to see integration:       |
|                                                   |
|   [P] [123456        ] [Look up]                  |
|                                                   |
|   Try these examples:                             |
|   P123456 | P789012 | P345678                     |
|                                                   |
+--------------------------------------------------+
```

**Lookup Result:**

```
+--------------------------------------------------+
|  TABLET FOUND                                     |
+--------------------------------------------------+
|                                                   |
|  +-------------------+   METADATA FROM CDLI       |
|  |                   |                            |
|  |  [Tablet image]   |   P-number: P123456        |
|  |                   |   Museum: YBC 4644         |
|  |  [Obv] [Rev]      |   Collection: Yale         |
|  +-------------------+   Period: Old Babylonian   |
|                          Language: Akkadian       |
|  GLINTSTONE STATUS       Genre: Letter            |
|                          Dimensions: 45x32x18mm   |
|  Transcription: 78%                               |
|  Contributors: 12        [View in CDLI ->]        |
|  Expert Reviews: 1                                |
|                                                   |
+--------------------------------------------------+
|                                                   |
|  GLINTSTONE TRANSCRIPTION (Draft)                 |
|                                                   |
|  @obverse                                         |
|  1. a-na {d}utu be-li2-ia         [Accepted]     |
|  2. um-ma {m}a-bi-e-szar2-rum     [Under Review] |
|  3. ar-du-ka-a-ma                 [Proposed]     |
|                                                   |
|  [Export ATF] [Contribute to this tablet]         |
|                                                   |
+--------------------------------------------------+
```

**Demo Data Requirements:**

Prepare 3-5 tablets with realistic P-numbers:
- At least 1 should link to a real CDLI entry (for the outbound link)
- Others can use fictional P-numbers with "demo" metadata
- Each should have varying completion states

**Acceptance Criteria:**
- [ ] P-number input field with validation (format: P + 6 digits)
- [ ] Example P-numbers provided for easy testing
- [ ] Found state shows CDLI metadata clearly labeled
- [ ] Glintstone progress/status shown separately
- [ ] "View in CDLI" link opens real CDLI if P-number exists
- [ ] Not found state handled gracefully

---

### Stage 3: Data Provenance Display

**User Goal:** Understand what data comes from where

**System Response:**
- Clear labeling of data sources
- Provenance indicators throughout
- Transparency about what Glintstone adds

**Provenance Visualization:**

```
+--------------------------------------------------+
|  DATA SOURCES                                     |
+--------------------------------------------------+
|                                                   |
|  From CDLI:                       [CDLI logo]     |
|  +--------------------------------------------+   |
|  | - P-number (P123456)                       |   |
|  | - Museum number (YBC 4644)                 |   |
|  | - Collection (Yale Babylonian Collection)  |   |
|  | - Period classification (Old Babylonian)   |   |
|  | - Language (Akkadian)                      |   |
|  | - Genre (Letter)                           |   |
|  | - Provenience (Sippar, uncertain)          |   |
|  | - Physical dimensions                      |   |
|  | - Tablet images (when available)           |   |
|  +--------------------------------------------+   |
|                                                   |
|  Added by Glintstone:           [Glintstone logo] |
|  +--------------------------------------------+   |
|  | - AI-proposed transcription                |   |
|  | - Crowdsourced verification                |   |
|  | - Expert review status                     |   |
|  | - Confidence scores                        |   |
|  | - Contribution history                     |   |
|  | - Translation (when available)             |   |
|  +--------------------------------------------+   |
|                                                   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] Clear visual separation of data sources
- [ ] CDLI data labeled with CDLI attribution
- [ ] Glintstone contributions labeled separately
- [ ] No ambiguity about data provenance

---

### Stage 4: Export Demo

**User Goal:** See how data can be exported for scholarly use

**System Response:**
- ATF format preview
- Export options demonstration
- Attribution handling

**Export Preview:**

```
+--------------------------------------------------+
|  EXPORT TO ATF                                    |
+--------------------------------------------------+
|                                                   |
|  Export ready for P123456 (YBC 4644)              |
|                                                   |
|  +--------------------------------------------+   |
|  | &P123456 = YBC 4644                        |   |
|  | #atf: lang akk                             |   |
|  | #project: glintstone                       |   |
|  |                                            |   |
|  | # Source: Glintstone Platform              |   |
|  | # CDLI: https://cdli.earth/P123456         |   |
|  | # Status: Draft (expert review pending)    |   |
|  | # Generated: 2026-01-03                    |   |
|  | # Contributors: 12 volunteers, 1 expert    |   |
|  |                                            |   |
|  | @tablet                                    |   |
|  | @obverse                                   |   |
|  | 1. a-na {d}utu be-li2-ia                   |   |
|  | 2. um-ma {m}a-bi-e-szar2-rum               |   |
|  | 3. ar-du-ka-a-ma                           |   |
|  | @reverse                                   |   |
|  | 1. u2-ul i-ba-asz-szi                      |   |
|  | ...                                        |   |
|  +--------------------------------------------+   |
|                                                   |
|  [Copy to Clipboard] [Download .atf]              |
|                                                   |
|  This export is compatible with:                  |
|  - ORACC project submission                       |
|  - Standard ATF editors                           |
|  - Scholarly publication                          |
|                                                   |
+--------------------------------------------------+
```

**ATF Export Features:**
- Valid ATF format
- CDLI P-number as identifier
- Project tag for Glintstone
- Source attribution comment block
- Status indicator (Draft/Provisional/Accepted)
- Contributor acknowledgment
- Timestamp

**Acceptance Criteria:**
- [ ] ATF export is syntactically valid
- [ ] P-number correctly formatted in header
- [ ] Attribution block includes all sources
- [ ] Copy to clipboard functional
- [ ] Download generates .atf file
- [ ] Compatibility notes visible

---

### Stage 5: Bidirectional Value Proposition

**User Goal:** Understand mutual benefit of integration

**System Response:**
- Value proposition for CDLI
- Value proposition for scholars
- Partnership messaging

**Value Exchange Display:**

```
+--------------------------------------------------+
|  BIDIRECTIONAL VALUE                              |
+--------------------------------------------------+
|                                                   |
|  What CDLI provides Glintstone:                   |
|  +--------------------------------------------+   |
|  | - Authoritative catalog metadata           |   |
|  | - P-number linking for all tablets         |   |
|  | - High-resolution images (when available)  |   |
|  | - Scholarly legitimacy and trust           |   |
|  +--------------------------------------------+   |
|                                                   |
|  What Glintstone provides CDLI:                   |
|  +--------------------------------------------+   |
|  | - Accelerated transcription production     |   |
|  | - AI-assisted draft generation             |   |
|  | - Crowdsourced verification                |   |
|  | - ATF-compatible exports for integration   |   |
|  | - Community engagement and awareness       |   |
|  +--------------------------------------------+   |
|                                                   |
|  Together, we can tackle the backlog faster.      |
|                                                   |
+--------------------------------------------------+
```

**Key Talking Points:**

| For CDLI | Benefit |
|----------|---------|
| Transcription acceleration | More tablets get text faster |
| Community engagement | New volunteers enter the field |
| Quality assurance | Expert review maintains standards |
| Familiar formats | ATF exports integrate seamlessly |

| For Scholars | Benefit |
|--------------|---------|
| Head start | AI + crowd drafts save time |
| Flexible workflow | Review when convenient |
| Full attribution | Your name on your work |
| Standards compliance | CDLI linking, ATF export |

**Acceptance Criteria:**
- [ ] Bidirectional value clearly articulated
- [ ] No claims of replacing CDLI
- [ ] Partnership framing, not competition
- [ ] Specific, concrete benefits listed

---

### Stage 6: Contact and Partnership

**User Goal:** Explore partnership or integration discussions

**System Response:**
- Partnership contact form
- Technical integration resources
- Next steps

**Partnership CTA:**

```
+--------------------------------------------------+
|  INTERESTED IN INTEGRATION?                       |
+--------------------------------------------------+
|                                                   |
|  For CDLI/ORACC integration discussions:          |
|                                                   |
|  [Contact our integration team]                   |
|                                                   |
|  Technical resources:                             |
|  - API documentation (coming soon)                |
|  - Data format specifications                     |
|  - Integration guidelines                         |
|                                                   |
|  For academic partnership inquiries:              |
|  - Pilot program participation                    |
|  - Corpus-specific projects                       |
|  - Research collaboration                         |
|                                                   |
|  [Express partnership interest]                   |
|                                                   |
+--------------------------------------------------+
```

**For Release 1:** Forms can submit to email or log locally. No backend required.

**Acceptance Criteria:**
- [ ] Clear contact path for integration discussions
- [ ] Mention of future API documentation
- [ ] Partnership interest form available
- [ ] Professional, scholarly tone

---

## Component Dependencies

| Component | Source PRD | Usage in J5 |
|-----------|------------|-------------|
| Design Tokens | L1 | All styling |
| TabletViewer | L3 | Tablet display in lookup |
| TranscriptionLine | L3 | Transcription preview |
| StatusBadge | L3 | Status indicators |
| Dummy Tablets | L2 | Demo data with P-numbers |

---

## Data Requirements

**Demo Tablets for Integration (3-5 tablets):**

| Tablet | P-number | Real/Fictional | Purpose |
|--------|----------|----------------|---------|
| YBC 4644 | P123456 | Fictional | Primary demo tablet |
| BM 106056 | P789012 | Fictional | Secondary demo |
| CBS 10467 | Real P-number | Real | Test actual CDLI link |

**For the real P-number tablet:**
- Use a well-known, publicly accessible CDLI entry
- Ensure "View in CDLI" link actually works
- Verify metadata matches real CDLI record

---

## Technical Notes

**P-number Validation:**
- Format: P + 6 digits (e.g., P123456)
- Validate on input
- Provide helpful error for malformed input

**CDLI Link Generation:**
- Format: `https://cdli.earth/P{number}`
- Opens in new tab
- Gracefully handle if CDLI page doesn't exist

**ATF Export:**
- Generate valid ATF structure
- Include all metadata comments
- Ensure proper line encoding

---

## Out of Scope

- Live API integration with CDLI
- Real-time data sync
- Bulk import from CDLI
- ORACC submission workflow
- Image import from CDLI

---

## Testing Requirements

**Functional:**
- [ ] P-number lookup returns correct demo data
- [ ] Invalid P-number shows appropriate error
- [ ] "View in CDLI" link works for real P-numbers
- [ ] ATF export is valid format
- [ ] Copy to clipboard works

**Content:**
- [ ] ATF format is syntactically correct
- [ ] Terminology is accurate
- [ ] No misleading claims about integration status

**User Experience:**
- [ ] Integration concept is clear
- [ ] Data sources are clearly distinguished
- [ ] Partnership pathway is accessible

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
