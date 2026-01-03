# J2: Passerby First Contribution Journey

**Document Type:** Journey PRD
**Priority:** P0 (Critical Path - Most Important Journey)
**Status:** Ready
**Estimated Complexity:** L
**Dependencies:** L1-L4 (All Layer PRDs)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| User Type | Passerby |
| Journey Scope | CTA Click -> First Task -> Session Complete -> Return Prompt |
| UX Strategy Reference | Section 2.2: Critical Path W-P1; Section 1.3: Contribution-Reward Cycle |
| Brief Reference | Primary KPI - "Number of contributions per hour" |

---

## Journey Narrative

A curious visitor clicks "Try it now" from the marketing page and lands in the contribution experience. Within 60 seconds, they complete their first micro-task without creating an account, learning anything complex, or feeling lost. The experience feels rewarding and simple - like a well-designed mobile game, but with genuine scholarly impact.

They complete 5-10 tasks, learning a tiny bit about cuneiform along the way through optional "fun facts." At the end of their session, they see concrete evidence of their impact and are gently invited to create an account or continue. Whether they do or not, they leave feeling that their contribution mattered.

**This journey is the most critical for platform growth.** It must be optimized for:
- Minimal friction (< 60 seconds to first contribution)
- Maximum reward (immediate, concrete feedback)
- Zero expertise required (anyone can succeed)
- Addictive flow (just one more task)

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Experience | Time to first task completion | < 60 seconds |
| Experience | User reports feeling "I made a real contribution" | > 80% |
| Behavior | Average tasks completed per session | > 5 |
| Behavior | Session completion rate (reach summary) | > 70% |
| Behavior | Return within 7 days | > 20% |
| KPI | Contributions per hour | > 30 (target) |

---

## Journey Map

### Stage 1: Entry Point

**User Goal:** Start contributing immediately

**System Response:**
- No account wall
- Brief orientation (< 15 seconds, skippable)
- First task loads automatically

**Flow:**

```
Marketing CTA Click
       |
       v
+------------------+
| Brief Welcome    |  <- "Welcome to Glintstone!"
| (3 seconds)      |     Auto-advances or skip
+------------------+
       |
       v
+------------------+
| Mini Tutorial    |  <- "Here's what you'll do..."
| (10-15 seconds)  |     Skippable, shows example
+------------------+
       |
       v
+------------------+
| First Task       |  <- Guaranteed easy task
| Loads            |
+------------------+
```

**Welcome Screen Specification:**

```
+--------------------------------------------------+
|                                                   |
|   [Glintstone logo - small]                       |
|                                                   |
|   Welcome to Glintstone                           |
|                                                   |
|   You're about to help decode ancient history.    |
|   No experience needed. Let's begin.              |
|                                                   |
|               [Continue ->]                       |
|                                                   |
|   (Auto-continues in 3 seconds)                   |
|                                                   |
+--------------------------------------------------+
```

**Mini Tutorial Specification:**

