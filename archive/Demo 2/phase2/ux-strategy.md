# Glintstone UX Strategy

**Document Type:** Phase 2 Strategic Framework
**Author:** UX Architect Agent
**Date:** January 3, 2026
**Version:** 1.0
**Status:** Ready for Product Manager Review

---

## Executive Summary

This UX Strategy defines the foundational experience architecture for Glintstone, an AI-powered platform accelerating cuneiform transcription and translation. The strategy synthesizes insights from Phase 1 Discovery to establish interaction frameworks, information architecture, and design principles that will guide all subsequent product development.

**Core Strategic Insight:** Glintstone must serve as a trust-building bridge between two distinct user communities - academic Assyriologists who require rigorous scholarly standards and hobbyist volunteers who need immediate, rewarding engagement. The platform succeeds only if both communities perceive genuine value and neither feels the other's needs compromise their own.

**Key Design Imperatives:**
1. **Trust as the primary metric** - Every interaction must build or maintain user confidence in the platform's scholarly integrity
2. **Progressive complexity** - Users encounter only the complexity they need at their current skill level
3. **Visible impact** - Contributions must feel concrete, traceable, and meaningful
4. **Ecosystem integration** - The platform enhances rather than disrupts existing academic workflows

---

## 1. Key Interaction Frameworks

The following frameworks define the fundamental interaction paradigms that govern the Glintstone experience across all user tiers.

### 1.1 Progressive Disclosure Model

**Framework Definition:** Information and functionality are revealed incrementally based on user context, skill level, and current task focus. Users are never confronted with the full complexity of the system until they actively seek it.

```
DISCLOSURE LEVELS
=================

Level 0: SURFACE
├── Marketing messaging
├── High-level impact statistics
├── "Try it now" entry point
└── Zero prerequisite knowledge required

Level 1: ENGAGEMENT
├── First contribution experience
├── Basic task instructions
├── Immediate feedback loops
└── Progress indicators

Level 2: UNDERSTANDING
├── Cuneiform basics curriculum
├── Sign learning modules
├── Contribution context explanations
└── AI confidence explanations

Level 3: COMPETENCE
├── Full transcription interface
├── Translation assistance tools
├── Cross-reference features
└── Contribution history and portfolio

Level 4: EXPERTISE
├── Review and approval workflows
├── Disagreement resolution tools
├── Publication pipeline access
├── Mentorship capabilities
```

**Application by User Tier:**

| Tier | Entry Level | Maximum Level | Transition Triggers |
|------|-------------|---------------|---------------------|
| Passerby | 0 | 1 | None required - immediate access |
| Early Learner | 1 | 3 | Curriculum completion, contribution volume |
| Expert | 3 | 4 | Credential verification, peer endorsement |

**Design Implications:**
- Default interfaces must be stripped to essential actions
- "Learn more" and "Show details" must be consistently available but never mandatory
- Advanced features use consistent "expansion" patterns (accordions, slide-outs, drill-downs)
- Context-sensitive help appears proactively at moments of likely confusion

---

### 1.2 Contextual Authority Model

**Framework Definition:** Different interface elements carry different levels of authority based on their source (AI, crowdsourced, expert-verified). Authority is always visible and impacts how content is presented and what actions are available.

```
AUTHORITY HIERARCHY
===================

PROPOSED
├── Source: AI-generated or single contributor
├── Visual: Dashed borders, muted colors, question mark iconography
├── Actions: Edit, Suggest Alternative, Flag for Review
└── Status: Awaiting validation

UNDER REVIEW
├── Source: Multiple contributors, awaiting expert review
├── Visual: Solid borders, active colors, clock iconography
├── Actions: Add Supporting Evidence, View Discussion
└── Status: Consensus building

PROVISIONALLY ACCEPTED
├── Source: One expert approval, awaiting second reviewer
├── Visual: Solid borders, confident colors, single checkmark
├── Actions: Request Re-review, View Rationale
└── Status: Expert-validated pending confirmation

ACCEPTED
├── Source: Multiple expert approval or collation
├── Visual: Bold borders, confident colors, double checkmark
├── Actions: Cite, Export, View Full History
└── Status: Canonical

DISPUTED
├── Source: Experts disagree
├── Visual: Split presentation, debate iconography
├── Actions: View Positions, Add Position, Vote (experts only)
└── Status: Multiple valid interpretations

SUPERSEDED
├── Source: Previously accepted, now revised
├── Visual: Struck-through, historical styling
├── Actions: View History, View Replacement
└── Status: Archived with rationale
```

**Visual Language Requirements:**
- Authority level must be perceivable at a glance without reading
- Color coding must be colorblind-accessible (use patterns, icons, and position in addition to color)
- Confidence percentages are reserved for experts; others see qualitative labels
- Transitions between states are animated to draw attention to status changes

---

### 1.3 Contribution-Reward Cycle

**Framework Definition:** Every user contribution triggers an immediate feedback response that confirms value, provides context, and invites continued engagement. The cycle is calibrated to the user's tier.

```
CONTRIBUTION-REWARD CYCLE
=========================

         +-----------------+
         |   CONTRIBUTE    |
         |(Task Completion)|
         +--------+--------+
                  |
                  v
         +--------+--------+
         |    VALIDATE     |
         | (System Check)  |
         +--------+--------+
                  |
    +-------------+-------------+
    |             |             |
    v             v             v
+---+---+   +-----+-----+   +---+---+
|CONFIRM|   |  EDUCATE  |   |REWARD |
|(You   |   |(Why this  |   |(Impact|
| did   |   | matters)  |   | shown)|
| it!)  |   |           |   |       |
+---+---+   +-----+-----+   +---+---+
    |             |             |
    +-------------+-------------+
                  |
                  v
         +--------+--------+
         |    CONTINUE     |
         | (Next Action)   |
         +-----------------+
```

