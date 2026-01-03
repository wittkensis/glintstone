# L3: Core - Tablet Interaction Components

**Document Type:** Layer PRD
**Priority:** P0 (Critical Path)
**Status:** Ready
**Estimated Complexity:** L
**Dependencies:** L1 (Design System), L2 (Dummy Data)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| Layer Level | Core |
| Serves User Types | All (Passerby, Early Learner, Expert) |
| UX Strategy Reference | Section 1.2: Contextual Authority Model; Section 1.4: Guided Discovery Pattern |
| PRD Structure Reference | prd-structure-proposals.md Example (Core - Tablet Interaction Components) |

---

## Layer Purpose

Provide reusable UI components for viewing and interacting with cuneiform tablet images across all user experiences. These components abstract the complexity of tablet display, sign highlighting, confidence visualization, and contextual information so that Experience layer screens can focus on user-type-specific workflows.

**Why This Matters for Release 1:**
- TabletViewer is the visual centerpiece of the platform
- SignCard enables the core Passerby contribution task
- ConfidenceMeter builds trust through transparency (UX Strategy P1)
- ContextPanel supports progressive disclosure (UX Strategy 1.1)

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Technical | All components render in < 100ms | Yes |
| Technical | Tablet images load in < 2 seconds | Yes |
| Enablement | Experience layer can build screens without image handling logic | Yes |
| Usability | Touch targets meet 44px minimum | Yes |
| Accessibility | All components keyboard navigable | Yes |

---

## Capabilities Provided

| Capability | Description | Consumed By |
|------------|-------------|-------------|
| Tablet Display | Render tablet image with zoom/pan | All experience screens |
| Sign Highlighting | Overlay highlights on specific signs | Task cards, transcription UI |
| Region Selection | Interactive clickable regions | Passerby tasks, review UI |
| Confidence Display | Visualize confidence levels | All transcription views |
| Status Badges | Show content authority status | All tablet displays |
| Context Panel | Show contextual information for selections | Early Learner, Expert views |

---

## Components

### Component 1: TabletViewer

**Purpose:** Display tablet image with standard pan/zoom interactions and optional sign region highlighting.

**Interface:**

```typescript
interface TabletViewerProps {
  // Required
  tabletId: string;
  surface: 'obverse' | 'reverse' | 'edge';

  // Optional - Display
  initialZoom?: number;               // 0.5 - 3.0, default 1.0
  showControls?: boolean;             // Zoom buttons, default true
  aspectRatio?: 'auto' | 'square' | '4:3';

  // Optional - Interaction
  highlightRegions?: SignRegion[];    // Regions to highlight
  activeRegionId?: string;            // Currently selected region
  selectionMode?: 'none' | 'single' | 'multi';
  disabled?: boolean;

  // Callbacks
  onRegionClick?: (region: SignRegion) => void;
  onRegionHover?: (region: SignRegion | null) => void;
  onZoomChange?: (level: number) => void;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

interface SignRegion {
  id: string;
  x: number;                          // Percentage 0-100
  y: number;
  width: number;
  height: number;
  signId?: string;
  lineNumber: number;
  positionInLine: number;
  status?: ContentStatus;             // Affects highlight color
  confidenceScore?: number;           // Affects highlight opacity
}
```

**Visual Specification:**

```
+------------------------------------------+
|  [Tablet Image]                     [-][+] |  <- Zoom controls (top-right)
|                                           |
|     +------+                              |
|     | Sign |  <- Highlighted region       |
|     | Here |     (pulsing border)         |
|     +------+                              |
|                                           |
|                                           |
|           [Pan indicator on drag]         |
|                                           |
+------------------------------------------+
|  Obverse | Reverse | Edge               |  <- Surface tabs (if multiple)
+------------------------------------------+
```

**Behavior Specification:**

1. **Image Loading:**
   - Show skeleton placeholder during load
   - Fade in image when loaded
   - Display error state with retry button on failure

