# Overlay Components

**Component Category:** Core
**Document Version:** 1.0

Overlay components present content that floats above the main interface. These components handle focus management, backdrop interaction, and dismissal patterns.

**Design Principles:**
- Never trap users (always provide escape)
- Focus managed properly
- Backdrop dismissal as convention
- Animation enhances understanding
- Mobile-friendly positioning

---

## Modal

### Purpose and Use Cases

Modal displays content that requires user attention or decision. Use for:
- Confirmation dialogs
- Form dialogs
- Important alerts
- Content preview

### Anatomy

```
+-------- Backdrop --------+
|                          |
|  +--------------------+  |
|  | [X]     Title      |  |
|  |--------------------|  |
|  |                    |  |
|  |  Modal content     |  |
|  |                    |  |
|  |--------------------|  |
|  |    [Cancel] [OK]   |  |
|  +--------------------+  |
|                          |
+--------------------------+
```

### HTML Structure

```html
<div
  class="modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <!-- Backdrop -->
  <div class="modal__backdrop" data-action="close"></div>

  <!-- Dialog -->
  <div class="modal__dialog" role="document">
    <header class="modal__header">
      <h2 id="modal-title" class="modal__title">
        Confirm Action
      </h2>
      <button
        type="button"
        class="modal__close"
        aria-label="Close dialog"
        data-action="close"
      >
        <svg aria-hidden="true"><!-- close icon --></svg>
      </button>
    </header>

    <div id="modal-description" class="modal__content">
      <p>Are you sure you want to perform this action?</p>
    </div>

    <footer class="modal__footer">
      <button
        type="button"
        class="button"
        data-variant="ghost"
        data-action="close"
      >
        Cancel
      </button>
      <button
        type="button"
        class="button"
        data-variant="primary"
        data-action="confirm"
      >
        Confirm
      </button>
    </footer>
  </div>
</div>
```

### Variants

| Variant | Size | Use Case |
|---------|------|----------|
| sm | 400px | Simple confirmations |
| md | 560px | Forms, detailed content |
| lg | 720px | Complex content |
| fullscreen | 100% | Mobile, immersive |

### Animation

**Open:**
1. Backdrop fades in (150ms)
2. Dialog scales up from 95% + fades in (200ms)
3. Focus moves to first focusable element or close button

**Close:**
1. Dialog scales down + fades out (150ms)
2. Backdrop fades out (100ms)
3. Focus returns to trigger element

### Focus Management

1. On open: Save active element, move focus to modal
2. While open: Trap focus within modal (Tab cycles)
3. On close: Return focus to trigger element
4. First focusable: Close button or first form element

### Keyboard Interaction

| Key | Action |
|-----|--------|
| Tab | Cycle through focusable elements |
| Shift+Tab | Cycle backwards |
| Escape | Close modal |
| Enter | Activate focused button |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-size | string | Modal size variant |
| data-dismissable | boolean | Backdrop/Escape closes |
| data-persistent | boolean | Cannot be dismissed |

### Accessibility

- role="dialog" with aria-modal="true"
- Title linked via aria-labelledby
- Description linked via aria-describedby
- Focus trapped within modal
- Escape key closes (unless persistent)
- Body scroll disabled when open

---

## Popover

### Purpose and Use Cases

Popover shows contextual information triggered by interaction. Use for:
- Additional details
- Quick actions
- Help content
- Sign/line context

### Anatomy

```
+----------------+
|  Popover Title |
|----------------|
|  Content goes  |
|  here with     |
|  details.      |
|                |
|  [Action]      |
+----------------+
      /\ (arrow pointing to trigger)
```

### HTML Structure

```html
<!-- Trigger -->
<button
  type="button"
  class="popover-trigger"
  aria-expanded="false"
  aria-haspopup="dialog"
  aria-controls="popover-1"
>
  More info
</button>

<!-- Popover (positioned dynamically) -->
<div
  id="popover-1"
  class="popover"
  role="dialog"
  aria-label="More information"
  hidden
>
  <div class="popover__arrow"></div>

  <div class="popover__content">
    <h3 class="popover__title">Sign: AN</h3>
    <p class="popover__body">
      This sign means "god" or "sky" in Sumerian.
      It appears before divine names.
    </p>
    <a href="/learn/signs/an" class="popover__action">
      Learn more
    </a>
  </div>
</div>
```

