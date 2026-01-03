# Glintstone Component Library

**Phase 3 - UX Design Documentation**
**Version:** 1.0
**Status:** Draft
**Date:** 2026-01-03

---

## Overview

This component library defines the unstyled, semantic building blocks for the Glintstone platform. Components are documented with their anatomy, variants, states, and interaction behaviors without applying the Stargazer's Script visual identity.

**Design Philosophy:**
- Semantic HTML as the foundation
- Accessibility-first (WCAG 2.1 AA baseline, AAA where feasible)
- Progressive enhancement
- Component composition over configuration
- Direct manipulation where possible (per Bret Victor's principles)

---

## Component Catalog

### Foundation Components

| Component | Purpose | Document |
|-----------|---------|----------|
| Container | Content width constraints | [layout.md](./layout.md#container) |
| Stack | Vertical spacing system | [layout.md](./layout.md#stack) |
| Cluster | Horizontal grouping with wrapping | [layout.md](./layout.md#cluster) |
| Grid | Multi-column layouts | [layout.md](./layout.md#grid) |
| Sidebar | Content with sidebar pattern | [layout.md](./layout.md#sidebar) |
| Switcher | Responsive row/column switching | [layout.md](./layout.md#switcher) |

### Tablet Interaction Components

| Component | Purpose | Document |
|-----------|---------|----------|
| TabletViewer | Pan/zoom tablet image display | [tablet.md](./tablet.md#tabletviewer) |
| RegionOverlay | Highlight areas on tablet | [tablet.md](./tablet.md#regionoverlay) |
| SignCard | Individual sign display with options | [tablet.md](./tablet.md#signcard) |
| TranscriptionLine | Single line of transliteration | [tablet.md](./tablet.md#transcriptionline) |
| TranscriptionPanel | Full tablet transcription display | [tablet.md](./tablet.md#transcriptionpanel) |

### Task Components

| Component | Purpose | Document |
|-----------|---------|----------|
| TaskCard | Container for individual tasks | [task.md](./task.md#taskcard) |
| SignMatchTask | Sign identification task type | [task.md](./task.md#signmatchtask) |
| BinaryTask | Yes/No decision task type | [task.md](./task.md#binarytask) |
| CountTask | Numeric input task type | [task.md](./task.md#counttask) |
| TaskQueue | Task list management | [task.md](./task.md#taskqueue) |

### Progress and Feedback Components

| Component | Purpose | Document |
|-----------|---------|----------|
| ProgressBar | Linear progress indicator | [progress.md](./progress.md#progressbar) |
| ProgressCircle | Circular progress indicator | [progress.md](./progress.md#progresscircle) |
| ConfidenceMeter | AI/crowd confidence display | [progress.md](./progress.md#confidencemeter) |
| RewardFeedback | Post-task celebration | [progress.md](./progress.md#rewardfeedback) |
| SessionSummary | End-of-session display | [progress.md](./progress.md#sessionsummary) |
| StatCard | Individual statistic display | [progress.md](./progress.md#statcard) |

### Trust and Authority Components

| Component | Purpose | Document |
|-----------|---------|----------|
| StatusBadge | Content verification status | [trust.md](./trust.md#statusbadge) |
| TrustIndicator | Aggregated trust signals | [trust.md](./trust.md#trustindicator) |
| ExpertCard | Expert profile display | [trust.md](./trust.md#expertcard) |
| InstitutionBadge | Institutional affiliation | [trust.md](./trust.md#institutionbadge) |
| ContributorList | Attribution display | [trust.md](./trust.md#contributorlist) |
| ProvenanceTimeline | Content history | [trust.md](./trust.md#provenancetimeline) |

### Navigation Components

| Component | Purpose | Document |
|-----------|---------|----------|
| Header | Global navigation bar | [navigation.md](./navigation.md#header) |
| NavItem | Individual navigation link | [navigation.md](./navigation.md#navitem) |
| Breadcrumb | Location hierarchy | [navigation.md](./navigation.md#breadcrumb) |
| TabGroup | Content tab navigation | [navigation.md](./navigation.md#tabgroup) |
| SurfaceTabs | Tablet surface switching | [navigation.md](./navigation.md#surfacetabs) |
| MobileNav | Mobile navigation drawer | [navigation.md](./navigation.md#mobilenav) |

### Form Components

| Component | Purpose | Document |
|-----------|---------|----------|
| Button | Action triggers | [forms.md](./forms.md#button) |
| TextInput | Single-line text entry | [forms.md](./forms.md#textinput) |
| TextArea | Multi-line text entry | [forms.md](./forms.md#textarea) |
| Select | Dropdown selection | [forms.md](./forms.md#select) |
| Checkbox | Boolean toggle | [forms.md](./forms.md#checkbox) |
| RadioGroup | Single selection from options | [forms.md](./forms.md#radiogroup) |
| EmailInput | Email capture with validation | [forms.md](./forms.md#emailinput) |

### Overlay Components

| Component | Purpose | Document |
|-----------|---------|----------|
| Modal | Blocking dialog | [overlays.md](./overlays.md#modal) |
| Popover | Contextual information | [overlays.md](./overlays.md#popover) |
| Tooltip | Brief hover information | [overlays.md](./overlays.md#tooltip) |
| Toast | Transient notification | [overlays.md](./overlays.md#toast) |
| ContextPanel | Detailed side panel | [overlays.md](./overlays.md#contextpanel) |

---

## Component Documentation Format

Each component is documented with:

1. **Purpose and Use Cases** - Why this component exists
2. **Anatomy** - Structural breakdown with semantic HTML
3. **Variants** - Different configurations of the component
4. **States** - Interactive states (default, hover, focus, active, disabled, error)
5. **Props/Attributes** - Configurable properties
6. **Accessibility** - WCAG requirements, ARIA attributes, keyboard interaction
7. **Behavior** - Interaction specifications
8. **Usage Guidelines** - When to use, when not to use

---

## Accessibility Standards

All components meet or exceed these requirements:

### Perceivable
- Text contrast ratio: 4.5:1 minimum (AA), 7:1 target (AAA)
- UI component contrast: 3:1 minimum
- Text resizable to 200% without loss of content
- No information conveyed by color alone

### Operable
- All functionality keyboard accessible
- Focus visible at all times (3:1 contrast minimum)
- Focus order follows visual order
- Touch targets minimum 44x44px
- Reduced motion support via prefers-reduced-motion

### Understandable
- Consistent navigation patterns
- Error prevention for destructive actions
- Clear error messages with recovery guidance
- Predictable interaction patterns

### Robust
- Valid semantic HTML
- Proper ARIA usage (roles, states, properties)
- Screen reader tested (VoiceOver, NVDA)

---

## Component States Reference

### Interactive States

| State | Description | CSS Selector |
|-------|-------------|--------------|
| Default | Resting state | - |
| Hover | Mouse over (desktop) | :hover |
| Focus | Keyboard focus | :focus-visible |
| Active | Being clicked/pressed | :active |
| Disabled | Not interactive | :disabled, [aria-disabled="true"] |

### Content States

| State | Description | Implementation |
|-------|-------------|----------------|
| Empty | No content available | Empty state component |
| Loading | Fetching content | Skeleton/spinner |
| Error | Failed to load | Error state with retry |
| Success | Action completed | Success feedback |

### Validation States

| State | Description | ARIA |
|-------|-------------|------|
| Valid | Input passes validation | aria-invalid="false" |
| Invalid | Input fails validation | aria-invalid="true" |
| Required | Must be completed | aria-required="true" |

---

## Spacing and Sizing

Components use a relative spacing system (not absolute values):

| Token | Description | Typical Use |
|-------|-------------|-------------|
| space-xs | Extra small gap | Icon to text |
| space-sm | Small gap | Related elements |
| space-md | Medium gap | Default component padding |
| space-lg | Large gap | Section separation |
| space-xl | Extra large gap | Major sections |

Touch targets: All interactive elements minimum 44x44px clickable area.

---

## Navigation

- [Layout Components](./layout.md)
- [Tablet Components](./tablet.md)
- [Task Components](./task.md)
- [Progress Components](./progress.md)
- [Trust Components](./trust.md)
- [Navigation Components](./navigation.md)
- [Form Components](./forms.md)
- [Overlay Components](./overlays.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial component library |