**Tier-Specific Calibration:**

**Passerby Cycle (30-60 seconds):**
- CONTRIBUTE: Binary or multiple-choice task
- VALIDATE: Instant (no waiting for consensus)
- CONFIRM: Animated success state
- EDUCATE: Optional "Did you know?" fact (max 15 words)
- REWARD: Counter increment, progress bar fill
- CONTINUE: Next task loads automatically with skip option

**Early Learner Cycle (2-5 minutes):**
- CONTRIBUTE: Transcription segment or translation attempt
- VALIDATE: Comparison with AI suggestion or parallel contributors
- CONFIRM: Match/divergence feedback with explanation
- EDUCATE: Relevant vocabulary, grammar, or historical context
- REWARD: Skill progress, tablet completion percentage
- CONTINUE: Choice of next task or review of work

**Expert Cycle (Variable, 5-30 minutes):**
- CONTRIBUTE: Review and verdict on pending items
- VALIDATE: Conflict check against other expert reviews
- CONFIRM: Status transition notification
- EDUCATE: N/A (experts provide, not receive)
- REWARD: Review count, influence metrics, citation potential
- CONTINUE: Queue of pending items with priority sorting

---

### 1.4 Guided Discovery Pattern

**Framework Definition:** Users exploring unfamiliar content or features receive contextual guidance that explains without interrupting, teaches without testing, and reveals without overwhelming.

**Pattern Components:**

1. **Beacon:** Subtle visual indicator that additional guidance is available (pulsing dot, highlighted affordance)

2. **Tooltip First:** Hover/focus reveals brief explanation (max 8 words)

3. **Popover Second:** Click/tap expands to fuller context (max 50 words) with optional actions

4. **Deep Dive Third:** Link to dedicated learning content for those who want comprehensive understanding

**Application Examples:**

| Element | Tooltip | Popover | Deep Dive |
|---------|---------|---------|-----------|
| Confidence meter | "AI certainty level" | "Higher confidence means the AI found more matching patterns. Experts verify all readings." | Curriculum module on AI methodology |
| Sign variant | "This sign has forms" | "Cuneiform signs changed over 3,000 years. This shows the form used in this tablet's period." | Sign evolution interactive explorer |
| Status badge | "Expert verified" | "Two Assyriology specialists have confirmed this reading. Click to see their notes." | Peer review process explanation |

---

### 1.5 Handoff Transparency Pattern

**Framework Definition:** When work transitions between user tiers (Passerby to Early Learner, Early Learner to Expert, or reverse), the transition is visible, explained, and credited to all participants.

```
HANDOFF VISUALIZATION
=====================

PASSERBY WORK                    EARLY LEARNER WORK               EXPERT WORK
+---------------+                +------------------+              +----------------+
| 47 sign       |   Aggregated   | Draft            |   Submitted  | Final          |
| matches       | -----------→   | Transcription    | ----------→  | Verified       |
| from 12       |                | with confidence  |              | Edition        |
| contributors  |                | scores           |              |                |
+---------------+                +------------------+              +----------------+
       |                                |                                |
       v                                v                                v
  [Credited as                    [Credited as                    [Credited as
   "Community                      "Contributor                    "Verified by
   Validation"]                    Name, Date"]                    Expert Name"]
```

**Design Requirements:**
- Every piece of content shows its provenance journey
- Contributors can see where their work was used and by whom
- Experts see the full contribution chain when reviewing
- No work disappears - even rejected contributions remain in history with explanation

---

## 2. Key Workflows

The following workflows map the primary user journeys, identifying critical paths, decision points, and friction areas requiring design attention.

### 2.1 Workflow Overview by Tier

```
PASSERBY WORKFLOWS
==================
W-P1: First Contribution (Critical Path - Marketing → Task → Completion)
W-P2: Return Session (Quick start without re-onboarding)
W-P3: Tier Upgrade Prompt (Invitation to become Early Learner)

EARLY LEARNER WORKFLOWS
=======================
W-E1: Curriculum Engagement (Sign learning, vocabulary building)
W-E2: Guided Transcription (AI-assisted transcription with scaffolding)
W-E3: Translation Attempt (First translation with heavy support)
W-E4: Portfolio Review (Seeing personal contribution history)
W-E5: Skill Assessment (Demonstrating competency for privileges)

EXPERT WORKFLOWS
================
W-X1: Review Queue Processing (Approving/rejecting pending work)
W-X2: Disagreement Resolution (Handling conflicting expert opinions)
W-X3: Original Transcription (Working with unpublished tablets)
W-X4: Publication Export (Preparing work for external publication)
W-X5: Mentorship (Guiding Early Learners through difficult tasks)

CROSS-TIER WORKFLOWS
====================
W-C1: Tablet Journey (Following a single tablet from first touch to publication)
W-C2: Search and Discovery (Finding specific content across the archive)
W-C3: Citation and Attribution (Citing platform content externally)
```

---

### 2.2 Critical Path: Passerby First Contribution (W-P1)

This workflow is the most critical for platform growth and must be optimized for minimal friction and maximum reward.

