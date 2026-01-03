# Trust and Authority Components

**Component Category:** Core
**Document Version:** 1.0

Trust components visualize the Contextual Authority Model defined in the UX Strategy. These components make the provenance, verification status, and credibility of content immediately apparent.

**Design Principles:**
- Authority is always visible (never hidden)
- Color is never the sole indicator
- Status transitions are visible and explained
- Attribution is prominent and traceable
- Uncertainty is shown, not hidden

---

## StatusBadge

### Purpose and Use Cases

StatusBadge displays the verification status of content per the Contextual Authority Model. Use for:
- Transcription line status
- Sign reading status
- Translation status
- Overall tablet status

### Anatomy

```
[Icon] [Label]
```

### HTML Structure

```html
<!-- Compact (icon only) -->
<span
  class="status-badge"
  data-status="proposed"
  data-variant="compact"
  aria-label="Status: Proposed - awaiting validation"
>
  <svg aria-hidden="true"><!-- question mark icon --></svg>
</span>

<!-- Default (icon + label) -->
<span class="status-badge" data-status="accepted">
  <svg aria-hidden="true"><!-- double checkmark icon --></svg>
  <span class="status-badge__label">Accepted</span>
</span>

<!-- Interactive (shows detail on click) -->
<button
  class="status-badge"
  data-status="under-review"
  data-interactive="true"
  aria-expanded="false"
  aria-haspopup="dialog"
>
  <svg aria-hidden="true"><!-- clock icon --></svg>
  <span class="status-badge__label">Under Review</span>
</button>
```

### Status Types

| Status | Icon | Border Style | Meaning |
|--------|------|--------------|---------|
| proposed | ? Question | Dashed | AI-generated or single contributor, awaiting validation |
| under-review | Clock | Solid | Multiple contributors, awaiting expert review |
| provisionally-accepted | Single Check | Solid | One expert approval, awaiting second reviewer |
| accepted | Double Check/Shield | Bold solid | Multiple expert approval, canonical |
| disputed | Split/Debate | Split pattern | Experts disagree, multiple interpretations |
| superseded | Strikethrough | Faded | Previously accepted, now revised |

### Variants

| Variant | Display | Use Case |
|---------|---------|----------|
| compact | Icon only | Inline, tables |
| default | Icon + label | Standard |
| pill | Full pill shape | Emphasis |
| interactive | Clickable | Shows detail popover |

### States

| State | Description |
|-------|-------------|
| default | Static display |
| hover | Slight emphasis (if interactive) |
| focus | Focus ring |
| expanded | Detail popover open |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-status | string | Status type |
| data-variant | string | Display variant |
| data-interactive | boolean | Shows detail on click |
| data-show-label | boolean | Display text label |

### Accessibility

- Icon alone is never sufficient - aria-label required for compact
- Colorblind accessible - icons and patterns differentiate status
- Interactive badges are buttons with proper ARIA
- Tooltip provides full explanation on hover/focus

### Detail Popover Content

When interactive, clicking shows:
```
+--------------------------------+
| Status: Under Review           |
|                                |
| This reading is being reviewed |
| by experts before approval.    |
|                                |
| Contributors: 8                |
| Expert reviews: 0              |
|                                |
| [View history]                 |
+--------------------------------+
```

---

## TrustIndicator

### Purpose and Use Cases

TrustIndicator aggregates multiple trust signals into a single visual. Use for:
- Tablet overall trust level
- Expert profile verification
- Source credibility

### Anatomy

```
+----------------------------+
| [Shield Icon]              |
| Verified Source            |
|                            |
| - Expert reviewed          |
| - CDLI verified            |
| - 15 contributors          |
+----------------------------+
```

### HTML Structure

