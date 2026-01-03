# Release 1 PRD Suite

**Project:** Glintstone
**Phase:** Phase 2 - Strategy and Roadmapping
**Created:** 2026-01-03
**Status:** Ready for Implementation

---

## Overview

This directory contains the complete set of Product Requirements Documents (PRDs) for Glintstone Release 1 (POC Demo). The PRDs are organized using a hybrid structure of **Layer PRDs** (horizontal capabilities) and **Journey PRDs** (vertical user experiences).

**Architecture Principle:** Build Layers first, then assemble Journeys from Layer components.

---

## PRD Dependency Map

```
LAYER PRDs (Build First)
========================

  L1: Design System ----+
         |              |
         v              |
  L2: Dummy Data -------+
         |              |
         v              |
  L3: Tablet Components--+
         |               |
         v               |
  L4: Task & Progress ---+
                         |
                         v
JOURNEY PRDs (Build Second)
===========================

  J1: Marketing Page  <-------- L1, L2, L3
         |
         v
  J2: Passerby Flow  <--------- L1, L2, L3, L4  [CRITICAL PATH]
         |
         +---> J3: Early Learner <-- L1, L2, L3, L4
         |
         +---> J4: Expert Review <-- L1, L2, L3, L4
         |
         +---> J5: CDLI Integration <-- L1, L2, L3
```

---

## PRD Index

### Layer PRDs (Foundation and Core)

| PRD | Title | Priority | Complexity | Dependencies |
|-----|-------|----------|------------|--------------|
| [L1](./L1-foundation-design-system.md) | Design System and Tokens | P0 | M | None |
| [L2](./L2-foundation-dummy-data.md) | Dummy Data Schema and Fixtures | P0 | M | L1 |
| [L3](./L3-core-tablet-components.md) | Tablet Interaction Components | P0 | L | L1, L2 |
| [L4](./L4-core-task-progress.md) | Task Queue and Progress Components | P0 | M | L1, L2, L3 |

### Journey PRDs (User Experiences)

| PRD | Title | Priority | Complexity | Dependencies |
|-----|-------|----------|------------|--------------|
| [J1](./J1-marketing-page.md) | Marketing Page | P0 | M | L1, L2, L3 |
| [J2](./J2-passerby-contribution.md) | Passerby First Contribution | P0 | L | L1-L4 |
| [J3](./J3-early-learner-onboarding.md) | Early Learner Curriculum Preview | P1 | M | L1-L4 |
| [J4](./J4-expert-review-preview.md) | Expert Review Workflow Preview | P1 | M | L1-L4 |
| [J5](./J5-cdli-integration-demo.md) | CDLI Integration Demo | P1 | S | L1-L3 |

---

## Priority Definitions

- **P0 (Critical Path):** Must be complete for Release 1 demo. Blocking.
- **P1 (Should Have):** Important for full demo value. Not blocking but strongly desired.

---

## Implementation Order

### Sprint 1: Foundation
1. L1: Design System (design tokens, textures, icons)
2. L2: Dummy Data (schemas, fixtures)

### Sprint 2: Core Components
3. L3: Tablet Components (TabletViewer, SignCard, ConfidenceMeter, etc.)
4. L4: Task & Progress (TaskQueue, TaskCard, RewardFeedback, etc.)

### Sprint 3: Primary Journeys
5. J1: Marketing Page
6. J2: Passerby Contribution (CRITICAL - most important journey)

### Sprint 4: Secondary Journeys
7. J3: Early Learner Preview
8. J4: Expert Review Preview
9. J5: CDLI Integration Demo

---

## Key Success Metrics (Release 1)

| Metric | Target | Source |
|--------|--------|--------|
| Time to first contribution | < 60 seconds | J2 |
| Average tasks per session | > 5 | J2 |
| Session completion rate | > 70% | J2 |
| Marketing page CTA click rate | > 15% | J1 |
| Contributions per hour | > 30 | J2 |

---

## Cross-Cutting Concerns

### Trust Indicators
All PRDs incorporate trust elements per UX Strategy:
- Contextual Authority Model (status badges)
- Confidence visualization
- Provenance transparency
- Expert oversight messaging

### Brand Application
All PRDs reference the Stargazer's Script brand identity:
- Dark mode primary (Celestial Navy)
- Gold accents (Celestial Gold)
- Violet for AI features (Nebula Violet)
- Tactile, clay-like textures

### Accessibility
All PRDs require:
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader compatibility
- Color not as sole indicator

---

## UX Strategy Alignment

These PRDs implement **Strategic Direction C: Adaptive Task Surfacing** from the UX Strategy document. Key alignment points:

| UX Strategy Element | Implemented In |
|--------------------|----------------|
| Progressive Disclosure (1.1) | J1, J3, L3 ContextPanel |
| Contextual Authority Model (1.2) | L3 StatusBadge, all Journeys |
| Contribution-Reward Cycle (1.3) | L4 RewardFeedback, J2 |
| Guided Discovery Pattern (1.4) | L3 ContextPanel, J2 fun facts |
| Tablet Journey Lifecycle (2.4) | L2 schema, L3 StatusBadge |

---

## Document Conventions

Each PRD follows the hybrid structure from `docs/discovery/prd-structure-proposals.md`:

1. **Meta section:** Priority, complexity, dependencies, references
2. **Purpose/Narrative:** Why this matters, user story
3. **Success Metrics:** How we measure success
4. **Components/Stages:** Detailed specifications
5. **Acceptance Criteria:** Checkboxes for completion
6. **Integration Points:** Upstream/downstream dependencies
7. **Out of Scope:** What this PRD does NOT cover
8. **Testing Requirements:** What to validate

---

## Notes for Implementation

1. **Dummy Data is King:** Release 1 is a POC with static data. All "backend" is localStorage.

2. **Prefetch Everything:** Task flow must feel instant. Prefetch next task during current.

3. **Mobile-First:** Passerby contributions will often happen on phones.

4. **No Account Wall:** First contribution must be possible without registration.

5. **Celebrate Everything:** The reward feedback loop is critical for engagement.

6. **Demo Mode Clarity:** Expert and integration demos must clearly indicate they're demos.

---

## Questions and Clarifications

Direct questions about these PRDs to the Product Manager agent or raise in daily standups.

---

*This README is the entry point for the Release 1 PRD suite. Each linked PRD contains full specifications for its scope.*
