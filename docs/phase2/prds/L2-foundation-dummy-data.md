# L2: Foundation - Dummy Data Schema and Fixtures

**Document Type:** Layer PRD
**Priority:** P0 (Critical Path)
**Status:** Ready
**Estimated Complexity:** M
**Dependencies:** L1 (Design System - for status color mapping)
**Assigned Agent:** eng-architect, eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| Layer Level | Foundation |
| Serves User Types | All (Passerby, Early Learner, Expert) |
| UX Strategy Reference | Section 3: Information Architecture; Section 1.2: Contextual Authority Model |
| Academic Reference | academic-workflow-report.md Section 3.4 (Status Taxonomy) |

---

## Layer Purpose

Define the data schemas and create fixture datasets that enable the Release 1 POC to demonstrate all user journeys with believable, realistic content. This layer provides the "dummy data" foundation that makes the platform feel real without requiring live integrations.

**Why This Matters for Release 1:**
- POC must be "believable, enticing, and a source for feedback" (Brief)
- All journeys require tablet data, user profiles, and contribution states
- Dummy data must demonstrate the full contribution-to-verification pipeline
- CDLI integration demo requires realistic P-number linking

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Coverage | All user journeys have sufficient dummy data | 100% |
| Realism | Data passes academic advisor review for plausibility | Yes |
| Volume | Sufficient tablets for 10-minute demo session | 20+ tablets |
| Variety | Multiple tablet types, periods, and states represented | Yes |

---

## Capabilities Provided

| Capability | Description | Consumed By |
|------------|-------------|-------------|
| Tablet Schema | Complete data model for cuneiform tablets | TabletViewer, Task system |
| Sign Schema | Data model for individual cuneiform signs | SignCard, Learning modules |
| User Schema | Contributor profiles with tier and stats | Profile, Attribution |
| Contribution Schema | Individual contribution records | Progress tracking, Review queue |
| Task Schema | Task definitions and states | Passerby tasks, Task queue |
| Session Schema | User session progress tracking | Progress components |
| Fixture Datasets | Pre-populated realistic data | All demo scenarios |

---

## Data Schemas

### Schema 1: Tablet

**Purpose:** Core data model for cuneiform tablet artifacts.

```typescript
interface Tablet {
  // Identifiers
  id: string;                          // Internal Glintstone ID (e.g., "glint-001")
  cdliPNumber: string;                 // CDLI P-number (e.g., "P123456")
  museumNumber: string;                // Museum catalog number
  collection: string;                  // Holding institution

  // Metadata
  period: Period;                      // Historical period
  language: Language;                  // Primary language
  genre: Genre;                        // Text type
  provenience: string;                 // Archaeological find location
  dimensions: {
    height: number;                    // in mm
    width: number;
    thickness: number;
  };

  // Images
  images: {
    obverse: ImageAsset;               // Front face
    reverse: ImageAsset;               // Back face
    edge?: ImageAsset;                 // Optional edge views
    thumbnail: string;                 // Small preview
  };

  // Content
  lineCount: {
    obverse: number;
    reverse: number;
  };
  transcription?: Transcription;       // Current transcription state
  translation?: Translation;           // Current translation state

  // Status (per UX Strategy 1.2 Authority Model)
  status: ContentStatus;
  confidenceScore: number;             // 0-100 aggregate
  contributorCount: number;
  lastActivity: Date;

  // Lifecycle (per UX Strategy 2.4 Tablet Journey)
  lifecycleStage: LifecycleStage;

  // Demo flags
  isFeatured: boolean;                 // Show on marketing page
  isStarterTablet: boolean;            // Good for first-time users
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced';
}

// Enums
type Period =
  | 'ur-iii'              // 2112-2004 BCE
  | 'old-babylonian'      // 2000-1600 BCE
  | 'middle-babylonian'   // 1600-1000 BCE
  | 'neo-assyrian'        // 911-609 BCE
  | 'neo-babylonian'      // 626-539 BCE
  | 'achaemenid';         // 539-330 BCE

type Language =
  | 'sumerian'
  | 'akkadian'
  | 'bilingual';          // Sumerian-Akkadian

type Genre =
  | 'administrative'      // Receipts, accounts
  | 'letter'              // Correspondence
  | 'legal'               // Contracts, laws
  | 'literary'            // Epics, hymns
  | 'scholarly'           // Scientific, medical
  | 'royal-inscription';  // Commemorative

type ContentStatus =
  | 'proposed'            // AI-generated or single contributor
  | 'under-review'        // Multiple contributors, awaiting expert
  | 'provisionally-accepted'  // One expert approved
  | 'accepted'            // Multiple experts verified
  | 'disputed';           // Experts disagree

type LifecycleStage =
  | 'catalog-entry'       // Just imported
  | 'preparation'         // Passerby tasks active
  | 'draft-transcription' // Early Learner work
  | 'expert-review'       // In review queue
  | 'consensus'           // Second expert needed
  | 'translation'         // Transcription done, translation WIP
  | 'publication';        // Ready for export

interface ImageAsset {
  url: string;
  width: number;
  height: number;
  regions?: SignRegion[];  // Pre-defined clickable areas
}

interface SignRegion {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  signId?: string;         // Link to Sign schema if identified
  lineNumber: number;
  positionInLine: number;
}
```

