# J1: Marketing Page Screenflow

**Journey:** Marketing Page
**User Type:** All visitors (entry point)
**Priority:** P0 (Critical Path)
**PRD Reference:** J1-marketing-page.md

---

## Journey Overview

```
[Landing/Hero] --> [Social Proof] --> [How You Help] --> [How It Works]
      |                                     |
      v                                     v
[Try it now] -----------------------> [J2: Passerby Flow]
      |
      v
[Scroll to] --> [For Scholars] --> [Final CTA] --> [J2 or J3 or J4]
```

**Goal:** Convert visitors to contributors within one page scroll.

**Success Metrics:**
- Primary CTA click rate: > 15%
- Scroll depth: > 60% reach "How It Works"
- Transition to first task: > 10% of visitors

---

## Screen 1: Hero Section

### Entry Points
- Direct URL (glintstone.io)
- Search engine
- Social media link
- Academic referral

### User Goal
Understand what Glintstone is within 10 seconds.

### Wireframe

```
+------------------------------------------------------------------+
| [Header: marketing variant]                                       |
| [Logo: Glintstone]                              [Try it now]      |
+------------------------------------------------------------------+
|                                                                   |
|                                                                   |
|          +--------------------------------+                       |
|          |                                |                       |
|          |     [TabletViewer: hero]       |                       |
|          |     (Dramatic tablet image     |                       |
|          |      with constellation        |                       |
|          |      overlay animation)        |                       |
|          |                                |                       |
|          +--------------------------------+                       |
|                                                                   |
|                                                                   |
|              WRITTEN IN THE STARS.                                |
|              WAITING TO BE READ.                                  |
|                                                                   |
|              Help unlock humanity's oldest stories.               |
|              No experience needed.                                |
|                                                                   |
|                                                                   |
|                   [Button: primary, lg]                           |
|                   [Try it now - 2 minutes]                        |
|                                                                   |
|                                                                   |
|              Scroll to learn more                                 |
|                     [v]                                           |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Header | navigation.md | variant="marketing" |
| Button | forms.md | variant="primary", size="lg" |
| TabletViewer | tablet.md | variant="hero", readonly |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| "Try it now" (header) | Click | Navigate to J2 Screen 1 |
| "Try it now" (hero) | Click | Navigate to J2 Screen 1 |
| Scroll indicator | Click | Smooth scroll to Screen 2 |
| Tablet image | None | Decorative animation only |

### States

**Loading:**
- Skeleton placeholder for tablet image
- Text content loads immediately (static HTML)

**Loaded:**
- Tablet image fades in
- Constellation animation starts
- Hero fully interactive

### Accessibility Notes

- Headline is `<h1>`
- Tablet image has alt text describing the artifact
- Animation respects prefers-reduced-motion
- CTA is keyboard focusable
- Skip link available in header

---

## Screen 2: Social Proof Section

### Entry Points
- Scroll from Hero
- Direct scroll/anchor link

### User Goal
Verify this is real and credible.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|   +------------------+  +------------------+  +------------------+ |
|   |                  |  |                  |  |                  | |
|   |  [StatCard]      |  |  [StatCard]      |  |  [StatCard]      | |
|   |                  |  |                  |  |                  | |
|   |      1.2M+       |  |      4,700+      |  |       85%        | |
|   |     tablets      |  |   contributors   |  |    still unread  | |
|   |      exist       |  |    worldwide     |  |                  | |
|   |                  |  |                  |  |                  | |
|   +------------------+  +------------------+  +------------------+ |
|                                                                   |
|                                                                   |
|   "This is the largest untapped archive of human knowledge        |
|    on Earth. These tablets hold 3,000 years of stories,           |
|    laws, letters, and recipes - waiting to be read."              |
|                                                                   |
|                                                                   |
|   Trusted by:                                                     |
|                                                                   |
|   [InstitutionBadge] [InstitutionBadge] [InstitutionBadge]        |
|       Yale               CDLI            Penn Museum              |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| StatCard | progress.md | variant="lg" |
| Grid | layout.md | columns="3" |
| InstitutionBadge | trust.md | variant="logo-only" |
| Cluster | layout.md | align="center" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Stats | Scroll into view | Animate count-up |
| Institution logos | Click | Open institution site (new tab) |

### Animation

Stats animate on scroll into view:
1. Numbers count up from 0 (duration: 1.5s)
2. Staggered start (100ms between each)
3. Easing: ease-out

### Accessibility Notes

- Stats have proper labels (not just numbers)
- Institution links indicate external destination
- Animation respects prefers-reduced-motion

---

## Screen 3: How You Can Help

### Entry Points
- Scroll from Social Proof

### User Goal
Understand what they would actually do.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|                      HOW YOU CAN HELP                             |
|                                                                   |
|   +-----------------------------+  +-----------------------------+|
|   |                             |  |                             ||
|   |  [Icon: Clock]              |  |  [Icon: Graduate]           ||
|   |                             |  |                             ||
|   |  Got 2 minutes?             |  |  Want to go deeper?         ||
|   |                             |  |                             ||
|   |  Match ancient signs with   |  |  Learn to read cuneiform    ||
|   |  modern references. No      |  |  and contribute full        ||
|   |  expertise needed. Your     |  |  transcriptions with AI     ||
|   |  input trains our AI and    |  |  assistance.                ||
|   |  helps experts focus.       |  |                             ||
|   |                             |  |                             ||
|   |  [Button: Try quick tasks]  |  |  [Button: Start learning]   ||
|   |                             |  |                             ||
|   +-----------------------------+  +-----------------------------+|
|                                                                   |
|   +-------------------------------------------------------------+|
|   |                                                             ||
|   |  [Icon: Expert Badge]                                       ||
|   |                                                             ||
|   |  Already an expert?                                         ||
|   |                                                             ||
|   |  Accelerate your review workflow. Approve AI-assisted       ||
|   |  drafts, export to ATF, and publish faster.                 ||
|   |                                                             ||
|   |  [Button: Access review tools]                              ||
|   |                                                             ||
|   +-------------------------------------------------------------+|
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Grid | layout.md | columns="2" (top), columns="1" (bottom) |
| Stack | layout.md | space="md" |
| Button | forms.md | variant="secondary" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| "Try quick tasks" | Click | Navigate to J2 Screen 1 |
| "Start learning" | Click | Navigate to J3 Screen 1 |
| "Access review tools" | Click | Navigate to J4 Screen 1 |

### Accessibility Notes

- Section has heading for navigation
- Three distinct paths clearly differentiated
- All buttons are keyboard accessible
- No jargon in hobbyist path

---

## Screen 4: How It Works

### Entry Points
- Scroll from How You Can Help

### User Goal
Understand the process and trust the system.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|                       HOW IT WORKS                                |
|                                                                   |
|   +-------------+  +-------------+  +-------------+  +-------------+
|   |             |  |             |  |             |  |             |
|   | [Icon]      |  | [Icon]      |  | [Icon]      |  | [Icon]      |
|   |  1          |  |  2          |  |  3          |  |  4          |
|   |             |  |             |  |             |  |             |
|   | CONTRIBUTE  |  | VERIFY      |  | REVIEW      |  | PUBLISH     |
|   |             |  |             |  |             |  |             |
|   | Complete    |  | Your work   |  | Expert      |  | Verified    |
|   | simple      |  | is compared |  | Assyrio-    |  | translations|
|   | visual      |  | with other  |  | logists     |  | are         |
|   | tasks or    |  | contributors|  | verify and  |  | published.  |
|   | transcribe  |  | and AI      |  | approve     |  | You're      |
|   | with AI     |  | suggestions.|  | final work. |  | credited.   |
|   | help.       |  |             |  |             |  |             |
|   +-------------+  +-------------+  +-------------+  +-------------+
|                                                                   |
|   +-------------------------------------------------------------+|
|   |                                                             ||
|   |  "Every contribution is validated. Expert review ensures    ||
|   |   accuracy. You're always credited for your work.           ||
|   |   Nothing is published without verification."               ||
|   |                                                             ||
|   +-------------------------------------------------------------+|
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Grid | layout.md | columns="4" (desktop), "2" (tablet), "1" (mobile) |
| Stack | layout.md | space="sm" |

### Interactions

None - informational content only.

### Accessibility Notes

- Steps are numbered for clarity
- Each step is a discrete article
- Trust messaging is emphasized
- No interaction needed

---

## Screen 5: For Scholars (Below Fold)

### Entry Points
- Scroll from How It Works
- Header "For Scholars" link

### User Goal
(For academics) Verify scholarly legitimacy.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|                     BUILT FOR SCHOLARS                            |
|                                                                   |
|   Glintstone integrates with the tools you already use:          |
|                                                                   |
|   +------------------+  +------------------+  +------------------+ |
|   |                  |  |                  |  |                  | |
|   | [InstitutionBadge]| | [InstitutionBadge]| | [InstitutionBadge]| |
|   |      CDLI        |  |      ORACC       |  |      ePSD        | |
|   |                  |  |                  |  |                  | |
|   | P-number linking |  | ATF format       |  | Dictionary       | |
|   | and metadata     |  | export for       |  | lookup and       | |
|   | sync             |  | publications     |  | lemmatization    | |
|   |                  |  |                  |  |                  | |
|   +------------------+  +------------------+  +------------------+ |
|                                                                   |
|   ---------------------------------------------------------------  |
|                                                                   |
|                      ADVISORY BOARD                               |
|                                                                   |
|   +----------------+  +----------------+  +----------------+       |
|   | [ExpertCard]   |  | [ExpertCard]   |  | [ExpertCard]   |       |
|   |                |  |                |  |                |       |
|   | Dr. Name       |  | Dr. Name       |  | Dr. Name       |       |
|   | Institution    |  | Institution    |  | Institution    |       |
|   +----------------+  +----------------+  +----------------+       |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| InstitutionBadge | trust.md | variant="default", linked |
| ExpertCard | trust.md | variant="compact" |
| Grid | layout.md | columns="3" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| CDLI badge | Click | Open cdli.ucla.edu (new tab) |
| ORACC badge | Click | Open oracc.org (new tab) |
| Expert card | Click | (Future: expert profile page) |

### Accessibility Notes

- External links indicate destination
- Advisory board uses proper headings
- Integration details expandable for detail

---

## Screen 6: Final CTA

### Entry Points
- Scroll from For Scholars (bottom of page)

### User Goal
Take action or get more information.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|   +-------------------------------------------------------------+|
|   |                                                             ||
|   |               READY TO MAKE HISTORY?                        ||
|   |                                                             ||
|   |               [Button: primary, lg]                         ||
|   |               [Try it now - No account needed]              ||
|   |                                                             ||
|   +-------------------------------------------------------------+|
|                                                                   |
+------------------------------------------------------------------+
|  [Footer]                                                         |
|                                                                   |
|  [Logo: Glintstone]                                               |
|                                                                   |
|  About | For Scholars | For Volunteers | Contact                  |
|                                                                   |
|  Newsletter:                                                      |
|  [EmailInput]                          [Button: Subscribe]        |
|                                                                   |
|  (c) 2026 Glintstone. Built to unlock the past.                   |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Button | forms.md | variant="primary", size="lg" |
| EmailInput | forms.md | - |
| Cluster | layout.md | - |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| "Try it now" | Click | Navigate to J2 Screen 1 |
| Footer links | Click | Navigate to respective pages |
| Newsletter submit | Click | Record email (localStorage for demo) |

### Footer Links (Release 1)

| Link | Destination | Status |
|------|-------------|--------|
| About | /about | Placeholder page |
| For Scholars | #for-scholars | Anchor link |
| For Volunteers | #how-you-help | Anchor link |
| Contact | mailto: or form | Email or placeholder |

---

## Transition: Marketing to Passerby Flow

### Trigger
User clicks any "Try it now" CTA.

### Transition Animation
1. Current page fades slightly (100ms)
2. Loading indicator (if needed)
3. J2 Screen 1 slides in from right (200ms)

### Data Passed
- Source CTA (for analytics)
- No authentication required

### Entry State for J2
- Fresh session (no localStorage)
- Or resume prompt if returning user

---

## Responsive Behavior

### Mobile (< 768px)

**Hero:**
- Tablet image smaller, centered
- Headline stacks
- Single CTA button

**Stats:**
- Vertical stack (not grid)
- Full-width cards

**How You Help:**
- Single column, stacked cards
- Each path on separate "screen"

**For Scholars:**
- Condensed, below fold
- Advisory board horizontal scroll

### Tablet (768-1023px)

**Stats:**
- 3-column grid maintained

**How You Help:**
- 2x2 grid

### Desktop (>= 1024px)

Full layout as wireframed.

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| Cumulative Layout Shift | < 0.1 |
| Hero CTA visible | Without scroll |
| Tablet image load | < 2s |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial screenflow |