```
+--------------------------------------------------+
|                                                   |
|   YOUR FIRST TASK                                 |
|                                                   |
|   +--------------------+                          |
|   | [Example task      |                          |
|   |  showing sign      |                          |
|   |  and options]      |                          |
|   +--------------------+                          |
|                                                   |
|   See this ancient symbol? Just pick which        |
|   reference sign it matches. That's it!           |
|                                                   |
|   - Your choices help train our AI               |
|   - Experts review everything                    |
|   - There's no wrong answer                      |
|                                                   |
|           [Got it, let's start!]                  |
|                                                   |
|   [Skip tutorial]                                 |
|                                                   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] No account creation required
- [ ] Welcome screen auto-advances after 3 seconds
- [ ] Tutorial is skippable with single click
- [ ] Tutorial shows interactive example, not video
- [ ] "No wrong answer" messaging reduces anxiety
- [ ] First task is pre-loaded during tutorial
- [ ] Total time from click to first task < 15 seconds

---

### Stage 2: First Task (Critical)

**User Goal:** Successfully complete first contribution

**System Response:**
- Guaranteed easy task (highest AI confidence)
- Large, clear touch targets
- Immediate positive feedback

**First Task Requirements:**

1. **Task Type:** Sign matching (4 options)
2. **Difficulty:** Easiest available (well-preserved, high AI confidence)
3. **Success Rate:** Must be achievable by 95%+ of users
4. **One "correct" option that is visually obviously closest**

**Task Screen Specification:**

```
+--------------------------------------------------+
|  Task 1 of 10                           [0:00]   |
|  [==========-----------------------------]       |
+--------------------------------------------------+
|                                                   |
|   Which sign matches the highlighted area?        |
|                                                   |
|   +---------------------------+                   |
|   |                           |                   |
|   |   [Tablet image with      |                   |
|   |    highlighted region     |                   |
|   |    pulsing gently]        |                   |
|   |                           |                   |
|   +---------------------------+                   |
|                                                   |
+--------------------------------------------------+
|   +--------+  +--------+  +--------+  +--------+  |
|   |  [AN]  |  |  [EN]  |  |  [LU]  |  |  [UD]  |  |
|   |        |  |        |  |        |  |        |  |
|   +--------+  +--------+  +--------+  +--------+  |
+--------------------------------------------------+
|   [I'm not sure]                      [Skip ->]   |
+--------------------------------------------------+
```

**Interaction Flow:**

1. User views highlighted region on tablet
2. User selects one of four sign options
3. Immediate visual feedback (checkmark, option highlights gold)
4. Brief pause (500ms) for satisfaction
5. Reward feedback appears
6. Next task auto-loads (or user clicks continue)

**Acceptance Criteria:**
- [ ] First task is always "easy" difficulty
- [ ] Options are visually distinct
- [ ] Correct option is objectively identifiable
- [ ] Selection feedback < 200ms
- [ ] Touch targets minimum 72px
- [ ] "I'm not sure" option always available
- [ ] Skip option available but visually secondary

---

### Stage 3: Task Loop (Core Experience)

**User Goal:** Build momentum and feel productive

**System Response:**
- Seamless task-to-task flow
- Variety in tasks (different tablets, different signs)
- Progress indication
- Occasional rewards (fun facts, milestone celebrations)

**Task Loop Flow:**

```
Complete Task
     |
     v
+------------------+
| Reward Feedback  |  <- "Great job!" + optional fun fact
| (1-2 seconds)    |
+------------------+
     |
     v
+------------------+
| Next Task Loads  |  <- Already pre-fetched
| (instant)        |
+------------------+
     |
     v
[Repeat until session complete or user exits]
```

**Reward Feedback Patterns:**

Every task gets brief positive feedback. Rotate between:

| Frequency | Feedback Type | Example |
|-----------|---------------|---------|
| 70% | Simple confirmation | "Got it!" / "Nice!" / "Thanks!" |
| 15% | Consensus match | "You matched 7 other contributors!" |
| 10% | Fun fact | "This tablet is 4,000 years old!" |
| 5% | Sign learning | "That's the sign 'AN' - it means 'sky'" |

**Fun Facts Pool (examples for L2 fixtures):**

- "This tablet is from ancient Babylon, around 1800 BCE."
- "The sign you just identified means 'god' in Sumerian."
- "This tablet was found in modern-day Iraq in 1923."
- "Cuneiform was used for over 3,000 years."
- "Only about 500 people worldwide can read cuneiform fluently."
- "This might be a letter from a merchant to his business partner."

**Milestone Celebrations:**

| Milestone | Celebration |
|-----------|-------------|
| 5 tasks | "You're on a roll! 5 signs identified." |
| 10 tasks | "Halfway there! You've helped with X tablets." |
| 25 tasks | "Amazing! You've contributed more than most visitors." |
| 50 tasks | "Expert-level dedication! Consider creating an account." |

**Acceptance Criteria:**
- [ ] No loading delay between tasks (prefetch working)
- [ ] Task variety - no two consecutive from same tablet
- [ ] Progress bar updates smoothly
- [ ] Fun facts appear ~15% of tasks (randomized)
- [ ] Milestone celebrations at 5, 10, 25, 50
- [ ] Timer shows elapsed time (non-stressful)

---

### Stage 4: "I'm Not Sure" Flow

**User Goal:** Handle uncertainty without shame

**System Response:**
- Positive reinforcement for honesty
- Explanation of why uncertainty is valuable
- No penalty or negative feedback

**Per hobbyist-feedback-report.md:** "Show me when my uncertainty is valuable data."

**"Not Sure" Response Specification:**

```
+--------------------------------------------------+
|                                                   |
|   [Flag icon]                                     |
|                                                   |
|   Uncertainty is helpful!                         |
|                                                   |
|   When you mark something as unclear, you help    |
|   us identify signs that need expert attention.   |
|   This is real, valuable data.                    |
|                                                   |
|                  [Continue ->]                    |
|                                                   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] "Not sure" counts as a valid contribution
- [ ] Positive messaging (never "wrong" or "skipped")
- [ ] Explanation of why uncertainty helps
- [ ] Contributes to session stats normally

