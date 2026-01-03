# L4: Core - Task Queue and Progress Components

**Document Type:** Layer PRD
**Priority:** P0 (Critical Path)
**Status:** Ready
**Estimated Complexity:** M
**Dependencies:** L1 (Design System), L2 (Dummy Data), L3 (Tablet Components)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| Layer Level | Core |
| Serves User Types | All (Passerby, Early Learner, Expert) |
| UX Strategy Reference | Section 1.3: Contribution-Reward Cycle; Section 9: Strategic Direction C (Adaptive Task Surfacing) |
| Brief Reference | Key Metrics - contributions per hour, task completion rate |

---

## Layer Purpose

Provide the task management and progress tracking infrastructure that powers the Adaptive Task Surfacing experience. This layer handles task queuing, session management, progress visualization, and the contribution-reward feedback loop that keeps users engaged and productive.

**Why This Matters for Release 1:**
- Task flow is the core engagement mechanic for Passerby users
- Progress tracking is critical for motivation (hobbyist-feedback-report.md)
- Session management enables the "2-5 minute contribution" promise
- Reward feedback creates the positive loop that drives retention

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Performance | Task load time | < 500ms |
| Performance | Next task ready before current completes | Yes (prefetch) |
| Usability | Session state survives page refresh | Yes |
| Engagement | Completion message appears within 200ms | Yes |
| KPI Enablement | Contributions per hour trackable | Yes |

---

## Capabilities Provided

| Capability | Description | Consumed By |
|------------|-------------|-------------|
| Task Queue | Ordered list of available tasks | Passerby, Early Learner flows |
| Task Card | Task presentation with interaction | All contribution screens |
| Session Manager | Track progress within session | Progress displays, summaries |
| Progress Display | Visual progress indicators | Task screens, dashboard |
| Reward Feedback | Celebration and education moments | Post-task flow |
| Session Summary | End-of-session impact display | Session complete screen |

---

## Components

### Component 1: TaskQueue (Service Layer)

**Purpose:** Manage task selection, ordering, and delivery for the Adaptive Task Surfacing system.

**Interface:**

```typescript
interface TaskQueueService {
  // Initialization
  initialize(userTier: UserTier, preferences?: TaskPreferences): Promise<void>;

  // Task retrieval
  getNextTask(): Task | null;
  peekNextTask(): Task | null;           // Preview without consuming
  getTaskById(taskId: string): Task | null;

  // Task lifecycle
  startTask(taskId: string): void;
  completeTask(taskId: string, result: TaskResult): void;
  skipTask(taskId: string): void;
  reportUnsure(taskId: string): void;

  // Queue management
  getQueueLength(): number;
  prefetchTasks(count: number): Promise<void>;
  refreshQueue(): Promise<void>;

  // Session context
  getSessionStats(): SessionStats;
  getCompletedTasks(): Task[];
}

interface TaskPreferences {
  preferredDuration?: 'quick' | 'standard' | 'deep';  // 2min, 10min, 30min
  preferredTypes?: TaskType[];
  excludeTablets?: string[];           // Tablets already seen
}

interface TaskResult {
  selectedOption?: string;
  customInput?: string;
  confidenceLevel: ConfidenceLevel;
  durationMs: number;
}

interface SessionStats {
  tasksCompleted: number;
  tasksSkipped: number;
  tabletsTouched: string[];
  signsIdentified: number;
  accuracyEstimate: number;            // Based on consensus
  sessionDurationMs: number;
}
```

**Task Selection Algorithm (Release 1 Simplified):**

For the POC, task selection uses simple rules:

1. **Filter by Tier:** Only show tasks appropriate for user's tier
2. **Prioritize Variety:** Avoid consecutive tasks from same tablet
3. **Respect Time Preference:** Match estimated duration to preference
4. **Prefetch Buffer:** Always have 3 tasks ready in memory