```
START                                                            END
  |                                                               |
  v                                                               v
+----------+     +----------+     +----------+     +----------+  +---------+
| LANDING  | --> | ENTRY    | --> | TUTORIAL | --> | FIRST    |->| SESSION |
| PAGE     |     | DECISION |     | (15 sec) |     | TASK     |  | SUMMARY |
+----------+     +----------+     +----------+     +----------+  +---------+
                      |                                |              |
                      v                                v              v
                 [CTA Click]                     [Task Loop      [Call to
                 No account                       x5-10]          Action]
                 required
```

**Critical Decision Points:**

| Point | User Question | Design Response |
|-------|---------------|-----------------|
| Landing → Entry | "Is this for me?" | Show immediate value prop + low-barrier CTA |
| Entry → Tutorial | "How long will this take?" | Show "2 minutes to first contribution" |
| Tutorial → Task | "Can I do this?" | Guarantee success on first task |
| Task → Next Task | "Do I want to continue?" | Celebration + easy continuation |
| Session → Return | "Was this worthwhile?" | Summary with concrete impact shown |

**Friction Points to Address:**

1. **Page Load Time:** Hero image must render in < 1 second; tasks must not require heavy downloads
2. **Account Prompt:** Must appear only AFTER value is demonstrated, never before
3. **Task Ambiguity:** First tasks must have obvious "right" answers
4. **Abandonment Recovery:** Session state must survive refresh/navigation

---

### 2.3 Critical Path: Expert Review Queue (W-X1)

This workflow is critical for platform credibility and must be optimized for expert efficiency and decision quality.

```
START                                                                       END
  |                                                                          |
  v                                                                          v
+----------+     +----------+     +----------+     +----------+     +--------+
| QUEUE    | --> | ITEM     | --> | EVIDENCE | --> | VERDICT  | --> | NEXT   |
| VIEW     |     | DETAIL   |     | REVIEW   |     | ENTRY    |     | ITEM   |
+----------+     +----------+     +----------+     +----------+     +--------+
     |                |                |                |
     v                v                v                v
 [Priority        [Tablet           [AI output       [Accept/
  sorting,         image +           + crowd          Reject/
  filtering]       context]          consensus]       Dispute]
```

**Expert Efficiency Requirements:**

1. **Queue Intelligence:**
   - Items sorted by priority (age, contributor confidence, near-consensus)
   - Filter by period, genre, language specialty
   - Batch actions for similar items
   - "Return later" option without losing place

2. **Review Interface:**
   - Side-by-side: tablet image | proposed reading | alternatives
   - One-click accept for high-confidence, high-agreement items
   - Rich editing for corrections with tracked changes
   - Access to reference tools without leaving context (dictionaries, parallels)

3. **Verdict Recording:**
   - Quick verdicts: Accept, Reject, Request More Evidence, Flag for Colleague
   - Detailed verdicts: Correction entry with rationale
   - Dispute initiation: Formal disagreement with structured argumentation

---

### 2.4 Critical Path: Tablet Journey (W-C1)

This cross-tier workflow shows how a single tablet progresses from initial digitization to published edition, with Glintstone accelerating each stage.

```
TABLET LIFECYCLE
================

STAGE 1: CATALOG ENTRY
+------------------+
| CDLI Import      |  System receives catalog metadata and images
| (Automated)      |  No user action required
+--------+---------+
         |
         v
STAGE 2: PREPARATION
+------------------+
| Passerby Tasks   |  Line segmentation, damage marking, orientation
| (Crowdsourced)   |  High volume, low expertise required
+--------+---------+
         |
         v
STAGE 3: DRAFT TRANSCRIPTION
+------------------+
| AI + Early       |  AI proposes readings, learners verify/correct
| Learners         |  Multiple contributors, confidence aggregation
+--------+---------+
         |
         v
STAGE 4: EXPERT REVIEW
+------------------+
| Expert Queue     |  Specialist reviews, approves, or corrects
| (Specialist)     |  Status transitions to "Provisionally Accepted"
+--------+---------+
         |
         v
STAGE 5: CONSENSUS
+------------------+
| Second Expert    |  Independent verification
| Review           |  Status transitions to "Accepted"
+--------+---------+
         |
         v
STAGE 6: TRANSLATION
+------------------+
| AI + Early       |  AI proposes translation, learners refine
| Learners +       |  Expert reviews for publication quality
| Experts          |
+--------+---------+
         |
         v
STAGE 7: PUBLICATION
+------------------+
| Export +         |  ATF export to ORACC, citation generation
| Attribution      |  All contributors credited
+------------------+
```

**Design Requirements for Tablet Journey:**

- **Progress Visibility:** Any user viewing a tablet can see its current lifecycle stage
- **Contribution Mapping:** Each stage shows who contributed what
- **Stage Transitions:** Notifications to relevant users when stages advance
- **Bottleneck Alerts:** System identifies tablets stalled at any stage

---

## 3. Information Architecture

### 3.1 Content Hierarchy

