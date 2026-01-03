# PRD Structure Proposals for Agentic Development

**Project:** Glintstone - AI-Powered Cuneiform Transcription Platform
**Author:** Product Manager Agent
**Date:** January 2, 2026
**Phase:** Discovery

---

## Executive Summary

This document proposes three distinct approaches for structuring Product Requirements Documents (PRDs) optimized for agentic development workflows. Each approach is designed to enable AI agents to execute effectively while maintaining human oversight and strategic alignment.

**Key Constraints for Release 1 (POC Demo):**
- Dummy data only - no live integrations
- Goal: Make vision "believable, enticing, and a source for feedback"
- Must demonstrate value for both academics and hobbyists
- Includes marketing page + main app + CDLI integration demo

**Primary KPIs:**
- Academics: Number of newly transcribed artifacts (demo simulated)
- Hobbyists: Number of contributions per hour (demo simulated)

---

## Approach 1: Atomic Feature Units (AFU)

### 1.1 Approach Name & Philosophy

**Core Organizing Principle:** Break every feature into the smallest independently shippable unit that delivers user value.

**Why This Works for Agentic Development:**
- AI agents excel at bounded, well-defined tasks with clear success criteria
- Small scope reduces hallucination risk and implementation drift
- Enables parallel execution across multiple agents
- Each unit is testable in isolation before integration
- Mirrors how LLMs naturally decompose problems

This approach treats each PRD as a "contract" - a precise specification that an AI agent can implement without requiring additional context beyond what is documented.

### 1.2 PRD Structure Template

```
# [Feature ID]: [Feature Name]

## Meta
- Status: Draft | Ready | In Progress | Complete
- Priority: P0 | P1 | P2
- Estimated Complexity: XS | S | M | L | XL
- Dependencies: [List of Feature IDs]
- Assigned Agent: [Agent Name]

## Problem Statement (2-3 sentences max)
What user pain point does this solve?

## Success Metrics
- Primary: [Quantifiable metric]
- Secondary: [Qualitative indicator]

## User Story
As a [user type], I want to [action] so that [outcome].

## Acceptance Criteria (Checkbox format)
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Scope
### In Scope
- Bullet list of what IS included

### Out of Scope
- Bullet list of what is NOT included (critical for agents)

## Technical Hints (Optional)
- Non-binding suggestions for implementation approach
- Component or pattern recommendations

## UI/UX Reference
- Link to wireframe section or component spec

## Test Scenarios
1. Happy path scenario
2. Edge case scenario
3. Error state scenario
```

**Level of Detail:**
- Acceptance criteria must be binary (pass/fail)
- No ambiguous language ("should," "might," "could")
- Include explicit boundary conditions
- Reference specific wireframe sections by name

**Handling Dependencies:**
- Dependencies are explicit via Feature IDs
- Blocked features cannot start until dependencies reach "Complete" status
- Shared components get their own Feature ID with highest priority

### 1.3 Prioritization Framework

**Sequencing for Release 1:**

| Tier | Criteria | Examples |
|------|----------|----------|
| P0 - Must Ship | Demonstrates core value proposition; blocks other features | Sign viewer, basic transcription UI, marketing hero section |
| P1 - Should Ship | Differentiates from existing tools; enables key demo moments | AI suggestion display, confidence indicators, contribution counter |
| P2 - Nice to Have | Polish and delight; can be cut without harming demo | Animations, advanced filtering, social features |

**MVP Criteria:**
- Does it appear in the wireframe's "critical path"?
- Can the demo be understood without it?
- Does it require backend infrastructure we don't have?

**Balancing Academic vs Hobbyist:**
For Release 1, prioritize features that:
1. Serve BOTH audiences (shared infrastructure)
2. Hobbyist features (faster to demo, more visual impact)
3. Academic features (deeper but narrower appeal)

Ratio target: 60% shared / 25% hobbyist / 15% academic

### 1.4 Example PRD Outline