2. **Zoom/Pan:**
   - Pinch-to-zoom on touch devices
   - Scroll-wheel zoom on desktop (with modifier key to avoid scroll hijack)
   - Click-and-drag to pan when zoomed
   - Zoom controls: [-] [reset] [+]
   - Zoom range: 0.5x to 3.0x

3. **Region Highlighting:**
   - Highlighted regions have pulsing border (gold for active, violet for AI-suggested)
   - Hover shows tooltip with basic region info
   - Click triggers onRegionClick callback
   - Multiple regions can be highlighted simultaneously
   - Active region has stronger visual emphasis

4. **Accessibility:**
   - Keyboard navigation between regions (Tab/Arrow keys)
   - Focus ring on active region
   - Alt text for tablet image
   - Zoom controls are labeled

**Acceptance Criteria:**
- [ ] Supports pinch-to-zoom on touch devices
- [ ] Supports scroll-to-zoom on desktop (with Ctrl/Cmd modifier)
- [ ] Renders placeholder during image load
- [ ] Displays error state with retry option on load failure
- [ ] Highlight regions pulse subtly to draw attention
- [ ] Clicking region triggers callback with region data
- [ ] Keyboard navigation works between highlighted regions
- [ ] Surface tabs switch between obverse/reverse views
- [ ] Zoom level persists during surface switch
- [ ] Component is responsive (works on mobile widths)

---

### Component 2: SignCard

**Purpose:** Display isolated sign with selection options for matching/identification tasks.

**Interface:**

```typescript
interface SignCardProps {
  // Required
  signImage: string;                  // URL to isolated sign image
  options: SignOption[];              // 2-4 options for selection

  // Optional
  prompt?: string;                    // "Which sign matches?"
  allowSkip?: boolean;                // Show skip button, default true
  allowUnsure?: boolean;              // Show "I'm not sure" option, default true
  showConfidence?: boolean;           // Show confidence for each option
  size?: 'compact' | 'standard' | 'large';
  disabled?: boolean;

  // AI context
  aiSuggestion?: string;              // ID of AI-suggested option
  aiConfidence?: number;              // AI confidence 0-100

  // Callbacks
  onSelect: (option: SignOption) => void;
  onSkip?: () => void;
  onUnsure?: () => void;
}

interface SignOption {
  id: string;
  label: string;                      // Sign name, e.g., "AN"
  imageUrl: string;                   // Reference sign image
  meaning?: string;                   // For context, e.g., "god, sky"
  isCorrect?: boolean;                // For validation (not shown to user)
}
```

**Visual Specification:**

```
+------------------------------------------+
|  Which sign matches the highlighted area? |
+------------------------------------------+
|                                           |
|        +------------------+               |
|        |   [Sign Image   |               |
|        |    from tablet] |               |
|        +------------------+               |
|                                           |
+------------------------------------------+
|  +--------+  +--------+                   |
|  | Option |  | Option |  <- Sign options  |
|  |   A    |  |   B    |     2x2 grid      |
|  +--------+  +--------+                   |
|  +--------+  +--------+                   |
|  | Option |  | Option |                   |
|  |   C    |  |   D    |                   |
|  +--------+  +--------+                   |
+------------------------------------------+
|  [I'm not sure]              [Skip ->]   |
+------------------------------------------+
```

**Behavior Specification:**

1. **Option Display:**
   - 2x2 grid for 4 options
   - Single row for 2-3 options
   - Options are large touch targets (min 72px)
   - AI suggestion has subtle violet border (if shown)

2. **Selection:**
   - Single selection only
   - Selected option gets gold border and checkmark
   - Other options fade slightly
   - Brief animation on selection
   - Callback fires immediately

3. **Skip/Unsure:**
   - Skip advances without recording answer
   - "I'm not sure" records uncertainty (valuable data per hobbyist-feedback-report.md)
   - Both should be visually secondary to main options

4. **Feedback Mode (optional):**
   - After selection, can show if answer matched consensus
   - "Most people chose the same!" or "Interesting - this one is tricky!"

