# L1: Foundation - Design System and Tokens

**Document Type:** Layer PRD
**Priority:** P0 (Critical Path)
**Status:** Ready
**Estimated Complexity:** M
**Dependencies:** None (Foundation Layer)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| Layer Level | Foundation |
| Serves User Types | All (Passerby, Early Learner, Expert) |
| UX Strategy Reference | Section 8: Principles and Guardrails; Section 7: Interaction Surface Layers |
| Brand Reference | Stargazer's Script (brand-identity-proposals.md) |

---

## Layer Purpose

Establish the foundational design system that implements the "Stargazer's Script" brand identity across all Glintstone interfaces. This layer provides design tokens, component primitives, and visual utilities that enable consistent, accessible, and on-brand UI development for all subsequent layers and journeys.

**Why This Matters for Release 1:**
- Visual consistency builds trust (UX Strategy Principle P1: Trust Over Speed)
- Foundation must be stable before Experience layers build upon it
- Stargazer's Script brand is optimized for dark mode with tactile, clay-like surfaces

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Technical | All tokens documented and exported | 100% coverage |
| Technical | WCAG 2.1 AA contrast compliance | 100% of text combinations |
| Enablement | Experience layers can build without custom color/spacing values | Yes |
| Enablement | Components render consistently across Chrome, Safari, Firefox | Yes |

---

## Capabilities Provided

| Capability | Description | Consumed By |
|------------|-------------|-------------|
| Color Tokens | Brand palette in CSS custom properties | All components |
| Typography Tokens | Font families, sizes, weights, line-heights | All text elements |
| Spacing Tokens | Consistent margin/padding scale | All layout components |
| Surface Textures | Clay-like tactile SVG textures | Buttons, cards, panels |
| Shadow System | Elevation levels for depth | Cards, modals, overlays |
| Animation Tokens | Transition timing and easing | Interactive elements |
| Icon System | Cuneiform-inspired icon set | Navigation, actions, status |

---

## Components

### Component 1: Color Token System

**Purpose:** Define the complete Stargazer's Script color palette as CSS custom properties.

**Specification:**

```css
:root {
  /* Primary - Celestial Navy (dark mode base) */
  --color-primary-900: #0A0F14; /* Deep Space - maximum contrast */
  --color-primary-800: #0D1B2A; /* Celestial Navy - main background */
  --color-primary-700: #1B2838; /* Night Sky - elevated surfaces */
  --color-primary-600: #243447; /* Twilight - hover states */

  /* Secondary - Starlight (text on dark) */
  --color-secondary-100: #F0F4F8; /* Starlight - primary text */
  --color-secondary-200: #CBD5E1; /* Cosmic Dust - secondary text */
  --color-secondary-300: #94A3B8; /* Asteroid - tertiary text */

  /* Accent - Celestial Gold (key interactions) */
  --color-accent-gold-500: #FFD166; /* Celestial Gold - primary accent */
  --color-accent-gold-400: #FFDF8C; /* Gold Light - hover */
  --color-accent-gold-600: #E8B84A; /* Gold Dark - pressed */

  /* Accent - Nebula Violet (AI features) */
  --color-accent-violet-500: #7B68EE; /* Nebula Violet - AI indicators */
  --color-accent-violet-400: #9B8BF4; /* Violet Light */
  --color-accent-violet-600: #5B4BC7; /* Violet Dark */

  /* Semantic - Status Colors */
  --color-success-500: #10B981; /* Aurora Green - verified/accepted */
  --color-warning-500: #F59E0B; /* Solar Flare - review needed */
  --color-error-500: #EF4444; /* Red Giant - errors */

  /* Contextual Authority Colors (per UX Strategy 1.2) */
  --color-status-proposed: #F59E0B; /* Orange - awaiting validation */
  --color-status-under-review: #7B68EE; /* Violet - consensus building */
  --color-status-provisional: #60A5FA; /* Blue - single expert approved */
  --color-status-accepted: #10B981; /* Green - fully verified */
  --color-status-disputed: #F97316; /* Deep Orange - experts disagree */

  /* Confidence Meter Colors (per UX Strategy 4.3) */
  --color-confidence-uncertain: #EF4444; /* 0-20% */
  --color-confidence-possible: #F59E0B; /* 21-50% */
  --color-confidence-likely: #FBBF24; /* 51-75% */
  --color-confidence-confident: #10B981; /* 76-90% */
  --color-confidence-verified: #059669; /* 91-100% with shield */

  /* Surface Colors */
  --color-surface-base: var(--color-primary-800);
  --color-surface-elevated: var(--color-primary-700);
  --color-surface-overlay: rgba(27, 40, 56, 0.95);

  /* Border Colors */
  --color-border-subtle: rgba(255, 255, 255, 0.08);
  --color-border-default: rgba(255, 255, 255, 0.15);
  --color-border-emphasis: var(--color-accent-gold-500);
}
```