```
GLINTSTONE CONTENT STRUCTURE
============================

LEVEL 0: PLATFORM
├── Marketing/Public Layer
└── Application Layer

LEVEL 1: APPLICATION CORE
├── CONTRIBUTE (Task-focused interfaces)
│   ├── Passerby Tasks
│   ├── Transcription Workspace
│   └── Translation Workspace
│
├── EXPLORE (Discovery-focused interfaces)
│   ├── Tablet Archive
│   ├── Search
│   └── Featured Discoveries
│
├── LEARN (Education-focused interfaces)
│   ├── Curriculum Modules
│   ├── Sign Library
│   └── Practice Area
│
├── REVIEW (Expert-focused interfaces)
│   ├── Review Queue
│   ├── Dispute Resolution
│   └── Publication Pipeline
│
└── PROFILE (User-focused interfaces)
    ├── Contribution History
    ├── Skills & Progress
    └── Settings

LEVEL 2: CONTENT TYPES
├── TABLETS (Primary objects)
│   ├── Metadata (period, provenance, genre, museum)
│   ├── Images (multiple angles, RTI if available)
│   ├── Transcription (versioned, with status)
│   ├── Translation (versioned, with status)
│   └── Commentary (expert notes, contextual info)
│
├── SIGNS (Cuneiform vocabulary)
│   ├── Visual forms (period variants)
│   ├── Readings (phonetic values)
│   ├── Meanings (logographic values)
│   └── Attestations (tablet references)
│
├── PEOPLE (Historical figures)
│   ├── Names (cuneiform + normalized)
│   ├── Roles (king, scribe, merchant, etc.)
│   └── Attestations (tablet references)
│
└── TASKS (Work units)
    ├── Micro-tasks (binary/choice)
    ├── Transcription segments
    ├── Translation units
    └── Review items
```

---

### 3.2 Navigation Model

**Primary Navigation (Persistent Header)**

```
+------------------------------------------------------------------+
| [Logo]   Contribute   Explore   Learn   [Search]   [Profile/Auth]|
+------------------------------------------------------------------+
```

**Tier-Specific Views:**

| Nav Item | Passerby | Early Learner | Expert |
|----------|----------|---------------|--------|
| Contribute | Quick tasks | Task queue + Transcription workspace | + Review queue |
| Explore | Featured tablets | Full archive search | + Publication pipeline |
| Learn | "Coming soon" teaser | Full curriculum | "Teach" mode (mentorship) |
| Profile | None (anonymous) | Basic profile | Full professional profile |

**Secondary Navigation (Context-Dependent Sidebar)**

Within each primary section, a left sidebar provides:
- Section-specific navigation
- Quick filters and sorting
- Progress indicators
- Related actions

**Tertiary Navigation (In-Content)**

Within content (e.g., tablet view), tabbed interfaces provide:
- Image view / Transcription view / Translation view / Context view
- Version history / Discussion / Contributors

---

### 3.3 Search and Discovery

**Search Interface Hierarchy:**

```
SEARCH LEVELS
=============

LEVEL 1: GLOBAL SEARCH (Header bar)
├── Type: Quick text search across all content
├── Results: Categorized by content type (Tablets, Signs, People)
└── Filters: Post-search refinement available

LEVEL 2: FACETED SEARCH (Explore section)
├── Type: Multi-dimensional filtering
├── Facets: Period, Language, Genre, Museum, Status
└── Results: List/grid with preview cards

LEVEL 3: SPECIALIZED SEARCH (Expert tools)
├── Type: Sign sequence search, prosopography search
├── Syntax: Supports ATF-like queries for experts
└── Results: Detailed matches with context
```

**Discovery Without Search:**

- **Featured Tablets:** Curated selection on Explore landing page
- **Recent Discoveries:** Tablets recently reaching "Accepted" status
- **Personal Recommendations:** "Based on your contributions" suggestions
- **Random Encounter:** "Explore a random tablet" for serendipity

---

### 3.4 URL Structure

```
URL ARCHITECTURE
================

/                           Marketing landing page
/app                        Application entry (redirects based on auth)
/app/contribute             Contribution hub
/app/contribute/quick       Passerby quick tasks
/app/contribute/transcribe  Transcription workspace
/app/contribute/translate   Translation workspace
/app/explore                Archive exploration
/app/explore/tablets        Tablet listing with filters
/app/explore/tablets/:id    Individual tablet view
/app/explore/signs          Sign library
/app/explore/signs/:id      Individual sign page
/app/learn                  Curriculum hub
/app/learn/modules/:id      Individual learning module
/app/review                 Expert review hub (authenticated experts only)
/app/review/queue           Review queue
/app/profile                User profile
/app/profile/contributions  Contribution history
/app/profile/skills         Skills and progress
```

---

## 4. System Model

The system model defines how users understand what Glintstone is, what it does, and how their actions produce results. This conceptual model must align with user mental models to reduce cognitive load and prevent confusion.

### 4.1 Core Metaphor: The Collaborative Archive

Glintstone is conceptualized as a **collaborative archive** where:
- **Tablets are artifacts** waiting to be understood
- **Users are contributors** who help decode artifacts
- **AI is an assistant** that proposes ideas but never decides
- **Experts are curators** who validate and preserve knowledge
- **Progress is visible** as artifacts move from mystery to knowledge

This metaphor was chosen over alternatives for specific reasons:

| Alternative Metaphor | Why Rejected |
|---------------------|--------------|
| Game/Quest | Risk of trivializing scholarly work; academics may disengage |
| Social Network | Contribution, not connection, is the core value |
| Classroom | Too hierarchical; experts are peers, not teachers |
| Laboratory | Too clinical; misses the humanistic dimension |
| Factory/Pipeline | Dehumanizing; obscures individual contribution value |

### 4.2 User Mental Model Mapping

**What Users Need to Understand:**

1. **The Problem:** Millions of tablets exist; almost none are translated
2. **The Opportunity:** Everyone can help, regardless of expertise
3. **The Process:** Small contributions aggregate into complete translations
4. **The Validation:** Experts verify everything before it becomes "official"
5. **The Impact:** Verified translations unlock humanity's oldest stories

**Common Mental Model Gaps to Address:**