### Positioning

Popover positions itself relative to trigger:
- Preferred: above trigger
- Fallback: below, left, or right
- Avoid: overlapping viewport edges
- Arrow always points to trigger

### States

| State | Description |
|-------|-------------|
| hidden | Not visible |
| opening | Animating in |
| visible | Displayed |
| closing | Animating out |

### Dismiss Triggers

- Click outside popover
- Press Escape
- Click close button (if present)
- Scroll (optional)
- Focus moves away (optional)

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-placement | string | Preferred position |
| data-offset | number | Distance from trigger |
| data-arrow | boolean | Show arrow |
| data-dismiss-on-scroll | boolean | Close when scrolling |

### Accessibility

- aria-expanded on trigger
- aria-haspopup="dialog" on trigger
- role="dialog" on popover
- Focus moves to popover (optional)
- Escape closes popover

---

## Tooltip

### Purpose and Use Cases

Tooltip provides brief supplementary information on hover/focus. Use for:
- Icon label clarification
- Abbreviated text explanation
- Keyboard shortcut hints

### Anatomy

```
+------------------+
| Brief text only  |
+------------------+
        \/
    [Element]
```

### HTML Structure

```html
<!-- Using native title (simplest) -->
<button type="button" title="Close dialog">
  <svg aria-hidden="true"><!-- close icon --></svg>
  <span class="visually-hidden">Close dialog</span>
</button>

<!-- Custom tooltip (more control) -->
<button
  type="button"
  aria-describedby="tooltip-1"
  class="tooltip-trigger"
>
  <svg aria-hidden="true"><!-- icon --></svg>
  <span class="visually-hidden">Confidence: Likely</span>
</button>

<div
  id="tooltip-1"
  role="tooltip"
  class="tooltip"
  hidden
>
  Confidence: Likely (72%)
</div>
```

### Behavior

**Show trigger:**
- Mouse hover (delay: 300ms)
- Keyboard focus (delay: 100ms)
- Touch: long-press (300ms)

**Hide trigger:**
- Mouse leaves
- Focus moves away
- After timeout (optional)
- Escape key

### Positioning

Same as popover, but simpler:
- Above by default
- Flip to below if no space
- Center-align with trigger

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-placement | string | Position preference |
| data-delay | number | Show delay (ms) |

### Accessibility

- role="tooltip" on tooltip element
- aria-describedby links trigger to tooltip
- NOT for essential information (use as supplementary)
- Visible text alternative always present

### Content Guidelines

- Maximum 8 words
- No interactive elements
- Use for clarification only
- Essential info belongs in visible UI

---

## Toast

### Purpose and Use Cases

Toast shows transient notifications that auto-dismiss. Use for:
- Success confirmations
- Error notifications
- System status updates
- Non-critical alerts

### Anatomy

```
+------------------------------------+
| [Icon] Message text       [X]      |
+------------------------------------+
```

### HTML Structure

```html
<div
  class="toast-container"
  aria-live="polite"
  aria-atomic="true"
>
  <!-- Toasts inserted here dynamically -->
</div>

<!-- Individual toast -->
<div class="toast" data-type="success" role="status">
  <svg class="toast__icon" aria-hidden="true">
    <!-- success icon -->
  </svg>
  <p class="toast__message">
    Your changes have been saved.
  </p>
  <button
    type="button"
    class="toast__dismiss"
    aria-label="Dismiss"
  >
    <svg aria-hidden="true"><!-- close icon --></svg>
  </button>
</div>
```

### Types

| Type | Icon | Use Case |
|------|------|----------|
| info | Info circle | Neutral information |
| success | Checkmark | Positive confirmation |
| warning | Warning triangle | Caution needed |
| error | X circle | Error notification |

### Behavior

**Display:**
- Appears at bottom-right (desktop) or bottom-center (mobile)
- Stacks vertically (newest at bottom)
- Maximum 3 visible at once

