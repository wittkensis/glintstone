# Glintstone Project Timeline

**A living record of key decisions, feedback, and evolution**

> This file is automatically updated by Claude after significant changes. Each entry captures the "what" and "why" of project evolution.

---

## How to Read This Timeline

- **Decisions** are marked with the context that led to them
- **Feedback** from users is captured verbatim when significant
- **Commits** are referenced for historical integrity
- **Agents** involved are noted for transparency

---

## January 3, 2026 (Afternoon) - Project Restructuring

### User Feedback Session
> "We're at a point where the project structure needs to be cleaned up... Keep any application assets and logic separate from the agentic *.md files and process documents."

**Key Principle Established: App vs. Spec Separation**
- App files (src, public, dist) change like clay - fluid, iterative
- Spec files (strategies, PRDs, research) capture iterations - versioned, historical
- Never mix concerns between runtime code and process documentation

**Structural Changes:**
| Before | After | Rationale |
|--------|-------|-----------|
| `/docs/` | `/specs/` | Clearer purpose - these are specifications, not just documentation |
| `/scripts/` | `/tablet-pipeline/` | Descriptive - this is specifically for CDLI tablet management |
| `/Instructions/` | `/specs/` | Consolidated - all process docs in one place |
| Loose `*.md` files in root | `/specs/` | Clean root - only README and claude.md remain |

**New Agent Created:** `project-curator`
- Specializes in file/folder organization
- Enforces app/spec separation
- Manages context window efficiency

**Commits:** `14144d8`, `3238bc3`

---

### Landing Page Evolution

**User Feedback:**
> "Let's start implementing the new landing page using a combination of Option 5 but with the gamification factor of Option 4 folded into it. Keep a clear CTA at the top like Option 2 has."

**Product Manager + Market Strategist Reviews:**
Both agents independently recommended **Option 5 (Mystery Hook)** as foundation:
- "What stories have been waiting 3,000 years?" creates curiosity gap
- Question-driven narrative compels exploration
- Honest framing builds trust with academics

**Combined Landing Page (Option 6) Created:**
- Hero: Option 5's mystery question + Option 2's clear CTA
- Stats: Option 4's progress bar and gamification visuals
- Content: Option 5's curiosity-building question blocks
- Process: Option 2's practical "How It Works" section
- Roadmap: Option 4's milestone tracker

**File:** `specs/landing-options/option-6-combined.html`

---

## January 3, 2026 (Morning) - Demo Feedback & V3 Polish

### User Feedback (Critical)
> "This is badass. But..."

1. "Remove all of those freefloating unicode cuneiform emblems, they're tacky"
2. "Remove all of the excessive hover effects. Only interactive elements"
3. "Remove the SVG institution logos, they turned out horribly. Just use text"
4. "Anonymize the names of people providing quotes"
5. "Avoid showing fake stats or advocacy"
6. "The How it Works section isn't communicating the pipeline well"

**Design Principles Captured:**
- Purposeful and elegant, not gaudy and chaotic
- Hover effects only on truly interactive elements
- Honest framing > impressive-sounding stats
- "Feedback from academic consultation" > fake expert names

**Added to CLAUDE.md:** Output Quality Standards section

---

## January 2-3, 2026 - V3 Visual Transformation

### The Problem
> "It works, but it doesn't *feel* like ancient Mesopotamia... It's a demo, but not *believable*"

### The Solution: "Twilight Scholar" Design System

**Color Transformation:**
- Background: `#0a0e14` → `#0f1419` (deeper aged clay)
- Accent: Lapis Lazuli (`#4a6fa5`) + Fired Gold (`#d4af37`)
- Terracotta tones for warmth

**Authenticity Additions:**
- 8 authentic CDLI tablet photographs downloaded
- Noto Sans Cuneiform font integrated
- Dingir (𒀭) logo created - 3 variants
- 15 institution logos (later removed per feedback)