| Gap | User Might Think | System Should Clarify |
|-----|------------------|----------------------|
| AI accuracy | "The AI knows the answer" | "AI proposes, humans verify" |
| Contribution value | "My guess doesn't matter" | "Your input trains the system and flags uncertainty" |
| Expert authority | "Experts are always right" | "Experts disagree; that's normal and valuable" |
| Progress speed | "This tablet will be done soon" | "Some tablets take years across many contributors" |
| Ownership | "I translated this tablet" | "You contributed to this tablet's translation" |

### 4.3 Confidence Model

Users must understand how confidence works without needing statistical literacy.

**User-Facing Confidence Language:**

| Technical Level | User Language | Visual Treatment |
|-----------------|---------------|------------------|
| 0-20% | "Uncertain" | Red/dotted, question mark |
| 21-50% | "Possible" | Orange/dashed, tilde |
| 51-75% | "Likely" | Yellow/light solid, single check |
| 76-90% | "Confident" | Green/solid, double check |
| 91-100% | "Verified" | Bold green, shield icon |

**Confidence Explanations (Progressive Disclosure):**

- **Tooltip:** "AI confidence: Likely"
- **Popover:** "The AI matched this to similar signs with 68% confidence. 4 volunteers agreed with this reading."
- **Deep Dive:** Link to explanation of confidence scoring methodology

---

## 5. Ecosystem Integration Model

Glintstone does not exist in isolation. It must integrate respectfully with the existing academic infrastructure, particularly CDLI and ORACC.

### 5.1 Integration Principles

1. **Enhancement, Not Replacement:** Glintstone accelerates work that flows through existing channels
2. **Data Portability:** All Glintstone work can be exported in standard formats
3. **Identity Preservation:** CDLI P-numbers remain the primary identifiers
4. **Attribution Clarity:** Glintstone contributions are clearly marked as such

### 5.2 CDLI Integration Model

```
CDLI INTEGRATION ARCHITECTURE
=============================

CDLI DATABASE                         GLINTSTONE
+----------------+                    +----------------+
| Catalog        | ---- Import ---->  | Artifact       |
| Metadata       |                    | Registry       |
+----------------+                    +----------------+
| Images         | ---- Import ---->  | Image Store    |
|                |                    | (cached copy)  |
+----------------+                    +----------------+
| P-Numbers      | <--- Sync --->     | Primary Keys   |
+----------------+                    +----------------+
                                      | Transcriptions |
                                      | Translations   |
                                      | Contributions  |
                                      +-------+--------+
                                              |
                                              | Export (ATF format)
                                              v
                                      +----------------+
                                      | Back to CDLI   |
                                      | or ORACC       |
                                      +----------------+
```

**User-Facing Integration Touchpoints:**

- **Tablet View Header:** "This tablet is cataloged as [P-number] in CDLI" with link
- **Export Options:** "Export transcription as ATF" with CDLI/ORACC compatibility
- **Import Option:** "Don't see a tablet? Request import from CDLI"

### 5.3 ORACC Integration Model

```
ORACC INTEGRATION ARCHITECTURE
==============================

ORACC PROJECTS                        GLINTSTONE
+----------------+                    +----------------+
| Lemmatization  | ---- Import ---->  | Dictionary     |
| Glossaries     |                    | Support        |
+----------------+                    +----------------+
| Published      | ---- Import ---->  | Reference      |
| Editions       |                    | Corpus         |
+----------------+                    +----------------+
                                      | New Work       |
                                      +-------+--------+
                                              |
                                              | Export (ATF + Lem)
                                              v
                                      +----------------+
                                      | To ORACC       |
                                      | Project        |
                                      +----------------+
```

**Export Workflow:**

1. Expert marks tablet as "Ready for Publication"
2. System generates ATF file with full attribution
3. Expert can copy/download for submission to ORACC project
4. System tracks which tablets have been submitted externally

---

## 6. Educational Guidance UX Approach

Education is not a separate mode but is woven throughout the experience. Learning happens through doing, with explicit teaching modules available for those who want structured progression.

### 6.1 Learning Philosophy

**Core Principles:**

1. **Learn by Contributing:** The best learning happens through authentic tasks
2. **Just-in-Time, Not Just-in-Case:** Information appears when needed, not before
3. **Scaffolded Complexity:** Early tasks require less knowledge; complexity increases with competency
4. **Failure is Data:** Wrong answers help the system and teach the user
5. **Celebrate Progress:** Every advancement is acknowledged

### 6.2 Learning Moments in Contribution Flow

| Moment | Trigger | Educational Content |
|--------|---------|---------------------|
| First task | New session start | Animated orientation (15 sec, skippable) |
| Wrong answer | Significant divergence from consensus | "Most people saw this differently. Here's why..." |
| Right answer | Match with expert reading | "Great eye! This sign is [name] and means [meaning]" |
| Unfamiliar sign | User hovers/pauses on element | Contextual sign information tooltip |
| Task completion | Session milestone (5, 10, 25 tasks) | "You've now seen [X] different signs. Want to learn their names?" |
| Difficult task | AI confidence below 50% | "This one is tricky! Even experts disagree sometimes." |

### 6.3 Structured Curriculum (Early Learner)

**Curriculum Architecture:**

```
LEARNING PATHWAY
================

MODULE 1: FOUNDATIONS (2-3 hours)
├── What is cuneiform?
├── How to read wedges
├── Number systems
├── Determinatives
└── Practice: Number reading tasks

MODULE 2: BASIC SIGNS (5-10 hours)
├── 25 high-frequency signs
├── Sign variants across periods
├── Logographic vs. syllabic use
└── Practice: Sign identification tasks

MODULE 3: READING WORDS (5-10 hours)
├── Basic Sumerian vocabulary
├── Basic Akkadian vocabulary
├── Name recognition patterns
└── Practice: Word completion tasks

MODULE 4: READING LINES (10-20 hours)
├── Administrative text formulas
├── Letter opening/closing patterns
├── Date formula recognition
└── Practice: Line transcription tasks

MODULE 5: BASIC TRANSLATION (10-20 hours)
├── Grammar essentials (Sumerian)
├── Grammar essentials (Akkadian)
├── Dictionary use
└── Practice: Formulaic text translation
```