---

### Stage 5: Skip Flow

**User Goal:** Move past a task without engaging

**System Response:**
- Silent skip (no feedback message)
- Move to next task immediately
- Track skip for analytics but don't display

**Skip Behavior:**
- Skip does not count as contribution
- No penalty messaging
- No "are you sure?" confirmation
- Just advances to next task

**Acceptance Criteria:**
- [ ] Skip advances immediately (no feedback)
- [ ] Skip tracked in analytics, not shown to user
- [ ] No guilt messaging ("Don't want to skip, do you?")
- [ ] Skipped tasks can re-appear later in session

---

### Stage 6: Session Momentum

**User Goal:** Feel productive and want to continue

**System Response:**
- Clear progress toward session goal
- Encouraging messaging without pressure
- Natural stopping points

**Session Structure:**

Default session: 10 tasks
- Tasks 1-5: Building confidence
- Task 5: First milestone ("Halfway there!")
- Tasks 6-9: Continued contribution
- Task 10: Session complete prompt

**Mid-Session State:**

```
+--------------------------------------------------+
|  Task 7 of 10                          [4:32]    |
|  [====================-----------]               |
+--------------------------------------------------+
|                                                   |
|   ...task content...                              |
|                                                   |
+--------------------------------------------------+
```

**"Just One More" Pattern:**

At task 10, instead of ending:

```
+--------------------------------------------------+
|                                                   |
|   Session complete! Amazing work.                 |
|                                                   |
|   You've identified 10 signs across 4 tablets.    |
|                                                   |
|   [See your impact]  [Do 10 more]                 |
|                                                   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] Progress bar clearly shows position in session
- [ ] Milestone at task 5 provides encouragement
- [ ] Task 10 offers choice: end or continue
- [ ] "Do more" resets counter but maintains stats
- [ ] Session can be ended at any point

---

### Stage 7: Session Complete

**User Goal:** See impact and feel accomplished

**System Response:**
- Session summary with concrete stats
- Connection to tablets helped
- Optional account creation (soft prompt)
- Clear next-step options

**Session Summary Specification:**

```
+--------------------------------------------------+
|                                                   |
|   [Star burst animation]                          |
|                                                   |
|   Session Complete!                               |
|                                                   |
|   +----------+  +----------+  +----------+        |
|   |    12    |  |    3     |  |   85%    |        |
|   |  tasks   |  | tablets  |  | accuracy |        |
|   +----------+  +----------+  +----------+        |
|                                                   |
+--------------------------------------------------+
|   You helped with:                                |
|                                                   |
|   [thumb] YBC 4644 - Old Babylonian letter        |
|           Identified 5 signs                      |
|                                                   |
|   [thumb] P123456 - Ur III receipt                |
|           Marked 3 regions                        |
|                                                   |
|   [thumb] CBS 10467 - Administrative record       |
|           Verified 4 transcriptions               |
|                                                   |
+--------------------------------------------------+
|                                                   |
|   Want to track your progress?                    |
|                                                   |
|   [Create free account]                           |
|                                                   |
|   or                                              |
|                                                   |
|   [Do more tasks]  [Explore tablets]  [Learn]     |
|                                                   |
+--------------------------------------------------+
```

**Summary Statistics:**

| Stat | Description | Display |
|------|-------------|---------|
| Tasks completed | Total tasks done | Large number |
| Tablets helped | Unique tablets | Large number |
| Accuracy | Agreement with others | Percentage |
| Time spent | Session duration | Small, optional |

**Tablet Connection:**
- Show thumbnails of tablets user contributed to
- Brief description of each tablet
- "Identified X signs" or similar specific impact

**Account Prompt (Non-blocking):**
- Soft prompt, not modal
- Can be dismissed or ignored
- Equal visual weight to "Continue" options

**Acceptance Criteria:**
- [ ] Stats prominently displayed
- [ ] Tablet thumbnails clickable (link to viewer)
- [ ] Account prompt is optional, not blocking
- [ ] Three continuation paths available
- [ ] Celebration animation plays (respects reduced motion)
- [ ] Session data recorded (localStorage for demo)

---

### Stage 8: Return User Recognition

**User Goal:** Return and pick up where they left off

**System Response:**
- Welcome back message
- Resume previous progress (if any)
- Skip tutorial on return

**Return User Flow:**

```
Returning visitor detected
          |
          v
