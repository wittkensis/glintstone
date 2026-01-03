# Glintstone Screenflows

**Phase 3 - UX Design Documentation**
**Version:** 1.0
**Status:** Draft
**Date:** 2026-01-03

---

## Overview

This directory contains detailed screenflows for the core user journeys in Glintstone Release 1. Each screenflow maps the complete user experience from entry to completion, documenting screens, transitions, decision points, and component usage.

**Relationship to Component Library:**
Screenflows compose components from `/docs/phase3/components/` into complete user experiences. Each screen references the specific components used.

---

## Screenflow Index

| Journey | User Type | Priority | Document |
|---------|-----------|----------|----------|
| Marketing Page | All | P0 | [J1-marketing.md](./J1-marketing.md) |
| Passerby Contribution | Passerby | P0 | [J2-passerby.md](./J2-passerby.md) |
| Early Learner Onboarding | Early Learner | P1 | [J3-early-learner.md](./J3-early-learner.md) |
| Expert Review | Expert | P1 | [J4-expert-review.md](./J4-expert-review.md) |

---

## How to Read Screenflows

### Screen Documentation Format

Each screen is documented with:

1. **Screen ID and Name** - Unique identifier and descriptive name
2. **Entry Points** - How users arrive at this screen
3. **User Goal** - What the user is trying to accomplish
4. **Screen Wireframe** - ASCII diagram of screen layout
5. **Component List** - Components used from the library
6. **Interactions** - What happens when users interact
7. **Exit Points** - Where users can go from here
8. **States** - Loading, error, empty states
9. **Accessibility Notes** - Specific a11y considerations

### Wireframe Conventions

```
+------------------------------------------+  <- Screen boundary
| [Header Component]                       |  <- Component reference
+------------------------------------------+
|                                          |
|  {Content Area}                          |  <- Content area
|                                          |
|  [Component Name]                        |  <- Interactive component
|                                          |
+------------------------------------------+
| [Footer or Actions]                      |
+------------------------------------------+

Annotations:
[Component]  - Reference to component from library
{Area}       - Generic content area
(Note)       - Design note or explanation
->           - User action/transition
<-           - Entry/navigation source
[*]          - Required/critical element
```

### Flow Diagram Conventions

```
[Screen A] --action--> [Screen B]
     |
     +--(condition)--> [Screen C]

States:
[Screen]     - User-visible screen
(Decision)   - System or user decision
{Process}    - Background process
```

---

## Journey Overview Map

```
                    MARKETING PAGE (J1)
                           |
                    [Try it now]
                           |
                           v
                    PASSERBY FLOW (J2)
                    /              \
           [Learn more]      [Create account]
                  /                    \
                 v                      v
        EARLY LEARNER (J3)       [Future: Auth]
                                        |
                                        v
                                 EXPERT REVIEW (J4)
                                 (Requires credentials)
```

---

## Critical Path: Passerby First Contribution

The most important journey is the Passerby First Contribution flow. This is the primary conversion funnel for the platform.

**Goal:** Marketing page visitor completes their first contribution in under 60 seconds.

```
Marketing Hero    Welcome       Tutorial      First       Reward      Session
   CTA        ->   Screen   ->   (15s)    ->  Task   ->  Feedback -> Continue
  [5 sec]         [3 sec]       [15 sec]    [30 sec]    [2 sec]     (Loop)
```

**Target Metrics:**
- Time to first task: < 25 seconds
- Time to first completion: < 60 seconds
- Session completion rate: > 70%
- Tasks per session: > 5

---

## Responsive Considerations

All screenflows are designed mobile-first:

| Breakpoint | Viewport | Adjustments |
|------------|----------|-------------|
| Mobile | < 768px | Single column, larger touch targets, mobile nav |
| Tablet | 768-1023px | Two-column where appropriate, touch-friendly |
| Desktop | >= 1024px | Full layout, hover states, keyboard shortcuts |

---

## Navigation

- [J1: Marketing Page](./J1-marketing.md)
- [J2: Passerby Contribution](./J2-passerby.md)
- [J3: Early Learner Onboarding](./J3-early-learner.md)
- [J4: Expert Review](./J4-expert-review.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial screenflows |