**Acceptance Criteria:**
- [ ] Sign image maintains aspect ratio in container
- [ ] Options display in 2x2 grid for 4 options
- [ ] Options display in row for 2-3 options
- [ ] Selected state is visually distinct (gold border)
- [ ] Skip button positioned consistently (bottom-right)
- [ ] "I'm not sure" option is always available
- [ ] AI suggestion indicated with subtle violet styling
- [ ] Touch targets meet 44px minimum
- [ ] Keyboard: Enter selects focused option
- [ ] Animation on selection < 200ms

---

### Component 3: ConfidenceMeter

**Purpose:** Visualize confidence level for a transcription element, supporting both AI and aggregated confidence.

**Interface:**

```typescript
interface ConfidenceMeterProps {
  // Required
  level: number;                      // 0-100

  // Optional
  variant: 'compact' | 'standard' | 'detailed';
  source?: 'ai' | 'crowd' | 'expert' | 'aggregated';
  showTooltip?: boolean;              // Hover explanation
  showLabel?: boolean;                // Text label
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;                 // Animate on mount
}
```

**Visual Specification:**

**Compact Variant (for inline use):**
```
[*]  <- Colored dot only
```

**Standard Variant (for cards):**
```
[====----] 65%  <- Progress bar with percentage
```

**Detailed Variant (for focused views):**
```
+---------------------------+
| Confidence: Likely (72%)  |
| [=========-------]        |
| AI + 8 contributors       |
+---------------------------+
```

**Color Mapping (per UX Strategy 4.3):**

| Level | Label | Color Token |
|-------|-------|-------------|
| 0-20% | Uncertain | `--color-confidence-uncertain` (red) |
| 21-50% | Possible | `--color-confidence-possible` (orange) |
| 51-75% | Likely | `--color-confidence-likely` (yellow) |
| 76-90% | Confident | `--color-confidence-confident` (green) |
| 91-100% | Verified | `--color-confidence-verified` (bold green + shield) |

**Accessibility:**
- Color is never the only indicator (use icons/patterns)
- Tooltip provides full explanation
- Progress bar has aria-valuenow

**Acceptance Criteria:**
- [ ] Compact variant shows colored dot with appropriate icon
- [ ] Standard variant shows progress bar with percentage
- [ ] Detailed variant shows label, bar, and source info
- [ ] Color scale matches UX Strategy specification
- [ ] Colorblind accessible (icons accompany colors)
- [ ] Tooltip explains what confidence means (per UX Strategy 1.4)
- [ ] Animated mount option for celebration moments
- [ ] aria-valuenow set correctly for screen readers

---

### Component 4: StatusBadge

**Purpose:** Display content authority status per the Contextual Authority Model.

**Interface:**

```typescript
interface StatusBadgeProps {
  status: ContentStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;                // Show text label
  showIcon?: boolean;                 // Show status icon
  interactive?: boolean;              // Clickable for details
  onClick?: () => void;
}

type ContentStatus =
  | 'proposed'
  | 'under-review'
  | 'provisionally-accepted'
  | 'accepted'
  | 'disputed'
  | 'superseded';
```

**Visual Specification (per UX Strategy 1.2):**

| Status | Icon | Border Style | Color |
|--------|------|--------------|-------|
| Proposed | ? | Dashed | Orange/muted |
| Under Review | Clock | Solid | Violet |
| Provisionally Accepted | Single Check | Solid | Blue |
| Accepted | Double Check/Shield | Bold | Green |
| Disputed | Split/Debate | Split | Deep Orange |
| Superseded | Strikethrough | Faded | Gray |

**Acceptance Criteria:**
- [ ] All 6 status types render correctly
- [ ] Icons match status (question, clock, checks, etc.)
- [ ] Border styles differentiate status at a glance
- [ ] Interactive badges show pointer cursor
- [ ] Tooltip explains status meaning (for non-experts)
- [ ] Status is colorblind accessible (icons + patterns)