+--------------------------------------------------+
|                                                   |
|   Welcome back!                                   |
|                                                   |
|   Last time you completed 12 tasks               |
|   and helped with 3 tablets.                      |
|                                                   |
|   [Continue where you left off]                   |
|                                                   |
|   [Start fresh]                                   |
|                                                   |
+--------------------------------------------------+
```

**Recognition Triggers:**
- localStorage contains previous session data
- Session is < 7 days old
- At least 1 task was completed

**Acceptance Criteria:**
- [ ] Return users skip tutorial automatically
- [ ] Previous stats shown on welcome back
- [ ] Option to continue or start fresh
- [ ] If > 7 days, treat as new user

---

## Component Dependencies

| Component | Source PRD | Usage in J2 |
|-----------|------------|-------------|
| TaskCard | L4 | Primary task display |
| SignCard | L3 | Sign matching tasks |
| TabletViewer | L3 | Tablet context display |
| ProgressBar | L4 | Session progress |
| RewardFeedback | L4 | Post-task celebration |
| SessionSummary | L4 | End-of-session display |
| TaskQueue | L4 | Task management |
| Design Tokens | L1 | All styling |
| Dummy Tasks | L2 | Task content |

---

## Task Types for Passerby

**Required for Release 1:**

| Task Type | Description | UI Pattern |
|-----------|-------------|------------|
| Sign Match | "Which sign matches?" | 4-option grid |
| Damage ID | "Is this area damaged?" | Binary yes/no |
| AI Validation | "Does this look correct?" | Binary yes/no |
| Line Count | "How many lines?" | Number input |

**UI Patterns:**

**4-Option Sign Match (Primary):**
```
[Sign image from tablet]
[A] [B] [C] [D]
[Not sure] [Skip]
```

**Binary Validation:**
```
[Sign image from tablet]
AI suggests: "This is AN"
[Yes, looks right] [No, different]
[Not sure] [Skip]
```

**Number Input:**
```
[Tablet image with lines]
How many lines of text?
[1] [2] [3] [4+]
[Not sure] [Skip]
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Task fails to load | Show retry button, prefetch next |
| Image fails to load | Show placeholder, skip to next |
| All tasks exhausted | "You've done them all! Come back soon." |
| Session corrupted | Clear and start fresh |
| Network offline | "Offline - your work is saved" |

---

## Accessibility Requirements

- All tasks keyboard navigable (Tab + Enter)
- Screen reader announces task prompt
- Focus management between tasks
- Color not sole indicator of correct/incorrect
- Touch targets 44px minimum
- Reduced motion respected

---

## Performance Requirements

- First task visible < 2 seconds from CTA click
- Task-to-task transition < 500ms
- Images lazy-loaded with placeholders
- Session state saved on each task completion
- Works on 3G connection (images compressed)

---

## Analytics Events (Future)

| Event | Data |
|-------|------|
| session_start | user_id (if any), entry_point |
| task_complete | task_id, task_type, response, duration_ms |
| task_skip | task_id |
| task_unsure | task_id |
| session_complete | tasks_completed, duration_ms |
| account_prompt_shown | session_tasks_completed |
| account_created | session_tasks_completed |

---

## Out of Scope

- Account creation flow (show prompt only)
- Persistent user profiles (localStorage for demo)
- Real contribution submission (dummy data)
- Accuracy calculation against ground truth
- Social sharing features
- Push notifications

---

## Testing Requirements

**User Flow Tests:**
- [ ] Complete 10-task session without errors
- [ ] Skip multiple tasks in a row
- [ ] Mark multiple tasks as "not sure"
- [ ] Return user flow works correctly
- [ ] Session resume after page refresh

**Performance Tests:**
- [ ] Time to first task < 2 seconds
- [ ] Task transition < 500ms
- [ ] Session state persists across refresh

**Accessibility Tests:**
- [ ] Complete session using only keyboard
- [ ] Screen reader announces all prompts
- [ ] Focus management is correct

**Edge Cases:**
- [ ] Very fast completion (< 30 seconds total)
- [ ] Very slow completion (> 30 minutes)
- [ ] Rapid skip of all tasks
- [ ] Returning after 30+ days

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