**Acceptance Criteria:**
- [ ] All colors defined as CSS custom properties in a single tokens file
- [ ] Light mode variant tokens defined (for accessibility escape hatch)
- [ ] Color combinations pass WCAG 2.1 AA contrast (4.5:1 for text, 3:1 for UI)
- [ ] Colorblind-accessible - confidence and status use patterns/icons, not just color
- [ ] Tokens consumable by Tailwind CSS configuration

---

### Component 2: Typography Token System

**Purpose:** Define the typography scale implementing Stargazer's Script fonts.

**Specification:**

```css
:root {
  /* Font Families - per brand-identity-proposals.md */
  --font-heading: 'Cormorant Garamond', Georgia, serif;
  --font-body: 'Open Sans', system-ui, sans-serif;
  --font-mono: 'Fira Code', 'JetBrains Mono', monospace;

  /* Font Weights */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Type Scale (per brand proposal) */
  --text-display: 3.5rem;    /* 56px - hero headlines */
  --text-h1: 2.625rem;       /* 42px */
  --text-h2: 2rem;           /* 32px */
  --text-h3: 1.5rem;         /* 24px */
  --text-h4: 1.125rem;       /* 18px */
  --text-body: 1rem;         /* 16px */
  --text-small: 0.875rem;    /* 14px */
  --text-caption: 0.75rem;   /* 12px */

  /* Line Heights */
  --leading-tight: 1.05;
  --leading-snug: 1.15;
  --leading-normal: 1.35;
  --leading-relaxed: 1.65;

  /* Letter Spacing */
  --tracking-tight: -0.02em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;
}
```

**Typography Classes:**

```css
.text-display {
  font-family: var(--font-heading);
  font-size: var(--text-display);
  font-weight: var(--font-weight-medium);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

/* Note: No italics per brand feedback */
.text-heading-1 { /* ... */ }
.text-heading-2 { /* ... */ }
.text-heading-3 { /* ... */ }
.text-heading-4 { /* ... */ }
.text-body { /* ... */ }
.text-small { /* ... */ }
.text-caption { /* ... */ }
.text-mono { /* For ATF/transliteration */ }
```

**Acceptance Criteria:**
- [ ] Cormorant Garamond loaded for headings (no italics variant needed)
- [ ] Open Sans loaded for body text
- [ ] Fira Code loaded for monospace/transliteration
- [ ] Font loading optimized (font-display: swap, preload critical fonts)
- [ ] Typography classes available as utility classes
- [ ] No italic variants used anywhere (per brand feedback)

---

### Component 3: Spacing Token System

**Purpose:** Consistent spacing scale for layout and component internals.

**Specification:**

```css
:root {
  /* Base spacing unit: 4px */
  --space-0: 0;
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
  --space-20: 5rem;    /* 80px */
  --space-24: 6rem;    /* 96px */

  /* Component-specific spacing */
  --space-button-x: var(--space-6);
  --space-button-y: var(--space-3);
  --space-card-padding: var(--space-6);
  --space-section-gap: var(--space-16);
}
```

**Acceptance Criteria:**
- [ ] Spacing tokens exported as CSS custom properties
- [ ] Tailwind spacing configuration aligned with tokens
- [ ] Component padding/margin uses only token values

---

### Component 4: Surface Texture System

**Purpose:** Implement tactile, clay-tablet-inspired textures for UI surfaces.

**Specification:**

Per brand feedback: "Make the UI feel more 'tactile' overall, as if the buttons themselves are clay tablets, and find a way to add SVG texture to various surfaces in a tasteful way."

**Texture Assets:**

1. **Clay Surface Texture** (`texture-clay.svg`)
   - Subtle noise pattern suggesting unfired clay
   - Low opacity (5-10%) overlay
   - Use on: primary buttons, card backgrounds

2. **Pressed Wedge Texture** (`texture-wedge.svg`)
   - Very subtle cuneiform-inspired impressions
   - Near-invisible at normal zoom
   - Use on: hover states, accent areas

3. **Stone Surface Texture** (`texture-stone.svg`)
   - Smooth, polished appearance
   - Use on: navigation, headers

**Implementation Pattern:**

```css
.surface-clay {
  background-color: var(--color-surface-elevated);
  background-image: url('/textures/texture-clay.svg');
  background-blend-mode: overlay;
  background-size: 200px 200px;
}

.surface-button-primary {
  background: linear-gradient(
    180deg,
    var(--color-accent-gold-500) 0%,
    var(--color-accent-gold-600) 100%
  );
  background-image: url('/textures/texture-clay.svg');
  background-blend-mode: soft-light;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border-radius: 6px;
}
```

**Acceptance Criteria:**
- [ ] Three SVG texture files created and optimized (<5KB each)
- [ ] Textures tile seamlessly
- [ ] Textures do not impact text readability
- [ ] Textures visible but subtle on high-DPI displays
- [ ] Surface utility classes documented

---