**Curriculum UX Patterns:**

- **Module Landing Page:** Overview, estimated time, prerequisites
- **Lesson Format:** Short reading (2-3 paragraphs) + interactive exercise + quiz
- **Progress Tracking:** Visual module map with completion states
- **Integration:** "Apply this" links to real contribution tasks that use the skill

### 6.4 Gamification Boundaries

**What We Do:**
- Achievement badges for meaningful milestones (100 contributions, first accepted reading)
- Progress bars and completion percentages
- Session statistics ("You helped with 3 tablets today")
- Streak acknowledgment ("5 days in a row!")

**What We Do Not Do:**
- Leaderboards (competition discourages collaborative spirit)
- Points or currency (reduces intrinsic motivation)
- Punitive streaks (no "you lost your streak" shame)
- Arbitrary levels (progression must reflect real competency)

---

## 7. Interaction Surface Layers

The platform is organized into distinct interaction layers, each with its own purpose, complexity level, and user expectations.

### 7.1 Layer Definitions

```
INTERACTION LAYERS
==================

LAYER 4: CONFIGURATION
+----------------------------------------------------------+
| Account settings, notification preferences, privacy      |
| controls, integration settings, export options           |
| Accessed: Infrequently | Complexity: Medium              |
+----------------------------------------------------------+
                         ^
                         |
LAYER 3: POWER/EXPERT TOOLS
+----------------------------------------------------------+
| Review queues, publication pipeline, advanced search,    |
| disagreement resolution, batch operations, mentorship    |
| Accessed: Frequently (experts) | Complexity: High        |
+----------------------------------------------------------+
                         ^
                         |
LAYER 2: CORE FUNCTIONALITY
+----------------------------------------------------------+
| Transcription workspace, translation interface, tablet   |
| viewer, curriculum, contribution history, sign library   |
| Accessed: Frequently (learners) | Complexity: Medium     |
+----------------------------------------------------------+
                         ^
                         |
LAYER 1: ENGAGEMENT SURFACE
+----------------------------------------------------------+
| Quick tasks, session progress, immediate feedback,       |
| basic exploration, featured content                      |
| Accessed: Always (all users) | Complexity: Low           |
+----------------------------------------------------------+
                         ^
                         |
LAYER 0: DISCOVERY/MARKETING
+----------------------------------------------------------+
| Landing page, value proposition, social proof,           |
| anonymous entry points, public metrics                   |
| Accessed: Once (new users) | Complexity: Minimal         |
+----------------------------------------------------------+
```

### 7.2 Layer Transition Patterns

**Upward Transitions (Accessing More Complexity):**
- Triggered by user intent (clicking "More options", "Advanced", etc.)
- Always reversible (easy path back to simpler view)
- Cognitive loading warning for major transitions ("This will show more options")

**Downward Transitions (Simplifying):**
- "Simplified view" always available in complex interfaces
- Session can be started from any layer and will return to appropriate layer
- "I'm a beginner" escape hatch from overwhelming interfaces

### 7.3 Cross-Layer Elements

**Persistent Across All Layers:**
- Global navigation header
- Notification indicator
- Help access
- User identity (when authenticated)

**Contextual Across Layers:**
- Breadcrumb navigation (Layers 2-4)
- Tool palette (Layers 2-3)
- Progress indicators (Layers 1-2)

---

## 8. Principles and Guardrails

### 8.1 Design Principles

These principles should guide every design decision. They are ordered by priority in cases of conflict.

**P1: Trust Over Speed**
> When a design choice improves efficiency but risks undermining user trust in platform accuracy, choose trust.

*Example Application:* AI suggestions should always show confidence levels even if this slows task completion, because users must understand the preliminary nature of AI output.

**P2: Respect Expertise Hierarchy Without Creating Barriers**
> The platform acknowledges that some users know more than others, but never uses expertise as a gatekeeping mechanism.

*Example Application:* Passersby can see expert discussions and rationale even if they cannot participate, because transparency builds trust.

**P3: Show the Work**
> Every piece of content should be traceable to its contributors and the process that created it.

*Example Application:* The tablet view always shows contribution history, even when it adds interface complexity, because provenance is non-negotiable for academic credibility.

**P4: Reward Honest Uncertainty**
> Users who admit they do not know should be valued as highly as users who provide correct answers.

*Example Application:* "I'm not sure" is always an option and triggers specific messaging: "Flagging uncertainty helps us focus expert attention. Thank you!"

**P5: Progressive Complexity, Not Mandatory Simplicity**
> Simple is the default, but complexity must be accessible for those who need it.

*Example Application:* The default transcription view shows clean text, but "Show technical notation" reveals ATF formatting for those who need it.

**P6: Integrate, Don't Isolate**
> Glintstone should make it easy to work with external tools and databases, never creating lock-in.

*Example Application:* Every export function produces standard formats (ATF, CSV, JSON) without Glintstone-specific requirements.

**P7: Celebrate Contribution, Not Competition**
> Recognition should focus on collective progress and individual growth, never on ranking users against each other.

*Example Application:* Profile pages show personal statistics and contribution impact, never comparative rankings.

---

### 8.2 Design Guardrails