```typescript
// Pseudocode for task selection
function selectNextTask(userTier, preferences, completedTaskIds) {
  const eligibleTasks = allTasks
    .filter(t => t.difficulty <= userTier.maxDifficulty)
    .filter(t => !completedTaskIds.includes(t.id))
    .filter(t => !preferences.excludeTablets?.includes(t.tabletId));

  // Avoid same tablet consecutively
  const lastTabletId = getLastCompletedTask()?.tabletId;
  const diverseTasks = eligibleTasks.filter(t => t.tabletId !== lastTabletId);

  // Sort by estimated duration match
  const sorted = (diverseTasks.length > 0 ? diverseTasks : eligibleTasks)
    .sort((a, b) => {
      const duraPref = durationToSeconds(preferences.preferredDuration);
      return Math.abs(a.estimatedSeconds - duraPref) -
             Math.abs(b.estimatedSeconds - duraPref);
    });

  return sorted[0] || null;
}
```

**Acceptance Criteria:**
- [ ] Tasks filtered by user tier
- [ ] Tasks ordered to avoid repetition
- [ ] Prefetch prevents loading delays between tasks
- [ ] Session stats accurately track progress
- [ ] Queue persists across page refresh (localStorage)
- [ ] Empty queue handled gracefully ("Come back soon!")

---

### Component 2: TaskCard

**Purpose:** Present a single task to the user with all necessary context and interaction controls.

**Interface:**

```typescript
interface TaskCardProps {
  // Required
  task: Task;
  onComplete: (result: TaskResult) => void;

  // Optional
  onSkip?: () => void;
  onUnsure?: () => void;
  showProgress?: boolean;              // Position in session
  progressCurrent?: number;
  progressTotal?: number;
  showTimer?: boolean;                 // Elapsed time
  showHint?: boolean;                  // AI/contextual hint

  // Customization
  variant?: 'fullscreen' | 'card' | 'inline';
  showTabletContext?: boolean;         // Mini tablet preview
}
```

**Visual Specification:**

**Fullscreen Variant (Passerby):**

```
+--------------------------------------------------+
|  Task 3 of 10                        [0:45]      |
|  ================================================ |
+--------------------------------------------------+
|                                                   |
|  Which sign matches the highlighted area?         |
|                                                   |
|  +-------------------+                            |
|  |   [Tablet with    |                            |
|  |    highlighted    |                            |
|  |    region]        |                            |
|  +-------------------+                            |
|                                                   |
|  +--------+  +--------+  +--------+  +--------+   |
|  |  AN    |  |  EN    |  |  LU    |  |  UD    |   |
|  | [img]  |  | [img]  |  | [img]  |  | [img]  |   |
|  +--------+  +--------+  +--------+  +--------+   |
|                                                   |
|  [I'm not sure]                        [Skip ->]  |
|                                                   |
+--------------------------------------------------+
```

**Card Variant (Dashboard embedded):**

```
+----------------------------------+
| Quick Task                  [->] |
+----------------------------------+
| Which sign matches?              |
| [Sign] [A] [B] [C] [D]           |
+----------------------------------+
```

**Behavior Specification:**

1. **Task Loading:**
   - Show skeleton while task loads
   - Prefetch next task during current interaction
   - Handle load failure with retry

2. **Interaction:**
   - Single selection for choice tasks
   - Text input for transcription tasks
   - Drawing for damage marking tasks
   - All inputs trigger immediate feedback

3. **Timer (Optional):**
   - Shows elapsed time since task start
   - Non-stressful display (no countdown)
   - Used for analytics, not pressure

4. **Progress Indicator:**
   - "Task 3 of 10" format
   - Progress bar fills as session progresses
   - Celebration at milestones (5, 10, 25)

**Acceptance Criteria:**
- [ ] Task prompt clearly displayed
- [ ] Tablet context visible if enabled
- [ ] Options meet touch target requirements (44px+)
- [ ] Skip button available and clearly secondary
- [ ] "I'm not sure" option available
- [ ] Progress indicator shows current position
- [ ] Keyboard navigation works (Tab, Enter)
- [ ] Focus managed correctly on task change

---

### Component 3: ProgressBar

**Purpose:** Visual indicator of progress within a session or toward a goal.

**Interface:**