### Component 5: Shadow and Elevation System

**Purpose:** Define depth hierarchy for layered UI elements.

**Specification:**

```css
:root {
  /* Elevation levels (dark mode optimized) */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.6);

  /* Glow effects (for accent elements) */
  --glow-gold: 0 0 20px rgba(255, 209, 102, 0.3);
  --glow-violet: 0 0 20px rgba(123, 104, 238, 0.3);
  --glow-success: 0 0 12px rgba(16, 185, 129, 0.3);

  /* Focus ring */
  --ring-focus: 0 0 0 3px rgba(255, 209, 102, 0.4);
}
```

**Acceptance Criteria:**
- [ ] Shadow tokens exported
- [ ] Glow effects available for interactive feedback
- [ ] Focus states use visible ring (accessibility)

---

### Component 6: Animation Token System

**Purpose:** Consistent motion design for interactions and transitions.

**Specification:**

```css
:root {
  /* Durations */
  --duration-instant: 0ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-slower: 600ms;

  /* Easing */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Standard transitions */
  --transition-colors: color var(--duration-fast) var(--ease-default),
                       background-color var(--duration-fast) var(--ease-default),
                       border-color var(--duration-fast) var(--ease-default);
  --transition-transform: transform var(--duration-normal) var(--ease-out);
  --transition-opacity: opacity var(--duration-normal) var(--ease-default);
  --transition-all: all var(--duration-normal) var(--ease-default);
}
```

**Acceptance Criteria:**
- [ ] Animation tokens respect `prefers-reduced-motion` media query
- [ ] No animations exceed 600ms
- [ ] Celebration animations (task completion) use bounce easing

---

### Component 7: Icon System Foundation

**Purpose:** Cuneiform-inspired icon set for navigation and actions.

**Icon Categories Required:**

1. **Navigation Icons:**
   - Home / Dashboard
   - Contribute
   - Explore
   - Learn
   - Profile
   - Search
   - Menu (hamburger)

2. **Action Icons:**
   - Play / Start
   - Skip
   - Submit / Check
   - Close / Cancel
   - Expand / Collapse
   - Zoom In / Out
   - Pan / Move

3. **Status Icons:**
   - AI Suggestion (sparkles/nebula)
   - Confidence Levels (1-5 variants)
   - Proposed (question mark)
   - Under Review (clock)
   - Provisionally Accepted (single checkmark)
   - Accepted (double checkmark / shield)
   - Disputed (split/debate)

4. **Object Icons:**
   - Tablet
   - Cuneiform Sign
   - Stylus
   - Star (dingir reference)
   - User / Profile
   - Expert Badge

**Visual Style:**
- 24px base size
- 1.5px stroke weight
- Slightly rounded terminals (per brand proposal)
- Gold for primary, violet for AI-related

**Acceptance Criteria:**
- [ ] Minimum 25 icons created covering core needs
- [ ] Icons available as SVG sprites
- [ ] Icons accessible (title elements, aria-labels documented)
- [ ] Icons render sharply at 16px, 24px, 32px sizes

---

## Integration Points

### Upstream Dependencies
None (this is the foundation layer)

### Downstream Consumers
- L2: Dummy Data Schema (uses status colors)
- L3: Tablet Interaction Components (uses all tokens)
- L4: Task & Progress Components (uses all tokens)
- All Journey PRDs (J1-J5)

---

## Configuration and Extensibility

**Theme Switching:**
- Dark mode is primary (Stargazer's Script)
- Light mode tokens defined for accessibility fallback
- Theme toggle should be available but not prominent in Release 1

**Token Export Formats:**
- CSS Custom Properties (primary)
- Tailwind CSS configuration object
- JSON (for potential design tool integration)

---

## Out of Scope

- Complex animation sequences (covered in individual components)
- Responsive breakpoint definitions (simple mobile-first approach sufficient)
- Form validation styling (covered in L3/L4)
- Print stylesheets

---

## Testing Requirements

**Unit Tests:**
- Token values are valid CSS
- All color combinations pass contrast checks

**Visual Tests:**
- Typography renders correctly with web fonts
- Textures tile without visible seams
- Components look correct in dark/light modes

**Cross-Browser:**
- Chrome 90+
- Safari 15+
- Firefox 95+
- Edge 90+

---

## Technical Hints

**Recommended Implementation:**

1. Create a `/styles/tokens/` directory with:
   - `colors.css`
   - `typography.css`
   - `spacing.css`
   - `shadows.css`
   - `animations.css`

2. Create a main `tokens.css` that imports all token files

3. Configure Tailwind to extend from token values:
   ```javascript
   // tailwind.config.js
   module.exports = {
     theme: {
       extend: {
         colors: {
           primary: 'var(--color-primary-800)',
           // ...
         }
       }
     }
   }
   ```

4. Create SVG textures using Figma or similar, export as optimized SVG

5. Use CSS `font-display: swap` and preload critical fonts

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