**Acceptance Criteria:**
- [ ] Schema supports all fields needed for demo journeys
- [ ] Status values align with UX Strategy authority model
- [ ] Lifecycle stages map to Tablet Journey (UX Strategy 2.4)
- [ ] TypeScript types exported for frontend consumption

---

### Schema 2: Sign

**Purpose:** Individual cuneiform sign data for learning and matching tasks.

```typescript
interface Sign {
  id: string;                          // Internal ID
  signName: string;                    // Standard name (e.g., "AN", "LU2")
  unicodeValue?: string;               // Cuneiform Unicode if available

  // Readings (polyvalency)
  readings: SignReading[];

  // Visual representations
  images: {
    standard: string;                  // Clear reference image
    variants: SignVariant[];           // Period/style variants
  };

  // Learning data
  frequency: 'high' | 'medium' | 'low';
  category: SignCategory;
  learnOrder: number;                  // Sequence in curriculum
  mnemonicHint?: string;               // Memory aid
  funFact?: string;                    // Engaging context

  // Relationships
  similarSigns: string[];              // IDs of visually similar signs
  determinativeFor?: string[];         // Categories it classifies
}

interface SignReading {
  value: string;                       // e.g., "an", "dingir", "ilu"
  type: 'syllabic' | 'logographic';
  language: 'sumerian' | 'akkadian';
  meaning?: string;                    // For logograms
  commonness: 'primary' | 'secondary' | 'rare';
}

interface SignVariant {
  id: string;
  period: Period;
  imageUrl: string;
  notes?: string;
}

type SignCategory =
  | 'number'
  | 'determinative'
  | 'common-noun'
  | 'verb'
  | 'divine-name'
  | 'personal-name-element'
  | 'grammatical';
```

**Acceptance Criteria:**
- [ ] At least 50 signs defined for demo/learning
- [ ] 25 high-frequency "foundation" signs fully documented
- [ ] Each sign has at least one clear reference image
- [ ] Mnemonics and fun facts for beginner engagement

---

### Schema 3: User (Contributor Profile)

**Purpose:** User profiles supporting the three-tier model.

```typescript
interface User {
  id: string;
  displayName: string;                 // Anonymous-friendly
  avatarUrl?: string;

  // Tier (per curriculum-research-report.md)
  tier: UserTier;
  tierProgress: TierProgress;

  // Contribution stats
  stats: ContributionStats;

  // For demo: pre-defined profiles
  isExpertVerified?: boolean;
  institution?: string;
  specialization?: string;

  // Session
  currentSession?: SessionState;
}

type UserTier = 'passerby' | 'early-learner' | 'expert';

interface TierProgress {
  // Passerby
  tasksCompleted: number;
  accuracy: number;                    // 0-100

  // Early Learner
  signsLearned: number;
  tabletsContributed: number;
  curriculumProgress: number;          // 0-100

  // Expert (display only for demo)
  reviewsCompleted: number;
  tabletsApproved: number;
}

interface ContributionStats {
  totalContributions: number;
  tabletsHelped: number;
  signsIdentified: number;
  sessionsCompleted: number;
  streakDays: number;
  joinDate: Date;
  lastActive: Date;
}
```