```typescript
interface ProgressBarProps {
  // Required
  current: number;
  total: number;

  // Optional
  variant?: 'linear' | 'circular' | 'segmented';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;                 // "3 of 10"
  showPercentage?: boolean;            // "30%"
  animated?: boolean;                  // Animate on change
  color?: 'gold' | 'violet' | 'success';
  milestones?: number[];               // Celebrate at these points
  onMilestone?: (milestone: number) => void;
}
```

**Visual Variants:**

**Linear (default):**
```
[=====---------] 5/10
```

**Circular:**
```
  ___
 /   \
|  5  |
| /10 |
 \___/
```

**Segmented:**
```
[*][*][*][*][*][ ][ ][ ][ ][ ]
```

**Milestone Behavior:**
- When progress hits a milestone, trigger celebration
- Fire onMilestone callback
- Brief pulse animation on progress bar

**Acceptance Criteria:**
- [ ] All three variants render correctly
- [ ] Progress animates smoothly on update
- [ ] Label/percentage display is optional
- [ ] Milestones trigger callback
- [ ] Accessible (aria-valuenow, aria-valuemax)
- [ ] Color uses design system tokens

---

### Component 4: RewardFeedback

**Purpose:** Provide immediate positive feedback after task completion per the Contribution-Reward Cycle.

**Interface:**

```typescript
interface RewardFeedbackProps {
  // Required
  type: 'success' | 'consensus' | 'valuable-uncertainty' | 'milestone';

  // Optional
  message?: string;                    // Override default message
  funFact?: string;                    // Educational tidbit
  educationalNote?: string;            // "This sign is called..."
  impactStatement?: string;            // "You helped with tablet X"
  duration?: number;                   // Auto-dismiss after ms

  // Callbacks
  onDismiss?: () => void;
  onLearnMore?: () => void;
  onContinue?: () => void;
}
```

**Feedback Types:**

**Success (default):**
```
+----------------------------------+
|  [Checkmark]  Great job!         |
|                                  |
|  Your answer matched 7 others.   |
|                                  |
|  [Continue ->]                   |
+----------------------------------+
```

**Consensus Match:**
```
+----------------------------------+
|  [Star] You matched the experts! |
|                                  |
|  This sign is "AN" - meaning     |
|  "god" or "sky" in Sumerian.     |
|                                  |
|  [Learn more]    [Continue ->]   |
+----------------------------------+
```

**Valuable Uncertainty:**
```
+----------------------------------+
|  [Flag] Uncertainty is helpful!  |
|                                  |
|  When you mark "not sure", it    |
|  helps us identify tricky areas  |
|  for expert review.              |
|                                  |
|  [Continue ->]                   |
+----------------------------------+
```

**Milestone:**
```
+----------------------------------+
|  [Trophy] 10 Tasks Complete!     |
|                                  |
|  You've helped with 3 tablets.   |
|  These ancient records are one   |
|  step closer to being read.      |
|                                  |
|  [See your impact] [Continue]    |
+----------------------------------+
```

**Behavior Specification:**

1. **Timing:**
   - Appears within 200ms of task completion
   - Auto-dismisses after 2 seconds (unless user interacts)
   - Can be dismissed immediately with continue

2. **Animation:**
   - Slides up from bottom or fades in
   - Checkmark/icon animates on appear
   - Brief bounce easing for celebration feel

3. **Content Priority:**
   - Message > Impact > Educational > Fun Fact
   - Never show all four; pick most relevant
   - Fun facts appear ~30% of the time (random)

**Acceptance Criteria:**
- [ ] Appears within 200ms of task completion
- [ ] Four feedback types display correctly
- [ ] Fun facts shown occasionally (not every time)
- [ ] Auto-dismiss after configurable duration
- [ ] Continue button always visible
- [ ] Learn more link when educational content present
- [ ] Animation is smooth and not jarring
- [ ] Respects prefers-reduced-motion

---

### Component 5: SessionSummary

**Purpose:** Display end-of-session impact and encourage continued engagement.

**Interface:**

