# J2: Passerby First Contribution Screenflow

**Journey:** Passerby First Contribution
**User Type:** Passerby (anonymous/new user)
**Priority:** P0 (Most Critical Journey)
**PRD Reference:** J2-passerby-contribution.md

---

## Journey Overview

```
[Welcome] --> [Tutorial] --> [Task Loop] --> [Session Summary]
   3s           15s            n tasks           end
                                  |
                            [Reward Feedback]
                                  |
                            [Return to Task]

Within Task Loop:
[Task Card] --answer--> [Reward] --continue--> [Next Task]
     |                      |
     +--unsure--> [Uncertainty Feedback] --continue--> [Next Task]
     |
     +--skip--> [Next Task] (silent)
```

**Goal:** Complete first contribution in under 60 seconds.

**Success Metrics:**
- Time to first task: < 25 seconds
- First task completion: < 60 seconds from entry
- Average tasks per session: > 5
- Session completion rate: > 70%
- Contributions per hour: > 30

---

## Screen 1: Welcome

### Screen ID
`J2-S1-welcome`

### Entry Points
- Marketing page "Try it now" CTA
- Direct link (/contribute)
- Return user (different variant)

### User Goal
Feel welcomed and oriented without delay.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|                                                                   |
|                                                                   |
|                     [Logo: Glintstone - small]                    |
|                                                                   |
|                                                                   |
|                     Welcome to Glintstone                         |
|                                                                   |
|                                                                   |
|              You're about to help decode ancient history.         |
|              No experience needed. Let's begin.                   |
|                                                                   |
|                                                                   |
|                                                                   |
|                        [Button: Continue]                         |
|                                                                   |
|                                                                   |
|                   (Auto-continues in 3 seconds)                   |
|                                                                   |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Stack | layout.md | space="xl", centered |
| Button | forms.md | variant="primary", size="lg" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Continue button | Click | Navigate to J2-S2-tutorial |
| Auto-advance | 3 seconds | Navigate to J2-S2-tutorial |
| Click anywhere | Click | Navigate to J2-S2-tutorial |

### States

**New User:**
- Standard welcome message
- 3-second auto-advance

**Return User:**
```
+------------------------------------------------------------------+
|                                                                   |
|                     Welcome back!                                 |
|                                                                   |
|              Last time you completed 12 tasks                     |
|              and helped with 3 tablets.                           |
|                                                                   |
|           [Button: Continue where you left off]                   |
|                                                                   |
|                      [Link: Start fresh]                          |
|                                                                   |
+------------------------------------------------------------------+
```

### Behavior

- Screen preloads tutorial content
- First task begins prefetch
- Minimum display: 1 second (even if clicked immediately)
- Maximum display: 3 seconds (auto-advance)

### Accessibility Notes

- Focus on Continue button
- Screen reader announces welcome message
- Auto-advance can be interrupted

---

## Screen 2: Mini Tutorial

### Screen ID
`J2-S2-tutorial`

### Entry Points
- Auto-advance from Welcome
- Continue click from Welcome

### User Goal
Understand what to do without reading.

### Wireframe

