# J1: Marketing Page Journey

**Document Type:** Journey PRD
**Priority:** P0 (Critical Path)
**Status:** Ready
**Estimated Complexity:** M
**Dependencies:** L1 (Design System), L2 (Dummy Data - for statistics), L3 (TabletViewer - for hero)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| User Type | All (entry point for all audiences) |
| Journey Scope | First Page Load -> CTA Click |
| UX Strategy Reference | Section 1.1: Progressive Disclosure (Level 0: Surface); Section 2.2: Critical Path W-P1 |
| Brief Reference | "All releases should be coupled with a single-page marketing site" |

---

## Journey Narrative

A visitor arrives at glintstone.io, curious about what they have heard or seen about this new way to help decode ancient tablets. Within 10 seconds, they understand what Glintstone does and why it matters. Within 30 seconds, they see evidence that this is real and credible. Within 60 seconds, they decide whether to try contributing - and if they click "Try it now," they should feel zero friction entering the experience.

The marketing page must serve two distinct audiences with different needs:
- **Academics:** Seek credibility, integration with existing workflows, scholarly rigor
- **Hobbyists:** Seek accessibility, immediate gratification, meaningful contribution

The page accomplishes this through careful information hierarchy and strategic CTA placement.

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Experience | Time to understand value proposition | < 10 seconds |
| Behavior | Primary CTA click rate | > 15% of visitors |
| Behavior | Scroll depth | > 60% reach "How It Works" |
| Outcome | Transition to first task (J2) | > 10% of visitors |

---

## Journey Map

### Stage 1: First Impression (0-3 seconds)

**User Goal:** Instantly understand "what is this?"