These guardrails define what we will NOT do, regardless of other considerations.

**G1: Never Present AI Output as Authoritative**
> AI-generated content must always be visually distinct from human-verified content and must never appear without confidence indicators.

**G2: Never Require Account Creation for First Value**
> Users must be able to experience the core value proposition (making a contribution) before any account prompt.

**G3: Never Use Dark Patterns for Engagement**
> No guilt messaging ("You'll lose your progress!"), no fake urgency, no hidden unsubscribe options.

**G4: Never Display Content Without Status**
> Every piece of transcription or translation must display its verification status. No ambiguous content.

**G5: Never Allow Expert Actions Without Attribution**
> Expert approvals, rejections, and corrections must be tied to identified individuals for accountability.

**G6: Never Gamify at the Expense of Accuracy**
> No incentives that reward speed over correctness, volume over quality, or agreement over honest assessment.

**G7: Never Remove Contribution History**
> Even rejected or superseded contributions remain visible in version history. No erasure of the work trail.

**G8: Never Block Access to Public Knowledge**
> Once a transcription reaches "Accepted" status, it should be publicly accessible. No paywalls for verified knowledge.

---

## 9. Strategic Directions for Workflow Structure

Based on the above frameworks, I present three strategic directions for how the platform's primary workflows could be structured. Each represents a coherent philosophy with distinct tradeoffs.

---

### Direction A: "Contribution Streams"

**Philosophy:** Organize the platform around parallel contribution streams, each optimized for a specific task type. Users choose their stream and work within it, with limited cross-stream navigation.

```
CONTRIBUTION STREAMS MODEL
==========================

STREAM 1: VISUAL TASKS
+----------------------------------+
| Sign matching, damage marking,   |
| line counting, orientation       |
| Target: Passerby, Early Learner  |
| Complexity: Low                  |
+----------------------------------+

STREAM 2: TRANSCRIPTION TASKS
+----------------------------------+
| Sign reading, word completion,   |
| line transcription               |
| Target: Early Learner            |
| Complexity: Medium               |
+----------------------------------+

STREAM 3: TRANSLATION TASKS
+----------------------------------+
| Word translation, clause         |
| translation, connected text      |
| Target: Early Learner (advanced) |
| Complexity: Medium-High          |
+----------------------------------+

STREAM 4: REVIEW TASKS
+----------------------------------+
| Verification, correction,        |
| dispute resolution               |
| Target: Expert                   |
| Complexity: High                 |
+----------------------------------+
```

**Key Strengths:**
- Maximum optimization for each task type
- Clear mental model: "I'm doing visual tasks today"
- Easy to parallelize development (each stream is independent)
- Suits users with limited, specific time slots

**Key Challenges:**
- Users may miss the "full picture" of tablet transcription
- Harder to show contribution impact across the tablet lifecycle
- Risk of streams feeling disconnected from each other
- May reduce understanding of how work flows to experts

**Ideal Use Cases:**
- High-volume passerby contribution (optimized micro-task flow)
- Expert review efficiency (focused review queue)
- Limited mobile sessions (single-purpose engagement)

**Tradeoffs:**
- Prioritizes efficiency over holistic understanding
- Prioritizes specialization over generalization
- Prioritizes throughput over connection

---

### Direction B: "Tablet-Centered Journeys"

**Philosophy:** Organize the platform around individual tablets as the primary navigation unit. Users explore tablets and contribute in context, seeing how their work fits the tablet's overall journey.

```
TABLET-CENTERED MODEL
=====================

TABLET VIEW (Primary Interface)
+----------------------------------+
| TABLET IMAGE    | CONTRIBUTION   |
| (Interactive)   | PANEL          |
|                 |                |
| [Zoom/Pan]      | [Current Task] |
| [Highlight]     | [Submit]       |
| [Compare]       | [Skip]         |
+----------------------------------+
| TABLET METADATA                  |
| Period | Provenance | Status     |
+----------------------------------+
| CONTRIBUTION HISTORY             |
| Timeline of all contributions    |
+----------------------------------+
| RELATED TABLETS                  |
| Similar texts, same archive, etc |
+----------------------------------+
```

**Key Strengths:**
- Deep context for every contribution
- Users see exact impact of their work on specific artifacts
- Supports the "collaborative archive" metaphor
- Natural for exploration and discovery
- Maintains connection between contribution types

**Key Challenges:**
- Context loading adds friction to quick tasks
- Less optimized for high-volume micro-contributions
- Tablet selection can create decision paralysis
- Harder to ensure even coverage across corpus

**Ideal Use Cases:**
- Early Learner transcription/translation work
- Expert review with full context
- Exploration-driven engagement
- Educational use (studying specific tablets)

**Tradeoffs:**
- Prioritizes context over efficiency
- Prioritizes understanding over throughput
- Prioritizes depth over breadth

---

### Direction C: "Adaptive Task Surfacing" (Recommended)

**Philosophy:** Organize the platform around an intelligent task queue that surfaces the right work to the right user at the right time, while maintaining optional access to tablet-centered exploration. The system adapts to user tier, skills, available time, and platform needs.

```
ADAPTIVE TASK MODEL
===================

ENTRY POINT: "WHAT SHOULD I DO?"
+----------------------------------+
| [Recommended Task]               |
| Based on: Skill level, time,     |
| platform needs, personal goals   |
+----------------------------------+
| [Task Options]                   |
| Quick (2 min) | Standard (10 min)|
| Deep (30 min+)                   |
+----------------------------------+
| [Or Explore]                     |
| Choose your own tablet/task      |
+----------------------------------+

TASK EXECUTION
+----------------------------------+
| [Context Panel] | [Task Panel]   |
| Relevant tablet | Current work   |
| info (collapsed | [Submit]       |
| by default)     | [Skip]         |
+----------------------------------+

POST-TASK
+----------------------------------+
| [Impact Summary]                 |
| What you did, how it helps       |
+----------------------------------+
| [Next Action]                    |
| Continue | Learn More | Explore  |
+----------------------------------+
```