```html
<div class="trust-indicator" data-level="high">
  <div class="trust-indicator__header">
    <svg class="trust-indicator__icon" aria-hidden="true">
      <!-- Shield icon -->
    </svg>
    <span class="trust-indicator__level">Verified Source</span>
  </div>

  <ul class="trust-indicator__signals">
    <li class="trust-signal" data-type="expert">
      <svg aria-hidden="true"><!-- check icon --></svg>
      Expert reviewed
    </li>
    <li class="trust-signal" data-type="institution">
      <svg aria-hidden="true"><!-- check icon --></svg>
      CDLI verified
    </li>
    <li class="trust-signal" data-type="crowd">
      <svg aria-hidden="true"><!-- people icon --></svg>
      15 contributors
    </li>
  </ul>
</div>
```

### Trust Levels

| Level | Icon | Description |
|-------|------|-------------|
| low | Open shield | Minimal verification |
| medium | Half shield | Some verification |
| high | Full shield | Well verified |
| verified | Shield + check | Fully verified |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-level | string | Trust level |
| data-signals | string | JSON signal array |
| data-collapsed | boolean | Show summary only |

### Accessibility

- List semantics for signals
- Expandable/collapsible with keyboard
- Clear level announced to screen readers

---

## ExpertCard

### Purpose and Use Cases

ExpertCard displays an expert's profile and credentials. Use for:
- Reviewer attribution
- Advisory board display
- Expert endorsements
- Dispute participants

### Anatomy

```
+----------------------------+
| +------+                   |
| | Photo|  Dr. Jane Smith   |
| |      |  Yale University  |
| +------+                   |
|                            |
| Specialization:            |
| Old Babylonian, Sippar     |
|                            |
| Reviews: 1,247             |
| [View profile]             |
+----------------------------+
```

### HTML Structure

```html
<article class="expert-card" data-expert-id="expert-123">
  <header class="expert-card__header">
    <figure class="expert-card__avatar">
      <img
        src="expert-photo.jpg"
        alt=""
        class="expert-card__photo"
      >
      <!-- Fallback initials if no photo -->
      <span class="expert-card__initials" aria-hidden="true">JS</span>
    </figure>

    <div class="expert-card__identity">
      <h3 class="expert-card__name">Dr. Jane Smith</h3>
      <p class="expert-card__institution">Yale University</p>
    </div>

    <span class="expert-card__verified" aria-label="Verified expert">
      <svg aria-hidden="true"><!-- verified badge --></svg>
    </span>
  </header>

  <div class="expert-card__details">
    <dl class="expert-card__metadata">
      <dt>Specialization</dt>
      <dd>Old Babylonian, Sippar corpus</dd>

      <dt>Reviews</dt>
      <dd>1,247 approved</dd>
    </dl>
  </div>

  <footer class="expert-card__actions">
    <a href="/experts/expert-123" class="button" data-variant="ghost">
      View profile
    </a>
  </footer>
</article>
```

### Variants

| Variant | Size | Content |
|---------|------|---------|
| compact | Small | Photo + name |
| default | Medium | Photo + name + institution |
| detailed | Large | Full profile |
| inline | Text | Name only (linked) |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-expert-id | string | Expert identifier |
| data-variant | string | Display variant |
| data-show-stats | boolean | Show review count |
| data-verified | boolean | Show verified badge |

### Avatar Handling

**Photo available:**
- Display photo with object-fit: cover
- Circular crop
- Alt text empty (decorative)

**No photo:**
- Display initials derived from name
- Use consistent background based on ID
- Still accessible (name announced)

### Accessibility

- Article semantics for card
- Definition list for metadata
- Photo is decorative (name provides identity)
- Verified status announced

---

## InstitutionBadge

### Purpose and Use Cases

InstitutionBadge displays an institutional affiliation or partnership. Use for:
- Partner logos (CDLI, ORACC)
- Museum affiliations
- University endorsements
- Social proof

### Anatomy

```
+----------+
| [Logo]   |
| CDLI     |
+----------+
```

### HTML Structure