```typescript
interface SessionSummaryProps {
  // Required
  stats: SessionStats;

  // Optional
  tabletsHelped: TabletSummary[];      // Mini-previews of tablets
  achievements?: Achievement[];         // Any unlocked achievements
  suggestedNext?: 'continue' | 'learn' | 'explore';

  // Callbacks
  onContinue?: () => void;
  onCreateAccount?: () => void;
  onExplore?: () => void;
  onLearn?: () => void;
}

interface TabletSummary {
  id: string;
  thumbnail: string;
  name: string;
  contributionType: string;
}

interface Achievement {
  id: string;
  name: string;
  icon: string;
  description: string;
  isNew: boolean;
}
```

**Visual Specification:**

```
+--------------------------------------------------+
|                                                   |
|  [Star Animation]                                 |
|                                                   |
|  Session Complete!                                |
|                                                   |
|  +------+  +------+  +------+                     |
|  |  15  |  |  3   |  |  87% |                     |
|  | tasks|  |tablets|  | accuracy                  |
|  +------+  +------+  +------+                     |
|                                                   |
+--------------------------------------------------+
|  You helped with:                                 |
|  [thumb] YBC 4644 - Identified 5 signs            |
|  [thumb] P123456 - Marked damage areas            |
|  [thumb] CBS 10467 - Verified transcription       |
+--------------------------------------------------+
|  [Achievement: First Session!]                    |
+--------------------------------------------------+
|                                                   |
|  [Create account to save progress]                |
|                                                   |
|  [Do more tasks]  [Explore tablets]  [Learn]      |
|                                                   |
+--------------------------------------------------+
```

**Stat Display (per hobbyist-feedback-report.md):**
- Tasks completed (concrete number)
- Tablets helped (connection to artifacts)
- Accuracy estimate (competence validation)
- Session duration (optional, non-judgmental)

**Call-to-Action Priority:**
1. Create Account (if anonymous, but not pushy)
2. Continue Contributing (primary CTA)
3. Explore / Learn (secondary options)

**Acceptance Criteria:**
- [ ] Stats display prominently with icons
- [ ] Tablet thumbnails link to tablet view
- [ ] Achievements section shows if any unlocked
- [ ] Account creation CTA is optional, not blocking
- [ ] All three continuation paths available
- [ ] Animation on mount is celebratory
- [ ] Shareable summary for social (stretch goal)

---

### Component 6: TaskTimer

**Purpose:** Track and display time spent on tasks for analytics and optional user feedback.

**Interface:**

```typescript
interface TaskTimerProps {
  isRunning: boolean;
  showDisplay?: boolean;               // Show elapsed time to user
  warningThreshold?: number;           // Seconds before "take your time"
  onTick?: (elapsedMs: number) => void;
}

// Hook for timer logic
function useTaskTimer(): {
  elapsed: number;                     // Milliseconds
  start: () => void;
  stop: () => number;                  // Returns final elapsed
  reset: () => void;
  isRunning: boolean;
}
```

**Display Specification:**

```
[0:45]  <- Minutes:seconds format
```

**Behavior:**
- Timer starts when task loads
- Timer stops when answer submitted
- No countdown or pressure-inducing display
- If > warningThreshold, show encouragement: "Take your time!"

**Acceptance Criteria:**
- [ ] Timer counts up, not down
- [ ] Display is optional (can be hidden)
- [ ] Time recorded for analytics
- [ ] Encouraging message at threshold (if shown)
- [ ] Timer pauses if user leaves tab (optional)

---

### Component 7: TaskQueue Display

**Purpose:** Show upcoming tasks and allow selection in Early Learner/Expert modes.

**Interface:**

```typescript
interface TaskQueueDisplayProps {
  tasks: Task[];
  currentTaskId?: string;
  allowSelection?: boolean;            // Can user choose next task
  showEstimates?: boolean;             // Show time estimates
  variant?: 'minimal' | 'detailed';
  onTaskSelect?: (taskId: string) => void;
}
```

**Visual Specification:**

**Minimal (Passerby - just progress):**
```
Task 3 of 10 [====------]
```

