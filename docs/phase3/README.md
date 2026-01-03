# Phase 3: Engineering Architecture - Complete

**Date:** January 3, 2026
**Status:** ✅ Complete
**Team:** eng-architect, ux-designer, general-purpose (asset sourcing)

---

## Overview

Phase 3 delivered the complete engineering architecture, component library, screenflows, and visual asset infrastructure for Glintstone Release 1. All work was completed in parallel across three specialized agents.

---

## Deliverables

### 1. Component Architecture Proposal

**Location:** [component-architecture-proposal.md](./component-architecture-proposal.md)

**Includes:**
- Three architectural approach evaluations (Astro, Vite+React, Next.js)
- **RECOMMENDED:** Vite + React + TypeScript stack
- Complete technology stack specification
- Component library structure (Atoms → Molecules → Organisms → Templates)
- Comprehensive data model design with TypeScript + Zod
- Image and asset strategy
- 5-week implementation roadmap

**Key Decisions:**
- Framework: Vite + React + TypeScript
- Design System: Shadcn/UI + Tailwind CSS
- State Management: Zustand + TanStack Query
- Routing: TanStack Router (type-safe)
- Deployment: Vercel

### 2. Component Library (Unstyled)

**Location:** [components/](./components/)

**8 Component Categories:**
- [Layout Components](./components/layout.md) - Container, Stack, Grid, Cluster, Sidebar, Switcher
- [Tablet Interaction](./components/tablet.md) - TabletViewer, SignCard, TranscriptionPanel
- [Task Components](./components/task.md) - SignMatchTask, BinaryTask, CountTask, TaskQueue
- [Progress Components](./components/progress.md) - ProgressBar, ConfidenceMeter, RewardFeedback
- [Trust Components](./components/trust.md) - ExpertCard, InstitutionBadge, StatusBadge, ProvenanceTimeline
- [Navigation](./components/navigation.md) - Header, Breadcrumb, TabGroup, MobileNav
- [Forms](./components/forms.md) - Button, TextInput, Select, Checkbox, RadioGroup
- [Overlays](./components/overlays.md) - Modal, Popover, Tooltip, Toast

**Design Principles:**
- ✅ Semantic HTML only (no brand styling)
- ✅ Accessibility-first (WCAG 2.1 AA baseline)
- ✅ Touch target minimum 44px
- ✅ Complete keyboard navigation
- ✅ Screen reader support
- ✅ Reduced motion support

**Browse:** See [components/README.md](./components/README.md) for component catalog

### 3. Screenflows

**Location:** [screenflows/](./screenflows/)

**4 Complete User Journeys:**
- [J1: Marketing Page](./screenflows/J1-marketing.md) - 6 screens from hero to CTA
- [J2: Passerby Contribution](./screenflows/J2-passerby.md) - 7 screens, complete first contribution flow
- [J3: Early Learner Onboarding](./screenflows/J3-early-learner.md) - 7 screens, curriculum preview
- [J4: Expert Review](./screenflows/J4-expert-review.md) - 6 screens, expert workflow

Each screenflow includes:
- ASCII wireframes
- Component mapping
- State management
- Accessibility notes
- Responsive behavior
- Success metrics

### 4. Visual Assets Infrastructure

**Location:** `/public/`

**Data Manifests:**
- [experts.json](../../public/data/experts.json) - 12 fictional Assyriologist profiles
- [institutions.json](../../public/data/institutions.json) - 15 major organizations

**Documentation:**
- [ASSET-SOURCING.md](../../public/ASSET-SOURCING.md) - Comprehensive sourcing strategy
- [public/README.md](../../public/README.md) - Integration guide
- [images/experts/README.md](../../public/images/experts/README.md) - Avatar sourcing guide
- [images/institutions/README.md](../../public/images/institutions/README.md) - Logo sourcing guide

**Assets to Source:**
- 12 expert headshots/avatars (AI-generated or CC0)
- 15 institutional logos (press kits or Wikimedia Commons)

**Trust & Credibility Features:**
- Expert profiles: Diverse demographics, realistic academic credentials
- Institutions: Top-tier universities, museums, research platforms
- Data model: Credibility scores, partnership status, collection metrics
- Legal compliance: CC0/public domain sourcing, attribution guidelines

---

## Data Model Highlights

The architecture defines comprehensive TypeScript + Zod schemas for:

### Core Entities

**Tablet**
- Metadata (museum number, CDLI ID, period, genre)
- Image management (obverse, reverse, edge views)
- Transcription status workflow
- Expert review tracking

**Expert**
- Professional credentials (title, affiliation, specialization)
- Avatar/headshot URLs
- Credibility metrics (score, publications, years experience)
- Review activity tracking

**Institution**
- Organizational data (name, type, location)
- Logo URLs and brand guidelines
- Partnership status and credibility scores
- Collection metrics for museums

**Transcription**
- ATF format support
- Multi-contributor tracking
- Expert review workflow (Proposed → Verified → Accepted)
- Confidence scoring per element

**Contribution**
- Granular action tracking across all user tiers
- Attribution and credit mechanisms
- Session management
- Reward feedback data

### Scalability Path

- **Release 1 (POC):** JSON fixture files in `/public/data/`
- **Release 2 (ALPHA):** SQLite → PostgreSQL migration
- **Release 3 (BETA):** Add Redis caching, full-text search
- **Release 4 (1.0):** Elasticsearch, CDN, external API integrations

---