```html
<!-- With logo -->
<a
  href="https://cdli.ucla.edu"
  class="institution-badge"
  data-institution="cdli"
  target="_blank"
  rel="noopener"
>
  <img
    src="cdli-logo.svg"
    alt=""
    class="institution-badge__logo"
  >
  <span class="institution-badge__name">CDLI</span>
  <span class="visually-hidden">(opens in new tab)</span>
</a>

<!-- Logo only (compact) -->
<span class="institution-badge" data-variant="logo-only">
  <img
    src="yale-logo.svg"
    alt="Yale Babylonian Collection"
    class="institution-badge__logo"
  >
</span>

<!-- Text only (inline) -->
<span class="institution-badge" data-variant="text">
  Yale Babylonian Collection
</span>
```

### Variants

| Variant | Display | Use Case |
|---------|---------|----------|
| default | Logo + name | Partner list |
| logo-only | Logo only | Logo bar |
| text | Name only | Inline reference |
| linked | Clickable | External link |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-institution | string | Institution identifier |
| data-variant | string | Display variant |
| data-linked | boolean | Is external link |

### Accessibility

- Alt text on logos (or empty if name provided)
- External links indicate opening behavior
- Focus styles visible

---

## ContributorList

### Purpose and Use Cases

ContributorList displays all contributors to a piece of content. Use for:
- Transcription attribution
- Tablet contributor credits
- Export attribution blocks

### Anatomy

```
Contributors:
+--+  +--+  +--+  +2
|A1|  |A2|  |A3|  more
+--+  +--+  +--+

Expanded:
- User A (5 contributions)
- User B (3 contributions)
- AI Assistant
- User C (1 contribution)
```

### HTML Structure

```html
<div class="contributor-list" aria-label="Contributors">
  <!-- Collapsed (avatar stack) -->
  <div class="contributor-list__stack">
    <span class="contributor-avatar" aria-label="User A">
      <img src="avatar-a.jpg" alt="">
    </span>
    <span class="contributor-avatar" aria-label="User B">
      <img src="avatar-b.jpg" alt="">
    </span>
    <span class="contributor-avatar" aria-label="User C">
      <img src="avatar-c.jpg" alt="">
    </span>
    <span class="contributor-avatar contributor-avatar--overflow">
      +2
    </span>
  </div>

  <button
    type="button"
    class="contributor-list__toggle"
    aria-expanded="false"
    aria-controls="contributor-details"
  >
    5 contributors
  </button>

  <!-- Expanded list -->
  <ul
    id="contributor-details"
    class="contributor-list__details"
    hidden
  >
    <li class="contributor-item">
      <span class="contributor-avatar">...</span>
      <span class="contributor-name">User A</span>
      <span class="contributor-count">5 contributions</span>
    </li>
    <li class="contributor-item" data-type="ai">
      <span class="contributor-avatar contributor-avatar--ai">AI</span>
      <span class="contributor-name">AI Assistant</span>
      <span class="contributor-count">Initial proposal</span>
    </li>
    <!-- More contributors -->
  </ul>
</div>
```

### Variants

| Variant | Display | Use Case |
|---------|---------|----------|
| stack | Avatar stack | Compact |
| list | Full list | Attribution section |
| inline | Text list | Export/citation |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-contributors | string | JSON contributor array |
| data-max-visible | number | Avatars before +N |
| data-variant | string | Display variant |
| data-expandable | boolean | Can show full list |

### Accessibility

- Each avatar has aria-label with name
- Expandable section uses proper ARIA
- AI contributions clearly marked
- Total count announced

---

## ProvenanceTimeline

### Purpose and Use Cases

ProvenanceTimeline shows the complete history of content changes. Use for:
- Detailed review view
- Dispute resolution context
- Version history

### Anatomy