**Key Strengths:**
- Balances efficiency with context
- Adapts to diverse user needs and time availability
- Platform can balance corpus coverage
- Supports both "I have 2 minutes" and "I have 2 hours" sessions
- Progressive disclosure of complexity
- Maintains agency (users can always choose their own path)

**Key Challenges:**
- Requires intelligent task recommendation system
- Must avoid feeling like an algorithm is controlling the user
- "Explore" path must be genuinely accessible, not hidden
- Recommendation transparency is essential for trust

**Ideal Use Cases:**
- All user tiers (adapts to each)
- Variable session lengths
- Platform growth phase (can direct attention to neglected areas)
- Returning users who want to just "jump in"

**Tradeoffs:**
- Requires more complex backend logic
- Must maintain "I choose" option alongside "recommend to me"
- Balance between platform needs and user preferences

---

### Strategic Recommendation

**I recommend Direction C: Adaptive Task Surfacing** as the primary organizational model for the following reasons:

1. **Serves All User Tiers:** Direction A is optimized for passersby but loses experts; Direction B is optimized for depth but loses casual contributors. Direction C adapts to each.

2. **Supports Key Metrics:** The brief emphasizes "contributions per hour" (needs efficiency) and "trust" (needs context). Direction C allows both by adapting the balance per user.

3. **Aligns with Progressive Disclosure:** The platform's core framework is progressive disclosure. Direction C embodies this by showing simple recommendations while maintaining access to complex exploration.

4. **Enables Platform Steering:** With millions of tablets, some will be neglected. Direction C allows the platform to gently guide attention without removing user agency.

5. **Scales with Complexity:** As the platform grows, new task types and contribution modes can be integrated into the recommendation system without restructuring the information architecture.

**Implementation for Release 1 (POC):**

For the POC, Direction C can be implemented in simplified form:
- Recommendation system uses simple rules (skill tier + random selection)
- "Explore" path is fully functional but secondary in prominence
- Context panel uses static dummy data
- Adaptive time-based options (Quick/Standard/Deep) are fixed categories

This establishes the interaction patterns that will scale to more sophisticated recommendation in later releases.

---

## 10. Release 1 Prioritization Summary

Based on this strategy, the following elements are critical for Release 1 (POC Demo):

### Must Have (P0)
- Progressive disclosure model implemented for Passerby tier
- Contextual authority model with visual status indicators
- Passerby first contribution workflow (W-P1) complete
- Basic tablet viewer with sign highlighting
- Contribution-reward cycle with immediate feedback
- "Stargazer's Script" visual identity applied throughout

### Should Have (P1)
- Early Learner curriculum landing page (content can be placeholder)
- Expert review queue mockup (functional UI, dummy data)
- Tablet journey visualization (showing lifecycle stages)
- Basic search within tablet archive
- CDLI integration demo (P-number linking, visual only)

### Could Have (P2)
- Cross-tier handoff visualization
- Sign library with learning content
- User profile with contribution history
- Guided discovery tooltips throughout

### Will Not Have (Deferred)
- Account creation and persistence
- Real AI integration (all proposals are pre-scripted)
- Export functionality
- Disagreement resolution workflow
- Mentorship features

---

## 11. Appendix: Glossary

| Term | Definition |
|------|------------|
| ATF | ASCII Transliteration Format - standard encoding for cuneiform texts |
| CDLI | Cuneiform Digital Library Initiative - primary digital repository |
| Collation | Physical examination of tablet to verify readings |
| Confidence | System's assessment of how likely a reading is correct |
| Contribution | Any user action that adds value to a tablet's transcription/translation |
| Determinative | Silent classifier sign in cuneiform |
| Expert | User with verified credentials and final approval authority |
| Early Learner | User engaged in curriculum with intermediate privileges |
| Logogram | Sign representing a complete word |
| ORACC | Open Richly Annotated Cuneiform Corpus - scholarly annotation platform |
| P-number | CDLI's unique identifier for cuneiform objects |
| Passerby | Anonymous or casual user performing simple tasks |
| Progressive Disclosure | Information architecture pattern revealing complexity gradually |
| Provenance | Origin and chain of custody for content |
| Status | Current verification level of content (Proposed, Under Review, Accepted, etc.) |
| Syllabogram | Sign representing a syllable |
| Tier | User classification based on expertise and platform privileges |
| Transcription | Conversion of cuneiform signs to Latin-alphabet representation |
| Translation | Rendering of ancient language text into modern language |

---

## 12. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | UX Architect Agent | Initial strategy document |

---

## 13. Approval and Next Steps

This UX Strategy requires review and approval from:
- [ ] Project Stakeholder
- [ ] Product Manager Agent
- [ ] Brand Visual Designer (for alignment with Stargazer's Script)
- [ ] Assyriology Academic Advisor (for workflow accuracy)

Upon approval, the Product Manager should proceed to create PRDs based on the hybrid User Journey Flows + Capability Layers approach defined in the PRD Structure Proposals, using this strategy as the foundational reference.

---

*This document establishes the strategic UX foundation for Glintstone. All subsequent design and development work should reference these frameworks, principles, and guardrails to ensure consistency and alignment with user needs.*