```
# AFU-007: Sign Recognition Micro-Task Card

## Meta
- Status: Ready
- Priority: P0
- Estimated Complexity: M
- Dependencies: AFU-001 (Design System), AFU-003 (Tablet Viewer)
- Assigned Agent: eng-frontend

## Problem Statement
Passerby users need a frictionless way to contribute to transcription
without any cuneiform knowledge. Currently, there is no way for
untrained users to provide valuable input on sign recognition.

## Success Metrics
- Primary: User can complete one micro-task in under 30 seconds
- Secondary: UI feels "game-like" and rewarding

## User Story
As a Passerby, I want to quickly compare cuneiform sign options
so that I can contribute to transcription without expertise.

## Acceptance Criteria
- [ ] Card displays isolated sign image from tablet
- [ ] 2-4 sign options displayed as clickable choices
- [ ] One option is "None of these / Unclear"
- [ ] Selection triggers immediate visual feedback (correct/selected state)
- [ ] "Skip" button available without penalty messaging
- [ ] Progress indicator shows position in current session
- [ ] Completion triggers celebration micro-interaction

## Scope
### In Scope
- Single sign comparison UI
- Static dummy data for sign options
- Session progress tracking (frontend only)
- Basic animations for feedback

### Out of Scope
- Backend submission of answers
- Accuracy scoring against "correct" answers
- User accounts or persistent progress
- Batch task queuing

## UI/UX Reference
- Wireframe: "Passerby Experience" section
- Component: Zooniverse-style choice card pattern

## Test Scenarios
1. User selects matching sign - sees success feedback
2. User selects "None of these" - proceeds without error
3. User clicks Skip - advances to next without feedback
4. User completes 10 tasks - sees session summary
```

### 1.5 Pros & Cons

**Pros:**
- Maximum clarity for AI agents - minimal interpretation needed
- Easy to track progress and identify blockers
- Enables parallel work across multiple agents
- Simple to re-prioritize individual units
- Natural fit for iterative, agile delivery

**Cons:**
- Risk of losing holistic user journey coherence
- Many small PRDs require robust dependency management
- Can feel bureaucratic for simple features
- Integration testing becomes critical
- May miss emergent requirements that span multiple units

**Best When:**
- Team has multiple AI agents working in parallel
- Features are relatively independent
- Clear wireframes already exist
- Speed of delivery is paramount

---

## Approach 2: User Journey Flows (UJF)

### 2.1 Approach Name & Philosophy

**Core Organizing Principle:** Organize PRDs around complete user journeys, ensuring each document captures an end-to-end experience for a specific user type.

**Why This Works for Agentic Development:**
- Maintains narrative coherence that AI can understand and preserve
- Each journey provides full context, reducing agent "drift"
- Natural alignment with the three user tiers (Passerby, Early Learner, Expert)
- Enables agents to make contextually appropriate micro-decisions
- Reduces risk of building disconnected features

This approach recognizes that AI agents benefit from understanding the "why" and broader context, not just isolated tasks.

### 2.2 PRD Structure Template

```
# Journey: [Journey Name]

## Meta
- User Type: Passerby | Early Learner | Expert
- Journey Scope: [Start State] --> [End State]
- Priority: P0 | P1 | P2
- Status: Draft | Ready | In Progress | Complete

## Journey Narrative (3-5 sentences)
Describe the complete experience from the user's perspective,
including their emotional state and goals.

## Success Metrics
- Experience Metric: [How users feel]
- Behavior Metric: [What users do]
- Outcome Metric: [What gets accomplished]

## Journey Map

### Stage 1: [Stage Name]
**User Goal:** What the user wants at this moment
**System Response:** What the app does
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

### Stage 2: [Stage Name]
...

### Stage N: [Stage Name]
...

## Shared Components Required
- [Component Name] - [Brief description]

## Edge Cases & Error States
| Scenario | Expected Behavior |
|----------|-------------------|
| ... | ... |

## Dependencies
- Prerequisite Journeys: [List]
- Shared Components: [List]

## Out of Scope for Release 1
- Explicit list of journey extensions deferred

## Design References
- Wireframe sections: [List]
- Interaction patterns: [List]
```