**System Response:**
- Hero section with dramatic tablet imagery
- Clear headline communicating core value
- Immediate visual identity (Stargazer's Script brand)

**Design Specification:**

```
+--------------------------------------------------+
|  [Logo: Glintstone]              [Try it now]    |
+--------------------------------------------------+
|                                                   |
|        +---------------------------+              |
|        |                           |              |
|        |   [Dramatic tablet image  |              |
|        |    with subtle glow,      |              |
|        |    constellation lines]   |              |
|        |                           |              |
|        +---------------------------+              |
|                                                   |
|   WRITTEN IN THE STARS.                           |
|   WAITING TO BE READ.                             |
|                                                   |
|   Help unlock humanity's oldest stories.          |
|   No experience needed.                           |
|                                                   |
|         [Try it now - 2 minutes]                  |
|                                                   |
|   Scroll to learn more                     [v]    |
|                                                   |
+--------------------------------------------------+
```

**Content Requirements:**

| Element | Specification |
|---------|---------------|
| Headline | "Written in the Stars. Waiting to Be Read." |
| Subhead | "Help unlock humanity's oldest stories. No experience needed." |
| Primary CTA | "Try it now - 2 minutes" (gold button, tactile style) |
| Hero Image | Featured tablet with constellation-style overlay |

**Acceptance Criteria:**
- [ ] Hero section loads in < 1 second
- [ ] Headline visible above fold on all devices
- [ ] Primary CTA visible without scroll on desktop
- [ ] Tablet image has subtle animation (glow, particles)
- [ ] No account prompt at this stage
- [ ] Scroll indicator visible on desktop

---

### Stage 2: Social Proof (3-10 seconds)

**User Goal:** Verify this is real and credible

**System Response:**
- Real-time contribution counter (animated)
- Institutional partnerships/endorsements
- Brief "what is cuneiform" context

**Design Specification:**

```
+--------------------------------------------------+
|                                                   |
|   +----------+  +----------+  +----------+        |
|   |  1.2M    |  |   4,700  |  |    85%   |        |
|   | tablets  |  |  contrib-|  | remain   |        |
|   | exist    |  |  utors   |  | unread   |        |
|   +----------+  +----------+  +----------+        |
|                                                   |
|   "This is the largest untapped archive of        |
|    human knowledge on Earth."                     |
|                                                   |
|   Trusted by:                                     |
|   [Yale] [CDLI] [Penn Museum] [Oxford]            |
|                                                   |
+--------------------------------------------------+
```

**Statistics to Display:**

| Stat | Value | Context |
|------|-------|---------|
| Tablets exist | "1.2M+" | "cuneiform tablets excavated" |
| Still unread | "85%" | "waiting to be translated" |
| Contributors | "4,700+" | "volunteers and scholars" (dummy for demo) |
| Tablets processed | "12,400+" | "transcriptions in progress" (dummy) |

**Acceptance Criteria:**
- [ ] Stats animate on scroll into view
- [ ] Contribution counter shows recent activity (simulated for demo)
- [ ] Partner logos visible (use placeholder if needed)
- [ ] Stats are visually impactful (large numbers, icons)

---

### Stage 3: Value Proposition (10-30 seconds)

**User Goal:** Understand what they would actually do

**System Response:**
- Clear explanation of the contribution model
- Differentiated messaging for academics vs. hobbyists
- Visual preview of the task interface

**Design Specification:**

```
+--------------------------------------------------+
|                                                   |
|   HOW YOU CAN HELP                                |
|                                                   |
|   +----------------------+  +-------------------+ |
|   | [Icon: Clock]        |  | [Icon: Graduate]  | |
|   |                      |  |                   | |
|   | Got 2 minutes?       |  | Want to go deeper?| |
|   |                      |  |                   | |
|   | Match ancient signs  |  | Learn to read     | |
|   | No expertise needed. |  | cuneiform and     | |
|   | Your input trains    |  | contribute full   | |
|   | our AI and helps     |  | transcriptions.   | |
|   | experts focus.       |  |                   | |
|   |                      |  |                   | |
|   | [Try quick tasks]    |  | [Start learning]  | |
|   +----------------------+  +-------------------+ |
|                                                   |
+--------------------------------------------------+
```

**Dual-Path Messaging:**

| Audience | Headline | Value Prop | CTA |
|----------|----------|------------|-----|
| Hobbyist | "Got 2 minutes?" | Match signs, train AI, help experts | "Try quick tasks" |
| Learner | "Want to go deeper?" | Learn cuneiform, real contributions | "Start learning" |
| Academic | "Already an expert?" | Review, approve, publish faster | "Access review tools" |

**Acceptance Criteria:**
- [ ] Three contribution paths clearly presented
- [ ] Each path has distinct CTA
- [ ] Visual preview of task interface (screenshot or animation)
- [ ] No jargon in hobbyist messaging
- [ ] Academic path mentions CDLI/ORACC integration

---

### Stage 4: How It Works (30-60 seconds)

**User Goal:** Understand the process and trust the system

**System Response:**
- Step-by-step contribution flow
- Trust indicators (expert review, quality assurance)
- Attribution and credit explanation

**Design Specification:**

```
+--------------------------------------------------+
|                                                   |
|   HOW IT WORKS                                    |
|                                                   |
|   1. CONTRIBUTE                                   |
|   [Icon: Hand + Tablet]                           |
|   Complete simple visual tasks or                 |
|   transcribe text with AI assistance.             |
|                                                   |
|   2. VERIFY                                       |
|   [Icon: Checkmarks]                              |
|   Your work is compared with other                |
|   contributors and AI suggestions.                |
|                                                   |
|   3. EXPERT REVIEW                                |
|   [Icon: Mortarboard]                             |
|   Professional Assyriologists verify              |
|   and approve final translations.                 |
|                                                   |
|   4. PUBLISH                                      |
|   [Icon: Book/CDLI logo]                          |
|   Approved translations are published             |
|   to the scholarly record. You're credited.       |
|                                                   |
+--------------------------------------------------+
```

**Trust Messaging:**
- "Every contribution is validated"
- "Expert review ensures accuracy"
- "You're always credited for your work"
- "Nothing is published without verification"

**Acceptance Criteria:**
- [ ] 4-step process clearly visualized
- [ ] Trust messaging addresses academic concerns
- [ ] Expert review step is prominent
- [ ] Attribution promise is explicit

---

### Stage 5: Credibility and Depth (60+ seconds)

**User Goal:** (For academics) Verify scholarly legitimacy

**System Response:**
- Integration details (CDLI, ORACC, ATF format)
- Academic advisor board
- Scholarly methodology explanation

**Design Specification:**

```
+--------------------------------------------------+
|                                                   |
|   BUILT FOR SCHOLARS                              |
|                                                   |
|   Glintstone integrates with the tools you        |
|   already use:                                    |
|                                                   |
|   [CDLI Logo] P-number linking and metadata sync  |
|   [ORACC Logo] ATF format export for publications |
|   [ePSD Logo] Dictionary lookup and lemmatization |
|                                                   |
|   ---                                             |
|                                                   |
|   ADVISORY BOARD                                  |
|                                                   |
|   [Photo] Dr. Name, Institution                   |
|   [Photo] Dr. Name, Institution                   |
|   [Photo] Dr. Name, Institution                   |
|                                                   |
+--------------------------------------------------+
```

**Academic Features to Highlight:**
- P-number integration with CDLI
- ATF format for data export
- Expert review workflow
- Attribution and citation support
- Advisory board (placeholder for demo)

**Acceptance Criteria:**
- [ ] CDLI/ORACC integration prominently featured
- [ ] Advisory board section (placeholder names acceptable for demo)
- [ ] Technical integration details accessible but not overwhelming
- [ ] Link to detailed methodology (can be placeholder)

---

### Stage 6: Final CTA (Bottom of page)

**User Goal:** Take action or get more information

**System Response:**
- Repeated primary CTA
- Secondary options (newsletter, contact)
- Footer with links

**Design Specification:**

```
+--------------------------------------------------+
|                                                   |
|   +------------------------------------------+    |
|   |                                          |    |
|   |   READY TO MAKE HISTORY?                 |    |
|   |                                          |    |
|   |   [Try it now - No account needed]       |    |
|   |                                          |    |
|   +------------------------------------------+    |
|                                                   |
+--------------------------------------------------+
|  [Logo]                                           |
|                                                   |
|  About | For Scholars | For Volunteers | Contact  |
|                                                   |
|  Newsletter: [email] [Subscribe]                  |
|                                                   |
|  (c) 2026 Glintstone. Built to unlock the past.   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] Primary CTA repeated at bottom
- [ ] "No account needed" messaging included
- [ ] Newsletter signup (can be non-functional for demo)
- [ ] Footer links present (can be placeholder pages)

---

## Shared Components Required

| Component | Source PRD | Usage |
|-----------|------------|-------|
| TabletViewer | L3 | Hero section interactive element (optional) |
| Design Tokens | L1 | All styling |
| Dummy Statistics | L2 | Contribution counter, stats |

---

## Edge Cases and Error States

| Scenario | Expected Behavior |
|----------|-------------------|
| Slow image load | Skeleton placeholder with pulse animation |
| CTA click | Immediate transition to J2 (no loading delay) |
| Mobile view | Hero image scales, stats stack vertically |
| Very wide screen | Content max-width 1200px, centered |
| JavaScript disabled | Static version still readable |

---

## Technical Requirements

**Performance:**
- Lighthouse score > 90
- First Contentful Paint < 1.5s
- Largest Contentful Paint < 2.5s
- Cumulative Layout Shift < 0.1

**Responsiveness:**
- Mobile: 320px - 767px
- Tablet: 768px - 1023px
- Desktop: 1024px+

**SEO:**
- Semantic HTML (h1, h2, proper heading hierarchy)
- Meta description and Open Graph tags
- Structured data for organization

**Analytics Hooks (for future):**
- Track scroll depth
- Track CTA clicks
- Track time on page
- Track which section visible at CTA click

---

## Content Specifications

**Hero Headline Options (A/B test ready):**
1. "Written in the Stars. Waiting to Be Read."
2. "Help Decode Humanity's Oldest Stories."
3. "Ancient Words. Modern Volunteers. Real Discoveries."

**Subhead:**
- "Help unlock humanity's oldest stories. No experience needed."

**CTA Text Options:**
1. "Try it now - 2 minutes"
2. "Start contributing"
3. "Begin your first task"

**Key Messaging Points:**
- 1.2M tablets exist, 85% unread (the scale of the problem)
- No expertise needed for basic tasks (accessibility)
- Expert review ensures quality (trust)
- Your work is credited (recognition)
- Integrates with CDLI/ORACC (scholarly legitimacy)

---

## Design Notes

**Stargazer's Script Application:**
- Dark navy background (Celestial Navy #0D1B2A)
- Gold accents for CTAs (Celestial Gold #FFD166)
- Violet for AI/innovation mentions (Nebula Violet #7B68EE)
- Starlight text (#F0F4F8)
- Subtle star particle animation in hero (performance-optimized)

**Tablet Hero Treatment:**
- Use featured tablet from L2 fixtures
- Apply constellation-style overlay connecting signs
- Subtle glow effect behind tablet
- Optional: gentle float animation

**Clay Texture Application:**
- CTAs use tactile button style from L1
- Cards have subtle texture overlay
- Balance texture with readability

---

## Out of Scope

- User authentication (handled in J2 optionally)
- Full "About" page content
- Blog or news section
- Pricing or subscription information
- Mobile app download links

---

## Dependencies

| Dependency | Required For | Blocking |
|------------|--------------|----------|
| L1: Design System | All styling | Yes |
| L2: Dummy Data | Statistics display | Partial (can hardcode) |
| L3: TabletViewer | Hero section (optional) | No |
| J2: Passerby Journey | CTA destination | Yes (for full demo) |

---

## Testing Requirements

**Functional:**
- [ ] All CTAs link to correct destinations
- [ ] Stats animate on scroll
- [ ] Page renders correctly on Chrome, Safari, Firefox
- [ ] Mobile layout works at 320px width

**Visual:**
- [ ] Matches Stargazer's Script brand
- [ ] Typography hierarchy is clear
- [ ] Contrast passes WCAG AA

**Performance:**
- [ ] Lighthouse > 90
- [ ] Images optimized
- [ ] Fonts loaded efficiently

**Content:**
- [ ] No placeholder text in final
- [ ] Stats are realistic (even if dummy)
- [ ] All copy reviewed for tone

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