**Detailed (Early Learner - can see queue):**
```
+----------------------------------+
| Up Next:                         |
| 1. [Sign match] YBC 4644 (~30s)  |
| 2. [Transcribe] P123456 (~2min)  |
| 3. [Verify] CBS 10467 (~1min)    |
+----------------------------------+
```

**Acceptance Criteria:**
- [ ] Minimal variant shows just progress
- [ ] Detailed variant shows task list
- [ ] Clickable tasks if allowSelection=true
- [ ] Time estimates shown if enabled
- [ ] Current task highlighted

---

## Integration Points

### Upstream Dependencies
- L1: Design System (all tokens, especially celebration animations)
- L2: Dummy Data (Task, Session schemas)
- L3: Tablet Components (SignCard, TabletViewer used within TaskCard)

### Downstream Consumers
- J2: Passerby Contribution (primary consumer - full task flow)
- J3: Early Learner (task queue with selection)
- J4: Expert Review (review queue as specialized task queue)

---

## State Management

**Session State (localStorage for demo):**

```typescript
interface PersistedSession {
  sessionId: string;
  startedAt: number;                   // Timestamp
  completedTaskIds: string[];
  skippedTaskIds: string[];
  stats: SessionStats;
  currentTaskId?: string;
  queueSnapshot: string[];             // Task IDs for queue restoration
}
```

**State Persistence:**
- Save to localStorage on each task completion
- Restore session on page load if < 24 hours old
- Offer "Resume session?" prompt on return

**Acceptance Criteria:**
- [ ] Session survives page refresh
- [ ] Session resumes after close/reopen (within 24h)
- [ ] Clear session on explicit end
- [ ] Handle corrupted state gracefully

---

## Out of Scope

- Backend task assignment (static queue for demo)
- Real-time multi-user task claiming
- Adaptive difficulty adjustment (future ML feature)
- Streak tracking beyond current session
- Push notifications for task availability

---

## Testing Requirements

**Unit Tests:**
- TaskQueue service correctly filters and orders
- Timer accurately tracks elapsed time
- Progress calculations are correct
- State persistence works correctly

**Integration Tests:**
- Complete task flow: load -> interact -> feedback -> next
- Session summary displays correct aggregate stats
- Milestone achievements trigger correctly

**User Flow Tests:**
- 10-task session completes without errors
- Skip flow works correctly
- "I'm not sure" flow works correctly
- Session resume works after refresh

**Performance Tests:**
- Next task prefetch completes before needed
- Reward feedback appears < 200ms

---

## Technical Hints

**State Management Recommendation:**

For Release 1, use React Context + useReducer for session state:

```typescript
// contexts/SessionContext.tsx
interface SessionState {
  status: 'idle' | 'active' | 'complete';
  currentTask: Task | null;
  completedTasks: Task[];
  stats: SessionStats;
}

type SessionAction =
  | { type: 'START_SESSION' }
  | { type: 'LOAD_TASK'; task: Task }
  | { type: 'COMPLETE_TASK'; result: TaskResult }
  | { type: 'SKIP_TASK' }
  | { type: 'END_SESSION' };

function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  // ...
}
```

**Prefetch Strategy:**

```typescript
// Always have next 2 tasks ready
useEffect(() => {
  if (currentTask && !nextTask) {
    prefetchTask();
  }
}, [currentTask]);
```

**Component File Structure:**

```
/components/task/
  TaskQueue/
    TaskQueue.tsx           # Display component
    TaskQueueService.ts     # Service layer
    useTaskQueue.ts         # Hook wrapping service
  TaskCard/
    TaskCard.tsx
    TaskCard.test.tsx
    variants/
      SignMatchTask.tsx
      DamageMarkingTask.tsx
      TranscriptionTask.tsx
  ProgressBar/
    ProgressBar.tsx
    ProgressBar.test.tsx
  RewardFeedback/
    RewardFeedback.tsx
    RewardFeedback.test.tsx
    animations/             # Celebration animations
  SessionSummary/
    SessionSummary.tsx
    SessionSummary.test.tsx
    StatCard.tsx
    AchievementCard.tsx
  TaskTimer/
    TaskTimer.tsx
    useTaskTimer.ts
  index.ts
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