---

### Component 5: ContextPanel

**Purpose:** Display contextual information for selected tablet elements using progressive disclosure.

**Interface:**

```typescript
interface ContextPanelProps {
  // Required
  contextType: 'sign' | 'word' | 'line' | 'tablet';
  contextId: string;

  // Optional
  variant?: 'popover' | 'sidebar' | 'inline';
  expanded?: boolean;                 // For accordion behavior
  showDeepDiveLink?: boolean;         // Link to full learning content

  // Callbacks
  onNavigate?: (targetId: string, targetType: string) => void;
  onClose?: () => void;
  onExpandToggle?: (expanded: boolean) => void;
}
```

**Content by Context Type:**

**Sign Context:**
```
+---------------------------+
| Sign: AN (dingir)         |
+---------------------------+
| Meaning: god, sky, heaven |
| Readings: an, dingir, ilu |
| Frequency: Very common    |
+---------------------------+
| [Learn more about AN ->]  |
+---------------------------+
```

**Line Context:**
```
+---------------------------+
| Line 1 (Obverse)          |
+---------------------------+
| a-na {d}utu be-li2-ia     |
| "To Shamash, my lord"     |
+---------------------------+
| Status: Under Review      |
| Confidence: 78%           |
| Contributors: 5           |
+---------------------------+
```

**Tablet Context:**
```
+---------------------------+
| YBC 4644 (P123456)        |
+---------------------------+
| Old Babylonian Letter     |
| From: Sippar (uncertain)  |
| Period: ~1800 BCE         |
+---------------------------+
| Stage: Draft Transcription|
| Progress: 45% complete    |
| Contributors: 12          |
+---------------------------+
| [View in CDLI ->]         |
+---------------------------+
```

**Progressive Disclosure (per UX Strategy 1.4):**
1. **Tooltip (hover):** Brief label only (max 8 words)
2. **Popover (click):** Summary context (max 50 words)
3. **Deep Dive (link):** Full learning/exploration page

**Acceptance Criteria:**
- [ ] Loads appropriate data based on context type
- [ ] Shows loading skeleton during data fetch
- [ ] Displays "No data available" gracefully
- [ ] Links to related contexts are navigable
- [ ] Popover variant positions intelligently (no overflow)
- [ ] Sidebar variant is collapsible
- [ ] Deep dive links go to appropriate learning content
- [ ] Keyboard accessible (Escape closes popover)

---

### Component 6: TranscriptionLine

**Purpose:** Display a single line of cuneiform transcription with sign-level interactivity.

**Interface:**

```typescript
interface TranscriptionLineProps {
  // Required
  lineNumber: number;
  surface: 'obverse' | 'reverse';
  transliteration: string;            // ATF-style text

  // Optional
  translation?: string;
  status?: ContentStatus;
  confidenceScore?: number;
  segments?: TranscriptionSegment[];  // For sign-level highlighting
  showStatus?: boolean;
  editable?: boolean;

  // Callbacks
  onSegmentClick?: (segment: TranscriptionSegment) => void;
  onEdit?: (newText: string) => void;
}

interface TranscriptionSegment {
  id: string;
  text: string;
  startIndex: number;
  endIndex: number;
  type: 'sign' | 'determinative' | 'number' | 'damaged' | 'missing';
  signId?: string;
  confidenceScore?: number;
  status?: ContentStatus;
}
```

**Visual Specification:**

```
1. a-na {d}utu be-li2-ia          [Under Review] [72%]
   ^^^^ ^^^^^^ ^^^^^^^^^^
   |    |      |
   |    |      +-- Segment: word (clickable)
   |    +-- Segment: divine determinative (gold)
   +-- Segment: word
```