**Level of Detail:**
- Journey narrative provides context for AI decision-making
- Stage-by-stage breakdown ensures completeness
- Acceptance criteria remain binary but within journey context
- Shared components called out to identify cross-journey work

**Handling Dependencies:**
- Journeys can depend on other journeys (sequential unlocking)
- Shared components extracted and built first
- Cross-journey touchpoints explicitly documented

### 2.3 Prioritization Framework

**Sequencing for Release 1:**

| Priority | Journey Type | Rationale |
|----------|--------------|-----------|
| P0 | Passerby Complete Journey | Fastest to demo, widest appeal, proves volunteer model |
| P0 | Marketing Page Journey | Required for all audiences to discover product |
| P1 | Early Learner Onboarding | Shows depth and learning potential |
| P1 | Expert Review Preview | Demonstrates academic value proposition |
| P2 | Cross-User Handoff | Shows ecosystem integration (complex) |

**MVP Criteria:**
- Is this journey visible in a 5-minute demo?
- Does removing this journey break the product narrative?
- Can this journey be completed with dummy data?

**Balancing Academic vs Hobbyist:**
- Lead with Passerby journey (hobbyist-friendly, visually compelling)
- Include at least one stage of Expert journey (academic validation)
- Use Early Learner as the bridge narrative between audiences

### 2.4 Example PRD Outline

```
# Journey: Passerby First Contribution

## Meta
- User Type: Passerby
- Journey Scope: Landing --> First Completed Micro-Task --> Session Summary
- Priority: P0
- Status: Ready

## Journey Narrative
A curious visitor arrives from the marketing page, intrigued by the
idea of contributing to ancient history research. Within 60 seconds,
they complete their first micro-task without creating an account.
They feel a sense of accomplishment and understand how their small
contribution connects to larger research goals. They leave with a
desire to return.

## Success Metrics
- Experience Metric: >80% report feeling "I made a real contribution"
- Behavior Metric: Average time to first task < 60 seconds
- Outcome Metric: >3 tasks completed per session

## Journey Map

### Stage 1: Entry Point
**User Goal:** Understand what this is and if it's for them
**System Response:**
- Display welcoming hero with immediate "Try it now" CTA
- No account required messaging prominent
- Show real-time contribution counter (social proof)

**Acceptance Criteria:**
- [ ] Hero section loads in < 2 seconds
- [ ] "Try it now" CTA is above the fold
- [ ] Contribution counter displays and animates

### Stage 2: Task Introduction
**User Goal:** Understand what they're being asked to do
**System Response:**
- Brief animated tutorial (< 15 seconds)
- Show example task with guided overlay
- "Got it" confirmation before live task

**Acceptance Criteria:**
- [ ] Tutorial is skippable
- [ ] Tutorial explains task in < 3 steps
- [ ] Example uses real tablet imagery

### Stage 3: First Micro-Task
**User Goal:** Successfully complete a contribution
**System Response:**
- Display sign recognition card (isolated sign + options)
- Immediate feedback on selection
- Progress indicator shows "1 of 10"

**Acceptance Criteria:**
- [ ] Task renders with sign image clearly visible
- [ ] Options are large enough for mobile tap targets
- [ ] Feedback appears within 200ms of selection

### Stage 4: Momentum Building
**User Goal:** Feel growing sense of progress
**System Response:**
- Sequential tasks with variety
- Occasional "fun facts" between tasks
- Progress bar filling

**Acceptance Criteria:**
- [ ] No two consecutive tasks look identical
- [ ] Fun fact appears after every 3rd task
- [ ] Progress bar animates smoothly

### Stage 5: Session Complete
**User Goal:** Feel accomplished, understand impact
**System Response:**
- Celebration animation
- Summary: "You helped with X signs from tablet Y"
- CTA: "Create account to track progress" or "Do more"

**Acceptance Criteria:**
- [ ] Summary shows actual task count
- [ ] Tablet reference links to tablet viewer
- [ ] Both CTAs are equally prominent

## Shared Components Required
- Sign Recognition Card (used in Early Learner journey too)
- Progress Bar Component
- Celebration Animation
- Fun Fact Display

## Edge Cases & Error States
| Scenario | Expected Behavior |
|----------|-------------------|
| User abandons mid-session | No penalty, can resume anytime |
| All dummy tasks exhausted | Show "Come back soon" message |
| Image fails to load | Skip task automatically, log error |

## Dependencies
- Prerequisite Journeys: None (entry point)
- Shared Components: Design System foundations

## Out of Scope for Release 1
- Account creation flow
- Persistent progress tracking
- Task difficulty adaptation
- Leaderboards

## Design References
- Wireframe: "Passerby Experience" section
- Interaction patterns: Zooniverse task flow, Duolingo session structure
```