**Acceptance Criteria:**
- [ ] At least 5 demo users per tier
- [ ] Expert users have institutional affiliations
- [ ] Stats are realistic and varied

---

### Schema 4: Contribution

**Purpose:** Individual contribution records for attribution and review.

```typescript
interface Contribution {
  id: string;
  userId: string;
  tabletId: string;

  // What was contributed
  type: ContributionType;
  target: ContributionTarget;          // What element was affected

  // Content
  content: string | SignMatch | TranslationSegment;
  confidenceLevel: ConfidenceLevel;    // User's self-assessment

  // Status
  status: ContributionStatus;
  validatedBy?: string;                // Expert user ID
  validatedAt?: Date;
  validationNotes?: string;

  // Metadata
  createdAt: Date;
  aiAssisted: boolean;                 // Was AI suggestion shown
  agreementScore?: number;             // How many others agreed (0-100)
}

type ContributionType =
  | 'sign-match'                       // Passerby task
  | 'damage-marking'
  | 'line-count'
  | 'orientation'
  | 'transcription-segment'            // Early Learner
  | 'translation-segment'
  | 'review-approval'                  // Expert
  | 'review-correction'
  | 'review-rejection';

interface ContributionTarget {
  surface: 'obverse' | 'reverse' | 'edge';
  lineNumber?: number;
  signPosition?: number;
  regionId?: string;
}

type ConfidenceLevel =
  | 'certain'          // "I'm sure"
  | 'probable'         // "Pretty confident"
  | 'possible'         // "Maybe"
  | 'guess';           // "Not sure"

type ContributionStatus =
  | 'pending'          // Just submitted
  | 'aggregated'       // Included in consensus
  | 'accepted'         // Validated by expert
  | 'rejected'         // Expert rejected
  | 'superseded';      // Newer contribution replaced this
```

**Acceptance Criteria:**
- [ ] Schema supports full contribution-to-review pipeline
- [ ] Attribution chain is fully traceable
- [ ] Status transitions align with UX Strategy authority model

---

### Schema 5: Task

**Purpose:** Task definitions for micro-contribution system.

```typescript
interface Task {
  id: string;
  tabletId: string;

  // Task definition
  type: TaskType;
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedSeconds: number;

  // Content
  prompt: string;                      // "Which sign matches the highlighted area?"
  context?: string;                    // Additional helpful info

  // For visual tasks
  targetRegion?: SignRegion;
  options?: TaskOption[];

  // For text tasks
  aiSuggestion?: string;
  referenceText?: string;

  // State
  status: TaskStatus;
  assignedTo?: string;
  completedCount: number;              // How many users have done this
  consensusReached: boolean;

  // Reward content
  completionMessage: string;
  funFact?: string;
  educationalNote?: string;
}

type TaskType =
  // Passerby (no knowledge required)
  | 'sign-match'                       // "Do these match?"
  | 'damage-identification'            // "Mark damaged areas"
  | 'line-counting'                    // "How many lines?"
  | 'orientation-check'                // "Which way is up?"
  | 'ai-validation'                    // "Is this correct? Yes/No"

  // Early Learner
  | 'sign-identification'              // "What sign is this?"
  | 'number-reading'                   // "What number is this?"
  | 'transcription-verify'             // "Check this transcription"
  | 'translation-segment';             // "Translate this phrase"

interface TaskOption {
  id: string;
  label: string;
  imageUrl?: string;                   // For visual options
  isCorrect?: boolean;                 // For demo validation
}

type TaskStatus =
  | 'available'
  | 'assigned'
  | 'completed'
  | 'expired';
```

**Acceptance Criteria:**
- [ ] Task types cover all Passerby and Early Learner activities
- [ ] Each task has clear prompt and options
- [ ] Completion messaging is encouraging without being condescending

---

### Schema 6: Session

**Purpose:** Track user progress within a contribution session.