**Styling by Segment Type:**
- Regular text: Monospace font (Fira Code)
- Determinatives: Gold color, smaller superscript
- Damaged signs: Gray with damage icon (#)
- Missing signs: Bracketed, italicized [x]
- Low confidence: Dashed underline

**Acceptance Criteria:**
- [ ] Line number displayed prominently
- [ ] Transliteration uses monospace font
- [ ] Segments are individually hoverable/clickable
- [ ] Determinatives styled distinctly (gold, superscript)
- [ ] Damaged/missing notation follows ATF conventions
- [ ] Status badge shows if showStatus=true
- [ ] Confidence meter inline if score provided
- [ ] Editable mode shows inline text input

---

## Integration Points

### Upstream Dependencies
- L1: Design System (all visual tokens)
- L2: Dummy Data (Tablet, Sign, Contribution schemas)

### Downstream Consumers
- L4: Task & Progress Components (uses SignCard, ConfidenceMeter)
- J1: Marketing Page (uses TabletViewer for hero)
- J2: Passerby Contribution (uses SignCard, TabletViewer)
- J3: Early Learner (uses all components)
- J4: Expert Review (uses all components)
- J5: CDLI Integration (uses TabletViewer, StatusBadge)

---

## Configuration and Extensibility

**TabletViewer:**
- Accepts custom highlight colors per region
- Supports custom overlay layers (for annotation tools in future)

**SignCard:**
- Options can include confidence scores for each choice
- Feedback mode can be enabled for educational contexts

**ContextPanel:**
- Content is user-type-aware (simpler for Passerby, detailed for Expert)
- Custom content renderers can be injected

---

## Out of Scope

- Drawing or annotation tools (Phase 2+)
- Collaborative cursors / real-time presence (Phase 2+)
- Real image processing (using pre-cropped dummy data)
- RTI (Reflectance Transformation Imaging) viewer (Phase 2+)
- 3D tablet model viewer (Phase 2+)

---

## Testing Requirements

**Unit Tests:**
- Each component renders with minimal required props
- Each component handles null/empty data gracefully
- Callbacks fire with correct arguments
- Keyboard navigation works correctly

**Integration Tests:**
- TabletViewer + SignCard selection flow
- TabletViewer + ContextPanel navigation
- Region click -> ContextPanel display

**Visual Tests:**
- Snapshot tests for all component states
- Dark mode renders correctly
- Responsive breakpoints work
- Status badge colors are correct

**Accessibility Tests:**
- All components pass axe-core checks
- Keyboard navigation works end-to-end
- Focus management is correct
- ARIA attributes are valid

---

## Technical Hints

**Recommended Libraries:**

1. **Image Pan/Zoom:** Consider `react-zoom-pan-pinch` or custom implementation with CSS transforms
2. **Overlays:** Absolute positioned divs with percentage-based coordinates
3. **Popovers:** `@floating-ui/react` for smart positioning
4. **Animations:** CSS transitions for performance, Framer Motion for complex sequences

**Performance Considerations:**

1. Lazy load tablet images
2. Use `loading="lazy"` for off-screen images
3. Debounce zoom/pan events
4. Memoize region overlay calculations
5. Use CSS transforms for animations (GPU accelerated)

**Component File Structure:**

```
/components/tablet/
  TabletViewer/
    TabletViewer.tsx
    TabletViewer.test.tsx
    TabletViewer.styles.ts
    useTabletZoom.ts          # Custom hook for zoom logic
    RegionOverlay.tsx         # Sub-component
  SignCard/
    SignCard.tsx
    SignCard.test.tsx
    SignOption.tsx            # Sub-component
  ConfidenceMeter/
    ConfidenceMeter.tsx
    ConfidenceMeter.test.tsx
  StatusBadge/
    StatusBadge.tsx
    StatusBadge.test.tsx
  ContextPanel/
    ContextPanel.tsx
    ContextPanel.test.tsx
    contexts/                 # Content renderers by type
      SignContext.tsx
      LineContext.tsx
      TabletContext.tsx
  TranscriptionLine/
    TranscriptionLine.tsx
    TranscriptionLine.test.tsx
    TranscriptionSegment.tsx
  index.ts                    # Barrel export
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