**Timing:**
- Auto-dismiss after 4-6 seconds
- Error toasts: longer or persistent
- Hover pauses auto-dismiss
- Focus pauses auto-dismiss

**Animation:**
- Slide in from right (desktop) or up (mobile)
- Fade out on dismiss

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-type | string | Toast type |
| data-duration | number | Auto-dismiss delay (ms) |
| data-persistent | boolean | No auto-dismiss |
| data-action | string | Optional action button |

### Accessibility

- Container is aria-live="polite"
- Content announced when added
- Dismiss button is keyboard accessible
- Does not steal focus
- Essential info needs alternative display

---

## ContextPanel

### Purpose and Use Cases

ContextPanel shows detailed information in a side panel. Use for:
- Sign/line detail (per UX Strategy 1.4)
- Tablet metadata
- Help content
- Secondary navigation

### Anatomy

```
Main Content         | Context Panel
                     |
                     | [X] Sign: AN
                     |----------------
                     | Meaning: god
                     | Readings: an
                     | Period: all
                     |
                     | [Learn more]
                     |
```

### HTML Structure

```html
<div class="layout-with-context">
  <main class="main-content">
    <!-- Primary content -->
  </main>

  <aside
    class="context-panel"
    aria-label="Context information"
    data-open="true"
  >
    <header class="context-panel__header">
      <h2 class="context-panel__title">Sign: AN</h2>
      <button
        type="button"
        class="context-panel__close"
        aria-label="Close panel"
      >
        <svg aria-hidden="true"><!-- close icon --></svg>
      </button>
    </header>

    <div class="context-panel__content">
      <dl class="context-panel__details">
        <dt>Meaning</dt>
        <dd>god, sky, heaven</dd>

        <dt>Readings</dt>
        <dd>an, dingir, ilu</dd>

        <dt>Period</dt>
        <dd>All periods</dd>
      </dl>

      <a href="/learn/signs/an" class="context-panel__action">
        Learn more about this sign
      </a>
    </div>
  </aside>
</div>
```

### Variants

| Variant | Behavior |
|---------|----------|
| inline | Always visible (desktop) |
| overlay | Slides over content (mobile) |
| modal | Full overlay (compact screens) |

### Responsive Behavior

| Screen | Behavior |
|--------|----------|
| Desktop (>1024px) | Inline sidebar |
| Tablet (768-1024px) | Collapsible sidebar |
| Mobile (<768px) | Full-height overlay |

### Animation

**Open (overlay/modal):**
- Slide in from right
- Duration: 250ms

**Close:**
- Slide out to right
- Duration: 200ms

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-open | boolean | Panel visibility |
| data-variant | string | Display variant |
| data-width | string | Panel width |
| data-context-type | string | sign/line/tablet |
| data-context-id | string | Context identifier |

### Accessibility

- aside landmark when inline
- role="dialog" when overlay/modal
- Focus managed when opening
- Escape closes overlay variants
- Content updates announced

---

## Usage Guidelines

### When to Use Each

| Component | Use For | Don't Use For |
|-----------|---------|---------------|
| Modal | Blocking decisions, forms | Notifications, help |
| Popover | Detailed context, actions | Essential info |
| Tooltip | Brief labels, hints | Long content |
| Toast | Transient notifications | Blocking alerts |
| ContextPanel | Detailed side info | Quick glances |

### Z-Index Stack

| Layer | Z-Index | Components |
|-------|---------|------------|
| Base | 0 | Page content |
| Header | 100 | Fixed header |
| Dropdown | 200 | Select menus |
| Popover | 300 | Popovers, tooltips |
| Panel | 400 | Context panels |
| Modal | 500 | Modals |
| Toast | 600 | Toast notifications |

### Animation Timing Summary

| Component | Enter | Exit |
|-----------|-------|------|
| Modal | 200ms | 150ms |
| Popover | 150ms | 100ms |
| Tooltip | 150ms | 100ms |
| Toast | 200ms | 150ms |
| ContextPanel | 250ms | 200ms |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial overlay components |