```typescript
interface Session {
  id: string;
  userId: string;
  startedAt: Date;
  endedAt?: Date;

  // Progress
  tasksCompleted: Task[];
  currentTaskId?: string;
  tasksSkipped: number;

  // Stats for session summary
  tabletsHelped: string[];             // Tablet IDs
  signsIdentified: number;
  accuracy: number;                    // Based on agreement

  // Engagement
  durationMinutes: number;
  streak: number;                      // Tasks in a row without skip
}

interface SessionSummary {
  tasksCompleted: number;
  tabletsHelped: number;
  signsIdentified: number;
  accuracyPercentage: number;
  durationMinutes: number;
  funFactsShown: string[];
  ctaType: 'continue' | 'create-account' | 'learn-more';
}
```

**Acceptance Criteria:**
- [ ] Session tracks all data needed for summary screen
- [ ] Progress persists through page refresh (localStorage for demo)

---

## Fixture Datasets

### Dataset 1: Demo Tablets (20 tablets)

**Composition Requirements:**

| Category | Count | Criteria |
|----------|-------|----------|
| Starter Tablets | 5 | Well-preserved, beginner-friendly, Ur III admin |
| Intermediate | 8 | Letters, varied periods, some damage |
| Advanced | 3 | Literary fragments, disputed readings |
| Featured | 2 | High visual impact for marketing |
| CDLI Integration | 2 | Real P-numbers for demo linking |

**Per-Tablet Requirements:**

Each tablet fixture must include:
- [ ] High-quality obverse and reverse images (or placeholders)
- [ ] Pre-defined sign regions for at least 5 signs per tablet
- [ ] Realistic metadata (period, language, genre, provenience)
- [ ] At least one "completed" transcription line for context
- [ ] Associated tasks (at least 3 per tablet)

**Sample Tablet Fixture:**

```json
{
  "id": "glint-001",
  "cdliPNumber": "P123456",
  "museumNumber": "YBC 4644",
  "collection": "Yale Babylonian Collection",
  "period": "old-babylonian",
  "language": "akkadian",
  "genre": "letter",
  "provenience": "Sippar (uncertain)",
  "dimensions": { "height": 45, "width": 32, "thickness": 18 },
  "images": {
    "obverse": {
      "url": "/fixtures/tablets/glint-001-obverse.jpg",
      "width": 1200,
      "height": 1600,
      "regions": [
        { "id": "r1", "x": 120, "y": 80, "width": 40, "height": 35, "lineNumber": 1, "positionInLine": 1 }
      ]
    },
    "reverse": {
      "url": "/fixtures/tablets/glint-001-reverse.jpg",
      "width": 1200,
      "height": 1600,
      "regions": []
    },
    "thumbnail": "/fixtures/tablets/glint-001-thumb.jpg"
  },
  "lineCount": { "obverse": 6, "reverse": 3 },
  "status": "under-review",
  "confidenceScore": 72,
  "contributorCount": 8,
  "lifecycleStage": "draft-transcription",
  "isFeatured": false,
  "isStarterTablet": true,
  "difficultyLevel": "beginner"
}
```

**Acceptance Criteria:**
- [ ] 20 tablet fixtures created with complete data
- [ ] Images are either real (public domain) or realistic placeholders
- [ ] At least 2 tablets use real CDLI P-numbers for integration demo

---

### Dataset 2: Sign Library (50 signs)

**Composition Requirements:**

| Priority | Count | Focus |
|----------|-------|-------|
| Foundation | 25 | Numbers, high-frequency, determinatives |
| Expansion | 25 | Verbs, nouns, grammatical markers |

**Per-Sign Requirements:**
- [ ] Clear reference image
- [ ] At least primary reading documented
- [ ] Category and frequency assigned
- [ ] Mnemonic or fun fact for engagement

**Reference:** Use curriculum-research-report.md Appendix A for sign selection.

---

### Dataset 3: Demo Users (15 users)

**Composition:**

| Tier | Count | Profiles |
|------|-------|----------|
| Passerby | 5 | Anonymous "Contributor 42" style |
| Early Learner | 5 | Named with varied progress levels |
| Expert | 5 | Institutional affiliations, specializations |

**Sample Expert Profile:**