```
+------------------------------------------------------------------+
| [Skip tutorial]                                                   |
+------------------------------------------------------------------+
|                                                                   |
|                        YOUR FIRST TASK                            |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  [Example Task - Animated/Interactive]                   |   |
|   |                                                          |   |
|   |        +----------------+                                |   |
|   |        |                |                                |   |
|   |        | [Sample sign   |                                |   |
|   |        |  highlighted]  |                                |   |
|   |        |                |                                |   |
|   |        +----------------+                                |   |
|   |                                                          |   |
|   |     +------+  +------+  +------+  +------+               |   |
|   |     | [A]  |  | [B]  |  | [C]  |  | [D]  |               |   |
|   |     +------+  +------+  +------+  +------+               |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   See this ancient symbol? Just pick which reference sign         |
|   it matches. That's it!                                          |
|                                                                   |
|   - Your choices help train our AI                                |
|   - Experts review everything                                     |
|   - There's no wrong answer                                       |
|                                                                   |
|                                                                   |
|                   [Button: Got it, let's start!]                  |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| SignMatchTask | task.md | (example, disabled) |
| Stack | layout.md | space="lg" |
| Button | forms.md | variant="primary", size="lg" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Skip tutorial | Click | Navigate to J2-S3-task (first task) |
| Got it button | Click | Navigate to J2-S3-task (first task) |
| Example options | Click | Visual feedback only (not functional) |

### Tutorial Content

**Animated sequence (optional):**
1. Sign image pulses to draw attention
2. Pointer animation moves to an option
3. Option highlights (demonstrating selection)
4. Checkmark animation (showing success)

Duration: 5 seconds, loops until user continues

### Accessibility Notes

- Skip link is first focusable element
- "No wrong answer" messaging reduces anxiety
- Tutorial is entirely skippable
- Screen reader describes the example task

---

## Screen 3: Task Card (Main Loop)

### Screen ID
`J2-S3-task`

### Entry Points
- Tutorial completion
- Previous task completion
- Return from reward feedback

### User Goal
Complete a contribution task.

### Wireframe

```
+------------------------------------------------------------------+
| Task 3 of 10                                            [2:45]   |
| [=========--------------------------------------------]          |
+------------------------------------------------------------------+
|                                                                   |
|                                                                   |
|            Which sign matches the highlighted area?               |
|                                                                   |
|                                                                   |
|          +----------------------------------+                     |
|          |                                  |                     |
|          |     [TabletViewer: compact]      |                     |
|          |                                  |                     |
|          |     +--------+                   |                     |
|          |     |Highlight|  <- pulsing      |                     |
|          |     +--------+     region        |                     |
|          |                                  |                     |
|          +----------------------------------+                     |
|                                                                   |
|                                                                   |
|   +----------+  +----------+  +----------+  +----------+          |
|   |          |  |          |  |          |  |          |          |
|   | [SignCard| | [SignCard| | [SignCard| | [SignCard|           |
|   |  option] |  |  option] |  |  option] |  |  option] |          |
|   |    AN    |  |    EN    |  |    LU    |  |    UD    |          |
|   |   god    |  |   lord   |  |   man    |  |   sun    |          |
|   |          |  |          |  |          |  |          |          |
|   +----------+  +----------+  +----------+  +----------+          |
|                                                                   |
|                                                                   |
+------------------------------------------------------------------+
| [Button: I'm not sure]                    [Button: Skip ->]       |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| TaskCard | task.md | variant="fullscreen" |
| ProgressBar | progress.md | variant="linear" |
| TabletViewer | tablet.md | variant="compact", single region |
| SignCard | tablet.md | variant="option", 4 cards |
| SignMatchTask | task.md | default |
| Button | forms.md | "secondary" and "ghost" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Sign option | Click | Select, animate, trigger J2-S4-reward |
| I'm not sure | Click | Record uncertainty, trigger J2-S4-unsure |
| Skip | Click | Silent skip, load next task |
| Tablet region | None | Decorative highlight only |

### Task Types (Release 1)

**Sign Match (primary):**
- 4 sign options in 2x2 grid
- One "correct" (AI highest confidence)
- Visual matching task

**Binary Validation:**
- "Does this AI suggestion look correct?"
- Yes/No buttons

**Count Task:**
- "How many lines of text?"
- Numeric options (1, 2, 3, 4+)

### Selection Flow

1. User clicks option
2. Option shows selected state (200ms)
3. Other options fade (100ms)
4. Brief pause (300ms) for satisfaction
5. Reward feedback appears (J2-S4)

### States

**Loading:**
- Skeleton for tablet image
- Options show loading state
- Progress bar pauses

**Ready:**
- Tablet image loaded
- Options enabled
- Timer running

**Selected:**
- Chosen option highlighted
- Others faded
- Footer hidden

### Accessibility Notes

- Task prompt has `aria-live="polite"`
- Options are radio group semantics
- Tab navigates between options
- Enter/Space selects
- Focus visible at all times
- Touch targets 72px minimum

---

## Screen 4: Reward Feedback

### Screen ID
`J2-S4-reward`

### Entry Points
- Task completion (answer selected)

### User Goal
Feel rewarded for contribution.

### Wireframe Variants

**Standard Success:**
```
+------------------------------------------------------------------+
|                                                                   |
|  Task 3 of 10                                                     |
|  [===========-----------------------------------------]          |
|                                                                   |
|                                                                   |
|                                                                   |
|  +------------------------------------------------------+        |
|  |                                                      |        |
|  |  [Checkmark icon - animated]                         |        |
|  |                                                      |        |
|  |  Great job!                                          |        |
|  |                                                      |        |
|  |  Your answer matched 7 other contributors.           |        |
|  |                                                      |        |
|  |                    [Button: Continue ->]             |        |
|  |                                                      |        |
|  +------------------------------------------------------+        |
|                                                                   |
|                                                                   |
+------------------------------------------------------------------+
```

**With Fun Fact (~15% of tasks):**
```
+------------------------------------------------------------------+
|  +------------------------------------------------------+        |
|  |                                                      |        |
|  |  [Lightbulb icon]                                    |        |
|  |                                                      |        |
|  |  Nice! Did you know?                                 |        |
|  |                                                      |        |
|  |  This tablet is a 4,000-year-old letter from         |        |
|  |  Babylon. It might be a merchant writing to          |        |
|  |  his business partner!                               |        |
|  |                                                      |        |
|  |                    [Button: Continue ->]             |        |
|  |                                                      |        |
|  +------------------------------------------------------+        |
+------------------------------------------------------------------+
```

**With Sign Learning (~10% of tasks):**
```
+------------------------------------------------------------------+
|  +------------------------------------------------------+        |
|  |                                                      |        |
|  |  [Star icon]  You matched the experts!               |        |
|  |                                                      |        |
|  |  This sign is "AN" (also read "dingir")              |        |
|  |  It means "god" or "sky" in Sumerian.                |        |
|  |                                                      |        |
|  |  [Link: Learn more]       [Button: Continue ->]      |        |
|  |                                                      |        |
|  +------------------------------------------------------+        |
+------------------------------------------------------------------+
```

**Milestone (Task 5, 10, 25, 50):**
```
+------------------------------------------------------------------+
|  +------------------------------------------------------+        |
|  |                                                      |        |
|  |  [Trophy icon - animated]                            |        |
|  |                                                      |        |
|  |  10 Tasks Complete!                                  |        |
|  |                                                      |        |
|  |  You've helped with 3 tablets. These ancient         |        |
|  |  records are one step closer to being read.          |        |
|  |                                                      |        |
|  |  [Button: See your impact] [Button: Continue ->]     |        |
|  |                                                      |        |
|  +------------------------------------------------------+        |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| RewardFeedback | progress.md | type varies |
| Button | forms.md | variant="primary" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Continue | Click | Load next task (J2-S3) |
| Learn more | Click | Open ContextPanel with sign info |
| See your impact | Click | Navigate to J2-S6-summary |
| Auto-dismiss | 2.5s | Load next task |

### Animation

**Icon animation by type:**
- Checkmark: Draw stroke (400ms)
- Star: Scale + sparkle (500ms)
- Trophy: Bounce + shine (600ms)
- Lightbulb: Glow pulse (400ms)

**Card animation:**
- Slide up from bottom (250ms)
- Fade in (200ms)

### Timing

- Appears: 200ms after selection
- Auto-dismiss: 2.5 seconds (hover pauses)
- User can continue immediately

### Accessibility Notes

- role="status" with aria-live="polite"
- Focus moves to Continue button
- Animation respects prefers-reduced-motion
- Message announced to screen readers

---

## Screen 5: Uncertainty Feedback

### Screen ID
`J2-S5-unsure`

### Entry Points
- "I'm not sure" button click

### User Goal
Feel validated for honest uncertainty.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|  +------------------------------------------------------+        |
|  |                                                      |        |
|  |  [Flag icon]                                         |        |
|  |                                                      |        |
|  |  Uncertainty is helpful!                             |        |
|  |                                                      |        |
|  |  When you mark something as unclear, you help        |        |
|  |  us identify signs that need expert attention.       |        |
|  |  This is real, valuable data.                        |        |
|  |                                                      |        |
|  |                    [Button: Continue ->]             |        |
|  |                                                      |        |
|  +------------------------------------------------------+        |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| RewardFeedback | progress.md | type="valuable-uncertainty" |
| Button | forms.md | variant="primary" |

### Key Messaging

- "Uncertainty is helpful!" (positive framing)
- Explains WHY it's valuable
- Never feels like failure
- Counts toward session progress

### Behavior

- Same timing as standard reward
- Task counts as contribution
- Progress bar advances

---

## Screen 6: Session Summary

### Screen ID
`J2-S6-summary`

### Entry Points
- Complete 10 tasks (default session)
- Click "See your impact" at milestone
- Explicit "End session" action

### User Goal
See concrete impact and decide next steps.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|                                                                   |
|                   [Celebration animation]                         |
|                                                                   |
|                     Session Complete!                             |
|                                                                   |
|                                                                   |
|   +----------------+  +----------------+  +----------------+      |
|   |                |  |                |  |                |      |
|   | [StatCard]     |  | [StatCard]     |  | [StatCard]     |      |
|   |                |  |                |  |                |      |
|   |      15        |  |       3        |  |      87%       |      |
|   |    tasks       |  |    tablets     |  |   accuracy     |      |
|   |  completed     |  |    helped      |  |                |      |
|   |                |  |                |  |                |      |
|   +----------------+  +----------------+  +----------------+      |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   You helped with:                                                |
|                                                                   |
|   +----------------------------------------------------------+   |
|   | [Thumb] YBC 4644 - Old Babylonian letter                 |   |
|   |         Identified 5 signs                               |   |
|   +----------------------------------------------------------+   |
|   | [Thumb] P123456 - Ur III receipt                         |   |
|   |         Marked 3 damage areas                            |   |
|   +----------------------------------------------------------+   |
|   | [Thumb] CBS 10467 - Administrative record                |   |
|   |         Verified 7 transcriptions                        |   |
|   +----------------------------------------------------------+   |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   [Achievement Card: First Session!] <- if unlocked              |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   Want to track your progress?                                    |
|                                                                   |
|   [Button: Create free account]                                   |
|                                                                   |
|   or                                                              |
|                                                                   |
|   [Button: Do more tasks]                                         |
|   [Button: Explore tablets]                                       |
|   [Button: Learn cuneiform]                                       |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| SessionSummary | progress.md | - |
| StatCard | progress.md | variant="lg" |
| Stack | layout.md | space="lg" |
| Button | forms.md | multiple variants |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Create account | Click | (Future: auth flow) |
| Do more tasks | Click | Reset counter, return to J2-S3 |
| Explore tablets | Click | Navigate to archive/explore |
| Learn cuneiform | Click | Navigate to J3-S1 |
| Tablet thumbnail | Click | Navigate to tablet detail |

### Statistics Displayed

| Stat | Description | Source |
|------|-------------|--------|
| Tasks completed | Count of submissions | Session state |
| Tablets helped | Unique tablets | Session state |
| Accuracy | Agreement with others | Calculated |
| Time spent | Session duration | Optional, non-judgmental |

### Account Prompt

**Non-blocking:**
- Appears as suggestion, not modal
- Can be ignored
- "or" clearly separates alternatives

**Value proposition:**
- "Track your progress"
- "Save your contributions"
- "Get recognized"

### Accessibility Notes

- Focus moves to summary on display
- Stats have proper labels
- All actions keyboard accessible
- Celebration animation optional

---

## State Management

### Session State (localStorage)

```javascript
{
  sessionId: "uuid",
  startedAt: timestamp,
  currentTaskIndex: 3,
  completedTasks: [
    { taskId: "t1", answer: "an", duration: 4500, type: "match" },
    { taskId: "t2", answer: "unsure", duration: 8200, type: "unsure" },
    { taskId: "t3", answer: "yes", duration: 3100, type: "validate" }
  ],
  skippedTasks: ["t4"],
  tabletsHelped: ["YBC4644", "P123456"],
  stats: {
    correct: 2,
    unsure: 1,
    skipped: 1
  }
}
```

### Task Prefetch

- Always prefetch next 2 tasks
- Begin prefetch on current task load
- Cancel prefetch on skip (may be same)

---

## Responsive Behavior

### Mobile (< 768px)

**Task Card:**
- Full viewport height
- Sign options in 2x2 grid
- Footer sticks to bottom
- Tablet viewer takes 40% height

**Reward Feedback:**
- Full-width card
- Slides up from bottom

**Summary:**
- Stats stack vertically
- Tablet list scrollable

### Tablet (768-1023px)

- Slightly more compact layout
- Stats remain in row

### Desktop (>= 1024px)

- Centered card (max-width: 640px)
- More whitespace

---

## Error States

### Task Load Failure

```
+------------------------------------------------------------------+
|                                                                   |
|  [Error icon]                                                     |
|                                                                   |
|  Couldn't load the next task.                                     |
|                                                                   |
|  [Button: Try again]     [Button: Skip to next]                   |
|                                                                   |
+------------------------------------------------------------------+
```

### Image Load Failure

- Show placeholder with error message
- Allow skip to proceed
- Retry loads in background

### All Tasks Exhausted

```
+------------------------------------------------------------------+
|                                                                   |
|  [Celebration icon]                                               |
|                                                                   |
|  You've done them all!                                            |
|                                                                   |
|  Amazing dedication. We're preparing more tasks -                 |
|  check back soon for new contributions.                           |
|                                                                   |
|  [Button: View your contributions]                                |
|  [Button: Explore tablets]                                        |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial screenflow |