## Component Library Structure

Built on atomic design principles:

```
Atoms (Shadcn/UI primitives)
├── Button, Badge, Avatar, Card, Input, etc.
│
Molecules (Glintstone-specific)
├── SignCard (sign display + options)
├── ConfidenceMeter (5-level visualization)
├── ExpertAvatar (with credibility badge)
├── StatusBadge (6 verification states)
└── InstitutionLogo (with partner indicator)
│
Organisms (Complex features)
├── TabletViewer (pan/zoom, overlays)
├── TranscriptionWorkspace (ATF editor)
├── ReviewQueue (expert workflow)
├── TaskCard (micro-task container)
└── CurriculumModule (learning content)
│
Templates (User tier layouts)
├── PasserbyTaskFlow
├── LearnerDashboard
└── ExpertReviewDashboard
```

All components documented with:
- Purpose and use cases
- Props/attributes
- Variants and states
- Accessibility requirements
- Usage guidelines
- Implementation notes

---

## Alignment with Phase 2

This architecture implements the Phase 2 UX Strategy:

✅ **Progressive Disclosure** - Component complexity layers match user tiers
✅ **Contextual Authority** - Expert/institution trust components throughout
✅ **Contribution-Reward Cycle** - RewardFeedback and session summary components
✅ **Adaptive Task Surfacing** - TaskQueue with difficulty/confidence logic

And supports the approved PRD structure:

✅ **Hybrid Approach** - Layer PRDs (L1-L4) + Journey PRDs (J1-J5)
✅ **Capability Layers** - Shared component library serves all journeys
✅ **User Journey Flows** - Complete screenflows for each user tier

---

## Next Steps: Phase 4

With Phase 3 complete, the project is ready for Phase 4 (Detailed Implementation):

### Immediate Actions

1. **Source Visual Assets**
   - Generate/obtain 12 expert avatars following [sourcing guide](../../public/ASSET-SOURCING.md)
   - Download 15 institutional logos
   - Optimize images per specifications

2. **Initialize Codebase**
   - Set up Vite + React + TypeScript project
   - Install Shadcn/UI + Tailwind CSS
   - Configure TanStack Router, Zustand, Zod
   - Set up project structure per architecture proposal

3. **Implement Foundation (Week 1)**
   - Design system tokens (colors, typography, spacing)
   - Atom layer components (Shadcn/UI configuration)
   - JSON data fixtures (experts, institutions, tablets)
   - Mock API layer

4. **Build Component Library (Week 2)**
   - Molecule layer: SignCard, ConfidenceMeter, ExpertAvatar, StatusBadge
   - Organism layer: TabletViewer, TaskCard, ReviewQueue
   - Storybook setup for component browsing

5. **Implement Journeys (Week 3)**
   - J1: Marketing page
   - J2: Passerby contribution flow
   - J3: Early learner onboarding (if time permits)
   - J4: Expert review workflow (if time permits)

### Agent Assignments (Phase 4)

- **eng-frontend**: Build out React components and implement screenflows
- **brand-visual-designer**: Apply brand styling to unstyled components
- **ux-designer**: Review implementations, refine interactions
- **eng-architect**: Code review, performance optimization, scaling prep

---

## Key Achievements

✅ Complete architectural proposal with 3 evaluated approaches
✅ Recommended technology stack with clear rationale
✅ Comprehensive data model supporting dummy → live data scaling
✅ 8-category unstyled component library with 50+ components
✅ 4 complete screenflows with wireframes and component mapping
✅ Visual asset infrastructure with 12 expert profiles + 15 institutions
✅ Accessibility-first design (WCAG 2.1 AA baseline)
✅ Trust/credibility built into data model (expert avatars, institutional logos)
✅ Clear 5-week implementation roadmap

---

## Files Created

### Documentation
- `docs/phase3/component-architecture-proposal.md`
- `docs/phase3/components/README.md`
- `docs/phase3/components/layout.md`
- `docs/phase3/components/tablet.md`
- `docs/phase3/components/task.md`
- `docs/phase3/components/progress.md`
- `docs/phase3/components/trust.md`
- `docs/phase3/components/navigation.md`
- `docs/phase3/components/forms.md`
- `docs/phase3/components/overlays.md`
- `docs/phase3/screenflows/README.md`
- `docs/phase3/screenflows/J1-marketing.md`
- `docs/phase3/screenflows/J2-passerby.md`
- `docs/phase3/screenflows/J3-early-learner.md`
- `docs/phase3/screenflows/J4-expert-review.md`

### Data & Assets
- `public/data/experts.json`
- `public/data/institutions.json`
- `public/ASSET-SOURCING.md`
- `public/README.md`
- `public/images/experts/README.md`
- `public/images/institutions/README.md`

---

## Agent Contributions

**eng-architect (a504007)**
- Evaluated 3 architectural approaches
- Recommended Vite + React + TypeScript stack
- Designed complete data model with scalability path
- Created 5-week implementation roadmap

**ux-designer (ad658f2)**
- Designed 8-category unstyled component library
- Created 4 complete screenflows with wireframes
- Documented 50+ components with accessibility specs
- Built browsable component catalog

**general-purpose (a051973)**
- Created expert and institution data manifests
- Designed visual asset infrastructure
- Wrote comprehensive sourcing strategy
- Documented legal/attribution requirements

---

**Phase 3 Status: ✅ COMPLETE**

Ready to proceed to Phase 4: Detailed Implementation