```
+------------------------------------------+
| HISTORY                                   |
+------------------------------------------+
| [AI] Jan 3, 10:42 AM                     |
| Initial proposal: "um-ma a-bi-e-szar"    |
+------------------------------------------+
| [User] Jan 3, 11:15 AM                   |
| Corrected to: "um-ma {m}a-bi-e-szar2"    |
| Note: Added determinative, corrected szar |
+------------------------------------------+
| [User] Jan 3, 11:30 AM                   |
| Confirmed reading                         |
+------------------------------------------+
| [Expert] Jan 3, 2:45 PM                  |
| Approved                                  |
+------------------------------------------+
```

### HTML Structure

```html
<section class="provenance-timeline" aria-label="Content history">
  <h3 class="provenance-timeline__title">History</h3>

  <ol class="provenance-timeline__events">
    <li class="provenance-event" data-type="ai">
      <div class="provenance-event__header">
        <span class="provenance-event__actor">
          <span class="actor-badge" data-type="ai">AI</span>
          AI Assistant
        </span>
        <time
          class="provenance-event__time"
          datetime="2026-01-03T10:42:00"
        >
          Jan 3, 10:42 AM
        </time>
      </div>
      <div class="provenance-event__content">
        <span class="provenance-event__action">Initial proposal:</span>
        <code class="provenance-event__value">um-ma a-bi-e-szar</code>
      </div>
    </li>

    <li class="provenance-event" data-type="user">
      <div class="provenance-event__header">
        <span class="provenance-event__actor">
          <span class="actor-badge" data-type="user">User</span>
          Contributor123
        </span>
        <time
          class="provenance-event__time"
          datetime="2026-01-03T11:15:00"
        >
          Jan 3, 11:15 AM
        </time>
      </div>
      <div class="provenance-event__content">
        <span class="provenance-event__action">Corrected to:</span>
        <code class="provenance-event__value">um-ma {m}a-bi-e-szar2</code>
        <p class="provenance-event__note">
          Added determinative, corrected szar
        </p>
      </div>
    </li>

    <li class="provenance-event" data-type="expert">
      <div class="provenance-event__header">
        <span class="provenance-event__actor">
          <span class="actor-badge" data-type="expert">Expert</span>
          Dr. Jane Smith
        </span>
        <time
          class="provenance-event__time"
          datetime="2026-01-03T14:45:00"
        >
          Jan 3, 2:45 PM
        </time>
      </div>
      <div class="provenance-event__content">
        <span class="provenance-event__action">Approved</span>
      </div>
    </li>
  </ol>
</section>
```

### Event Types

| Type | Actor Badge | Use Case |
|------|-------------|----------|
| ai | AI | AI-generated content |
| user | User | Volunteer contribution |
| expert | Expert | Expert action |
| system | System | Automated change |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-events | string | JSON event array |
| data-collapsed | boolean | Show recent only |
| data-max-visible | number | Events before "Show all" |

### Accessibility

- Ordered list semantics
- Time elements with machine-readable datetime
- Clear visual hierarchy
- Can be navigated linearly

---

## Usage Guidelines

### Trust Display Hierarchy

**Always visible (Level 1):**
- StatusBadge on all content
- ConfidenceMeter on uncertain content

**On request (Level 2):**
- TrustIndicator (click status for detail)
- ContributorList (expandable)

**Full detail (Level 3):**
- ProvenanceTimeline (dedicated view)
- ExpertCard (profile page)

### Combining Trust Components

```html
<article class="transcription-line">
  <div class="transcription-line__content">
    <!-- Content here -->
  </div>

  <div class="transcription-line__trust">
    <span class="status-badge" data-status="under-review">
      Under Review
    </span>
    <span class="confidence-meter" data-level="78">
      78%
    </span>
    <div class="contributor-list" data-max-visible="3">
      <!-- Contributors -->
    </div>
  </div>
</article>
```

### Status Transition Animations

When status changes:
1. Old badge fades out (150ms)
2. New badge fades in with scale (200ms)
3. Brief highlight effect (300ms)
4. Toast notification (optional)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial trust components |