```json
{
  "id": "expert-001",
  "displayName": "Dr. Sarah Chen",
  "tier": "expert",
  "isExpertVerified": true,
  "institution": "University of Pennsylvania",
  "specialization": "Ur III Administrative Texts",
  "stats": {
    "totalContributions": 847,
    "tabletsHelped": 234,
    "reviewsCompleted": 412
  }
}
```

---

### Dataset 4: Task Queue (100 tasks)

**Composition:**

| Type | Count | Distribution |
|------|-------|--------------|
| sign-match | 40 | 4-option multiple choice |
| damage-identification | 15 | Drawing/selection |
| ai-validation | 20 | Binary yes/no |
| transcription-verify | 15 | Compare and confirm |
| translation-segment | 10 | Short phrase translation |

**Per-Task Requirements:**
- [ ] Linked to specific tablet and region
- [ ] Clear prompt text
- [ ] For choice tasks: plausible distractor options
- [ ] Completion message and optional fun fact

---

### Dataset 5: Contribution History (200 contributions)

**Purpose:** Pre-populate review queue and demonstrate handoff patterns.

**Composition:**
- 80% from Passerby users (sign-match, damage, etc.)
- 15% from Early Learner users (transcription, translation)
- 5% from Expert users (reviews, approvals)

**Status Distribution:**
- 50% aggregated (consensus reached)
- 30% pending (awaiting more input)
- 15% accepted (expert validated)
- 5% rejected (with notes explaining why)

---

## Integration Points

### Upstream Dependencies
- L1: Design System (status colors must match schema statuses)

### Downstream Consumers
- L3: Tablet Components (consume Tablet, Sign schemas)
- L4: Task & Progress Components (consume Task, Session, Contribution schemas)
- J1-J5: All journeys use fixture data

---

## Data Storage (Release 1)

**Approach:** Static JSON files + localStorage

For the POC demo, data will be:
1. **Static Fixtures:** JSON files loaded at build time
2. **Session State:** localStorage for current session progress
3. **No Backend:** All data is client-side

**File Structure:**

```
/fixtures/
  /tablets/
    index.json           # Tablet list
    glint-001.json       # Individual tablet data
    glint-001-obverse.jpg
    ...
  /signs/
    index.json           # Sign list
    sign-assets/         # Sign images
  /users/
    demo-users.json      # Pre-defined user profiles
  /tasks/
    task-queue.json      # Available tasks
  /contributions/
    demo-contributions.json  # Pre-populated history
```

---

## Out of Scope

- Real CDLI API integration (demo uses static linking only)
- Backend database schema (Release 2+)
- User authentication (demo uses pre-defined profiles)
- Real-time data updates (static fixtures only)
- Full ATF format support (simplified representation)

---

## Testing Requirements

**Schema Validation:**
- [ ] All fixture files validate against TypeScript schemas
- [ ] No missing required fields
- [ ] ID references are consistent (tablet IDs exist, etc.)

**Content Review:**
- [ ] Academic advisor reviews tablet metadata for plausibility
- [ ] Sign data accuracy verified against standard references
- [ ] Task prompts are clear and grammatically correct

**Demo Coverage:**
- [ ] Each journey (J1-J5) has sufficient data to complete
- [ ] 10-minute demo session can be performed without data exhaustion
- [ ] Edge cases are represented (disputed status, low confidence, etc.)

---

## Technical Hints

**Recommended Implementation:**

1. Define schemas as TypeScript interfaces in `/types/`
2. Create fixture JSON files in `/fixtures/`
3. Use a data service layer to abstract fixture loading
4. For localStorage persistence, use a simple wrapper:

```typescript
// services/sessionStore.ts
const STORAGE_KEY = 'glintstone_session';

export const sessionStore = {
  get: () => JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'),
  set: (data: SessionState) => localStorage.setItem(STORAGE_KEY, JSON.stringify(data)),
  clear: () => localStorage.removeItem(STORAGE_KEY),
};
```

5. Consider using a mock API layer that could be swapped for real API later:

```typescript
// services/api.ts
export const api = {
  getTablet: (id: string) => import(`../fixtures/tablets/${id}.json`),
  getTasks: () => import('../fixtures/tasks/task-queue.json'),
  // ...
};
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