**Emotional Shift:**
> From "generic SaaS landing page" to "museum exhibition catalog meets documentary film"

**Commits:** `728cc48` through `34f7ada`

---

## Late December 2025 - Phase 2: Strategy & Roadmapping

### UX Architecture Decisions
**Agent:** `ux-architect`

**Breakthrough:** Progressive disclosure by user tier
- Passerby sees simplified UI
- Early Learner sees curriculum
- Expert sees full ATF editor

**Three Principles:**
1. Contextual authority (show expert faces, not faceless AI)
2. Contribution-reward cycle (immediate feedback, not points)
3. Adaptive task surfacing (match difficulty to confidence)

### PRD Structure Decision
**Agent:** `product-manager`

**Hybrid Approach Selected:**
- Layer PRDs (L1-L4): Shared capabilities
- Journey PRDs (J1-J5): User-specific flows

**The Five Journeys:**
| Journey | Focus | Priority |
|---------|-------|----------|
| J1 | Marketing page - "Can I trust this?" | POC |
| J2 | Passerby contribution - 3-minute task | POC |
| J3 | Early learner onboarding | Future |
| J4 | Expert review workflow | Future |
| J5 | Scholar integration | Future |

---

## Week 1-2, December 2025 - Phase 1: Discovery

### Ecosystem Mapping
**Agent:** `assyriology-ecosystem-advisor`

**Key Discoveries:**
- CDLI: 340k+ tablets cataloged
- ORACC: Corpus annotation projects
- Gap identified: No citizen science platform exists for cuneiform

### The Hobbyist Perspective
**Agent:** `assyriology-hobbyist`

**Critical Insight:**
> "I have 30 minutes on Sunday"

- Barrier: Overwhelming jargon, unclear entry points
- Motivation: Mystery and discovery > gamification gimmicks
- Sweet spot: Micro-contributions with visible impact

### Academic Reality Check
**Agent:** `assyriology-academic-advisor`

**Hard Truth:**
> "Academics won't use tools that compromise rigor"

**Must-haves:**
- Provenance tracking
- ATF format support
- Expert attribution
- Supplement existing databases, don't replace

### Market Positioning
**Agent:** `market-positioning-strategist`

**Resolution:** "Citizen science" positioning
- Rigorous but accessible
- Lead with mystery ("unlock ancient voices")
- Validate with authority (institutional partnerships)

---

## Pre-December 2025 - Phase 0: The Vision

### The Problem
- 500,000+ cuneiform tablets in collections worldwide
- ~200 active specialists
- Most tablets untranscribed or partially translated
- Processing backlog: centuries at current pace

### The Idea
- Crowdsourced transcription platform
- AI-assisted sign matching for non-experts
- Expert validation layer for quality
- Three-tier system: Passerby → Early Learner → Expert

### The Challenge
- How to build trust in a PhD-dominated field?
- How to make 4,000-year-old wedge marks compelling?
- How to scale academic workflows to thousands?

---

## Appendix: Key Files Created

### Discovery Phase
- `specs/discovery/ecosystem-research-report.md`
- `specs/discovery/curriculum-research-report.md`
- `specs/discovery/academic-workflow-report.md`
- `specs/discovery/hobbyist-feedback-report.md`
- `specs/discovery/marketing-positioning-analysis.md`

### UX Specifications
- `specs/ux/` - Component designs and screenflows (HTML)
- `specs/landing-options/` - 6 landing page alternatives

### Implementation
- `/src/` - React/TypeScript application
- `/tablet-pipeline/` - CDLI download and validation scripts
- `/.claude/agents/` - 13 specialized agent definitions

---

## Timeline Maintenance

This file is updated after significant project changes. To ensure updates:
1. Claude checks for this file after completing major tasks
2. New entries are prepended (newest first after the header)
3. Commit references are included for traceability
4. User feedback is captured verbatim when it shapes decisions

**Last Updated:** January 3, 2026