### 2.5 Pros & Cons

**Pros:**
- Maintains user experience coherence throughout development
- AI agents can make contextually appropriate decisions
- Natural alignment with user research and personas
- Easier to demo and validate with stakeholders
- Reduces integration surprises

**Cons:**
- Larger PRD scope means longer agent execution time
- Harder to parallelize work within a journey
- Risk of scope creep within journey boundaries
- Dependencies between journeys can create bottlenecks
- May duplicate component specifications across journeys

**Best When:**
- User experience coherence is paramount
- Team has clear user personas and journeys mapped
- Features are tightly interconnected
- Stakeholder demos are frequent checkpoints

---

## Approach 3: Capability Layers (CL)

### 3.1 Approach Name & Philosophy

**Core Organizing Principle:** Structure PRDs around horizontal capability layers that serve multiple user types, building from foundational infrastructure up to user-facing experiences.

**Why This Works for Agentic Development:**
- Creates reusable components that multiple agents can build upon
- Reduces redundant specification across user types
- Natural progression from stable foundations to flexible surfaces
- Enables clear division of labor between specialist agents
- Mirrors how modern applications are actually architected

This approach recognizes that the three user tiers (Passerby, Early Learner, Expert) share significant underlying capabilities, and building those shared layers first creates leverage.

### 3.2 PRD Structure Template

```
# Layer: [Layer Name]

## Meta
- Layer Level: Foundation | Core | Experience | Polish
- Serves User Types: [List]
- Priority: P0 | P1 | P2
- Status: Draft | Ready | In Progress | Complete

## Layer Purpose
Why does this layer exist? What does it enable?

## Capabilities Provided
| Capability | Description | Consumed By |
|------------|-------------|-------------|
| ... | ... | ... |

## Success Metrics
- Technical: [Performance, reliability metrics]
- Enablement: [What becomes possible]

## Components

### Component 1: [Name]
**Purpose:** Brief description
**Interface:**
- Inputs: [What it accepts]
- Outputs: [What it provides]
- Events: [What it emits]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

### Component 2: [Name]
...

## Integration Points
- Upstream Dependencies: [Layers this depends on]
- Downstream Consumers: [Layers that depend on this]

## Configuration & Extensibility
How can this layer be customized for different user types?

## Out of Scope
What this layer explicitly does NOT handle

## Testing Requirements
- Unit test scenarios
- Integration test scenarios
```

**Level of Detail:**
- Focus on interfaces and contracts between layers
- Components defined by inputs/outputs, not implementation
- Extensibility points explicitly called out
- Clear upstream/downstream relationships

**Handling Dependencies:**
- Strict layer ordering: Foundation --> Core --> Experience --> Polish
- Lower layers must be complete before upper layers begin
- Cross-layer integration tests at each boundary

### 3.3 Prioritization Framework

**Layer Sequencing for Release 1:**

```
Layer 4: Polish        [P2] Animations, micro-interactions, delight
    ^
Layer 3: Experience    [P1] User-type-specific screens and flows
    ^
Layer 2: Core          [P0] Shared UI components, state management
    ^
Layer 1: Foundation    [P0] Design system, data models, dummy data
```

**MVP Criteria:**
- Foundation and Core are non-negotiable
- Experience layer can be reduced to single user type (Passerby)
- Polish layer is entirely deferrable

**Balancing Academic vs Hobbyist:**
- Foundation and Core serve both equally (50/50)
- Experience layer: Build Passerby first (hobbyist), Expert views second
- Polish layer: Prioritize whatever ships

### 3.4 Example PRD Outline

```
# Layer: Core - Tablet Interaction Components

## Meta
- Layer Level: Core
- Serves User Types: Passerby, Early Learner, Expert
- Priority: P0
- Status: Ready

## Layer Purpose
Provide reusable UI components for viewing and interacting with
cuneiform tablet images across all user experiences. These components
abstract the complexity of tablet display so that experience-layer
screens can focus on user-type-specific workflows.

## Capabilities Provided
| Capability | Description | Consumed By |
|------------|-------------|-------------|
| Tablet Display | Render tablet image with zoom/pan | All experience screens |
| Sign Highlighting | Overlay highlights on specific signs | Task cards, transcription UI |
| Context Panel | Show contextual information for selection | Early Learner, Expert views |
| Confidence Display | Visualize confidence levels | All transcription views |

## Success Metrics
- Technical: All components render in < 100ms
- Enablement: Experience layer can build screens without image handling logic

## Components

### Component 1: TabletViewer
**Purpose:** Display tablet image with standard interactions

**Interface:**
- Inputs:
  - tabletId: string
  - initialZoom: number (0.5 - 3.0)
  - highlightRegions: Region[] (optional)
- Outputs:
  - onRegionClick: (region: Region) => void
  - onZoomChange: (level: number) => void
- Events:
  - loaded: Fires when image renders
  - error: Fires on load failure

**Acceptance Criteria:**
- [ ] Supports pinch-to-zoom on touch devices
- [ ] Supports scroll-to-zoom on desktop
- [ ] Renders placeholder during load
- [ ] Displays error state with retry option
- [ ] Highlight regions pulse subtly to draw attention

### Component 2: SignCard
**Purpose:** Display isolated sign with selection options

**Interface:**
- Inputs:
  - signImage: ImageData
  - options: SignOption[]
  - allowSkip: boolean
- Outputs:
  - onSelect: (option: SignOption) => void
  - onSkip: () => void

**Acceptance Criteria:**
- [ ] Sign image maintains aspect ratio
- [ ] Options display in 2x2 grid for 4 options
- [ ] Options display in row for 2-3 options
- [ ] Selected state visually distinct
- [ ] Skip button positioned consistently

### Component 3: ConfidenceMeter
**Purpose:** Visualize confidence level for a transcription element

**Interface:**
- Inputs:
  - level: number (0-100)
  - variant: 'compact' | 'detailed'
- Outputs: None (display only)

**Acceptance Criteria:**
- [ ] Compact variant shows colored dot only
- [ ] Detailed variant shows percentage + label
- [ ] Color scale: Red (<40) / Yellow (40-70) / Green (>70)
- [ ] Accessible to colorblind users (includes pattern)

### Component 4: ContextPanel
**Purpose:** Display contextual information for selected element

**Interface:**
- Inputs:
  - contextType: 'sign' | 'word' | 'line' | 'tablet'
  - contextId: string
- Outputs:
  - onNavigate: (targetId: string) => void

**Acceptance Criteria:**
- [ ] Loads appropriate data based on context type
- [ ] Shows loading skeleton during fetch
- [ ] Displays "No data available" gracefully
- [ ] Links to related contexts are navigable

## Integration Points
- Upstream Dependencies:
  - Foundation: Design System (colors, typography, spacing)
  - Foundation: Dummy Data Schema
- Downstream Consumers:
  - Experience: Passerby Task Screen
  - Experience: Early Learner Transcription Screen
  - Experience: Expert Review Screen

## Configuration & Extensibility
- TabletViewer accepts custom highlight colors per region
- SignCard options can include confidence scores
- ContextPanel content is user-type-aware (simpler for Passerby)

## Out of Scope
- Drawing or annotation tools (Phase 2+)
- Collaborative cursors (Phase 2+)
- Real image processing (using pre-cropped dummy data)

## Testing Requirements
- Unit: Each component renders with minimal props
- Unit: Each component handles null/empty gracefully
- Integration: TabletViewer + SignCard selection flow
- Integration: TabletViewer + ContextPanel navigation
- Visual: Snapshot tests for all states
```

### 3.5 Pros & Cons

**Pros:**
- Maximizes code reuse across user types
- Clear separation of concerns for specialist agents
- Stable foundations reduce downstream rework
- Natural technical architecture alignment
- Scales well as product grows

**Cons:**
- Requires upfront architectural decisions
- Risk of over-engineering shared components
- User experience coherence harder to validate until late
- Dependencies create strict sequencing (less parallelization)
- May not surface user-facing issues until Experience layer

**Best When:**
- Technical architecture is a key concern
- Multiple user types share significant functionality
- Long-term scalability is important
- Team includes specialist agents (design system, components, etc.)

---

## Recommendation

[@Claude this recommendation sounds good, let's go with it.]

**Selected Approach: Hybrid - User Journey Flows (Primary) + Capability Layers (Secondary)**

### Rationale

For Glintstone Release 1, I recommend a hybrid approach that uses **User Journey Flows as the primary organizing structure** while extracting **Capability Layers for shared components**.

**Why User Journey Flows as Primary:**

1. **Demo-centric Release** - Release 1 is explicitly about making the vision "believable and enticing." UJF ensures we're building complete, demo-able experiences rather than disconnected features.

2. **Three Distinct User Tiers** - The wireframes already define Passerby, Early Learner, and Expert as distinct journeys. This organizational structure is already validated.

3. **Context Preservation** - AI agents implementing journeys will have full context about user goals, emotional states, and success criteria, reducing implementation drift.

4. **Stakeholder Communication** - Journey-based PRDs are easier for non-technical stakeholders to review and validate.

**Why Capability Layers as Secondary:**

1. **Shared Components** - The three journeys share significant UI components (TabletViewer, SignCard, ConfidenceMeter). Extracting these as a "Core Components" layer prevents redundant specifications.

2. **Foundation Requirements** - Design system, dummy data, and basic infrastructure need explicit specification regardless of journey structure.

3. **Agent Specialization** - The eng-frontend agent can work on component layers while ux-designer agents define journey specifics.

### Proposed PRD Hierarchy

```
LAYER PRDs (Build First)
------------------------
L1: Foundation - Design System & Tokens
L2: Foundation - Dummy Data Schema & Fixtures
L3: Core - Tablet Interaction Components
L4: Core - Task & Progress Components

JOURNEY PRDs (Build Second)
---------------------------
J1: Marketing Page Journey (All Users) [P0]
J2: Passerby First Contribution Journey [P0]
J3: Early Learner Onboarding Journey [P1]
J4: Expert Review Preview Journey [P1]
J5: CDLI Integration Demo Journey [P1]
```

### Implementation Sequence

| Week | Focus | PRDs Active |
|------|-------|-------------|
| 1 | Foundations | L1, L2 |
| 2 | Core Components | L3, L4 |
| 3 | Primary Journeys | J1, J2 |
| 4 | Secondary Journeys | J3, J4 |
| 5 | Integration & Polish | J5, Bug fixes |

### Success Criteria for This Approach

- [ ] Each journey PRD can be completed in < 1 week by assigned agents
- [ ] Shared components work identically across all journeys
- [ ] Demo script can walk through J1 --> J2 --> J4 in 10 minutes
- [ ] Stakeholders can review journey PRDs without technical background
- [ ] No journey has more than 2 upstream dependencies

---

## Next Steps

1. **Validate this approach** with project stakeholders
2. **Begin drafting Layer PRDs** (L1-L4) in parallel with UX strategy work
3. **Align with UX Architect** on journey definitions before writing Journey PRDs
4. **Establish PRD template files** in `/docs/prd/` directory
5. **Create dependency tracking mechanism** (simple table or kanban)

---

*This document is a living artifact. Updates will be made as the team aligns on approach and begins execution.*
