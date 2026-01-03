# Task Components

**Component Category:** Core
**Document Version:** 1.0

Task components power the contribution experience, presenting micro-tasks to users and capturing their responses. These components implement the Contribution-Reward Cycle defined in the UX Strategy.

**Design Principles:**
- Immediate, visible feedback for every action
- Clear, unambiguous prompts
- Large touch targets for mobile-first interaction
- No cognitive overload - one decision at a time
- Failure-free design (no "wrong" answers, only data)

---

## TaskCard

### Purpose and Use Cases

TaskCard is the container component for all task types. It provides consistent framing, progress indication, and action controls. Use for:
- Passerby contribution tasks
- Early Learner transcription tasks
- Verification tasks
- Learning exercises

### Anatomy

```
+------------------------------------------+
| Task 3 of 10                     [0:45]  |  <- Header
| [========----------------------]         |  <- Progress
+------------------------------------------+
|                                          |
|  [Task Prompt]                           |
|                                          |
|  +----------------------------------+    |
|  |                                  |    |
|  |     [Task-specific content]      |    |
|  |     (SignMatchTask, etc.)        |    |
|  |                                  |    |
|  +----------------------------------+    |
|                                          |
+------------------------------------------+
|  [I'm not sure]              [Skip ->]   |  <- Footer actions
+------------------------------------------+
```

### HTML Structure

```html
<article
  class="task-card"
  data-task-id="task-123"
  data-task-type="sign-match"
  aria-label="Sign matching task"
>
  <header class="task-card__header">
    <span class="task-card__position">
      Task <span aria-current="step">3</span> of 10
    </span>
    <time class="task-card__timer" aria-label="Time elapsed">0:45</time>
  </header>

  <div
    class="task-card__progress"
    role="progressbar"
    aria-valuenow="3"
    aria-valuemin="0"
    aria-valuemax="10"
    aria-label="Session progress: 3 of 10 tasks"
  >
    <div class="task-card__progress-fill" style="width: 30%"></div>
  </div>

  <div class="task-card__content">
    <p class="task-card__prompt" id="task-prompt">
      Which sign matches the highlighted area?
    </p>

    <!-- Task-specific component inserted here -->
    <div class="task-card__task" aria-describedby="task-prompt">
      <!-- SignMatchTask, BinaryTask, etc. -->
    </div>
  </div>

  <footer class="task-card__footer">
    <button
      type="button"
      class="button"
      data-variant="secondary"
      data-action="unsure"
    >
      I'm not sure
    </button>
    <button
      type="button"
      class="button"
      data-variant="ghost"
      data-action="skip"
    >
      Skip
      <svg aria-hidden="true"><!-- arrow icon --></svg>
    </button>
  </footer>
</article>
```

### Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| fullscreen | Takes full viewport | Mobile Passerby flow |
| card | Contained card | Dashboard embedded |
| inline | Minimal chrome | Learning exercises |

### States

| State | Description |
|-------|-------------|
| loading | Task content loading |
| ready | Awaiting user input |
| submitting | Processing response |
| feedback | Showing result feedback |
| transitioning | Animating to next task |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-task-id | string | Unique task identifier |
| data-task-type | string | Type of task |
| data-position | number | Position in queue |
| data-total | number | Total tasks in session |
| data-show-timer | boolean | Display elapsed time |
| data-show-progress | boolean | Display progress bar |

### Accessibility

- Progress bar has proper ARIA attributes
- Task prompt linked to content via aria-describedby
- Focus managed on task load
- Skip action announced to screen readers
- Timer is informational only (aria-live="polite" for updates)

---

## SignMatchTask

### Purpose and Use Cases

SignMatchTask presents a sign from the tablet and asks the user to identify it from multiple options. This is the primary Passerby task type.

### Anatomy

```
+------------------------------------------+
|  Which sign matches the highlighted area? |
+------------------------------------------+
|                                           |
|        +------------------+               |
|        |   [Sign Image   |               |
|        |    from tablet] |               |
|        +------------------+               |
|                                           |
+------------------------------------------+
|  +--------+  +--------+                   |
|  |  [AN]  |  |  [EN]  |                   |
|  |  god   |  |  lord  |                   |
|  +--------+  +--------+                   |
|  +--------+  +--------+                   |
|  |  [LU]  |  |  [UD]  |                   |
|  |  man   |  |  sun   |                   |
|  +--------+  +--------+                   |
+------------------------------------------+
```

### HTML Structure

```html
<div class="sign-match-task" role="group" aria-label="Sign matching options">
  <!-- Sign image from tablet -->
  <figure class="sign-match-task__target">
    <img
      src="tablet-region-cropped.jpg"
      alt="Cuneiform sign to identify"
      class="sign-match-task__image"
    >
    <figcaption class="visually-hidden">
      Sign from line 1, position 3 of tablet
    </figcaption>
  </figure>

  <!-- Options grid -->
  <div
    class="sign-match-task__options"
    role="radiogroup"
    aria-label="Select the matching sign"
  >
    <label class="sign-option" data-option-id="an">
      <input
        type="radio"
        name="sign-choice"
        value="an"
        class="visually-hidden"
      >
      <span class="sign-option__card">
        <img src="sign-an.svg" alt="" aria-hidden="true">
        <span class="sign-option__name">AN</span>
        <span class="sign-option__meaning">god, sky</span>
      </span>
    </label>

    <label class="sign-option" data-option-id="en">
      <input
        type="radio"
        name="sign-choice"
        value="en"
        class="visually-hidden"
      >
      <span class="sign-option__card">
        <img src="sign-en.svg" alt="" aria-hidden="true">
        <span class="sign-option__name">EN</span>
        <span class="sign-option__meaning">lord</span>
      </span>
    </label>

    <label class="sign-option" data-option-id="lu">
      <input
        type="radio"
        name="sign-choice"
        value="lu"
        class="visually-hidden"
      >
      <span class="sign-option__card">
        <img src="sign-lu.svg" alt="" aria-hidden="true">
        <span class="sign-option__name">LU</span>
        <span class="sign-option__meaning">man, person</span>
      </span>
    </label>

    <label class="sign-option" data-option-id="ud">
      <input
        type="radio"
        name="sign-choice"
        value="ud"
        class="visually-hidden"
      >
      <span class="sign-option__card">
        <img src="sign-ud.svg" alt="" aria-hidden="true">
        <span class="sign-option__name">UD</span>
        <span class="sign-option__meaning">sun, day</span>
      </span>
    </label>
  </div>
</div>
```

### Variants

| Variant | Options | Layout |
|---------|---------|--------|
| default | 4 options | 2x2 grid |
| binary | 2 options | Side-by-side |
| difficult | 6 options | 2x3 grid |

### Option States

| State | Description | Visual |
|-------|-------------|--------|
| default | Unselected | Standard border |
| hover | Mouse over | Subtle highlight |
| focus | Keyboard focus | Focus ring |
| selected | User choice | Bold border, check indicator |
| ai-suggested | AI recommendation | Subtle indicator (not prominent) |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-sign-image | string | URL of sign to identify |
| data-options | string | JSON array of options |
| data-ai-suggestion | string | AI's suggested answer |
| data-show-meanings | boolean | Display sign meanings |

### Accessibility

- Options are radio buttons (single selection)
- Tab navigates between options
- Space/Enter selects focused option
- Selection is immediate (no separate submit)
- Minimum touch target: 72x72px per option
- Screen reader announces option details

### Interaction Behavior

1. User views sign image from tablet
2. User selects one of four options
3. **Immediate visual feedback:**
   - Selected option shows check mark
   - Other options fade slightly
   - Brief scale animation (100ms)
4. Task completion callback fires
5. RewardFeedback component displays

---

## BinaryTask

### Purpose and Use Cases

BinaryTask presents a yes/no or true/false decision. Use for:
- AI suggestion validation ("Does this look correct?")
- Damage identification ("Is this area damaged?")
- Simple verification tasks

### Anatomy

```
+------------------------------------------+
|  Does this AI suggestion look correct?    |
+------------------------------------------+
|                                           |
|  +----------------------------------+     |
|  | AI suggests: This sign is "AN"  |     |
|  |                                  |     |
|  | [Sign image]      [AN reference] |     |
|  +----------------------------------+     |
|                                           |
|  +----------------+  +----------------+   |
|  |                |  |                |   |
|  |  Yes, correct  |  |  No, different |   |
|  |                |  |                |   |
|  +----------------+  +----------------+   |
|                                           |
+------------------------------------------+
```

### HTML Structure

```html
<div class="binary-task" role="group" aria-label="Verification task">
  <!-- AI suggestion context -->
  <div class="binary-task__context">
    <p class="binary-task__suggestion">
      <span class="binary-task__ai-label">AI suggests:</span>
      This sign is "<strong>AN</strong>"
    </p>

    <div class="binary-task__comparison">
      <figure>
        <img src="tablet-sign.jpg" alt="Sign from tablet">
        <figcaption>From tablet</figcaption>
      </figure>
      <figure>
        <img src="sign-an.svg" alt="Reference sign AN">
        <figcaption>AN reference</figcaption>
      </figure>
    </div>
  </div>

  <!-- Binary options -->
  <div
    class="binary-task__options"
    role="radiogroup"
    aria-label="Is this suggestion correct?"
  >
    <label class="binary-option" data-value="yes">
      <input
        type="radio"
        name="binary-choice"
        value="yes"
        class="visually-hidden"
      >
      <span class="binary-option__card">
        <svg aria-hidden="true"><!-- check icon --></svg>
        <span class="binary-option__label">Yes, correct</span>
      </span>
    </label>

    <label class="binary-option" data-value="no">
      <input
        type="radio"
        name="binary-choice"
        value="no"
        class="visually-hidden"
      >
      <span class="binary-option__card">
        <svg aria-hidden="true"><!-- x icon --></svg>
        <span class="binary-option__label">No, different</span>
      </span>
    </label>
  </div>
</div>
```

### Variants

| Variant | Labels | Use Case |
|---------|--------|----------|
| correct | Yes/No | AI validation |
| damage | Damaged/Clear | Damage marking |
| custom | Configurable | Flexible |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-question | string | Question text |
| data-yes-label | string | Affirmative label |
| data-no-label | string | Negative label |
| data-context | string | Additional context HTML |

### Accessibility

- Two large buttons with clear labels
- Keyboard: Tab between, Space/Enter to select
- Minimum button size: 120x60px
- High contrast labels

---

## CountTask

### Purpose and Use Cases

CountTask asks the user to count something visible on the tablet. Use for:
- Line counting
- Sign counting
- Column identification

### Anatomy

```
+------------------------------------------+
|  How many lines of text are visible?      |
+------------------------------------------+
|                                           |
|  +----------------------------------+     |
|  |                                  |     |
|  |     [Tablet image section]       |     |
|  |                                  |     |
|  +----------------------------------+     |
|                                           |
|  +-----+  +-----+  +-----+  +-----+       |
|  |  1  |  |  2  |  |  3  |  | 4+  |       |
|  +-----+  +-----+  +-----+  +-----+       |
|                                           |
+------------------------------------------+
```

### HTML Structure

```html
<div class="count-task" role="group" aria-label="Counting task">
  <!-- Image to count -->
  <figure class="count-task__image">
    <img
      src="tablet-section.jpg"
      alt="Section of tablet showing text lines"
    >
  </figure>

  <!-- Count options -->
  <div
    class="count-task__options"
    role="radiogroup"
    aria-label="Select the number of lines"
  >
    <label class="count-option" data-value="1">
      <input
        type="radio"
        name="count-choice"
        value="1"
        class="visually-hidden"
      >
      <span class="count-option__button">1</span>
    </label>

    <label class="count-option" data-value="2">
      <input
        type="radio"
        name="count-choice"
        value="2"
        class="visually-hidden"
      >
      <span class="count-option__button">2</span>
    </label>

    <label class="count-option" data-value="3">
      <input
        type="radio"
        name="count-choice"
        value="3"
        class="visually-hidden"
      >
      <span class="count-option__button">3</span>
    </label>

    <label class="count-option" data-value="4+">
      <input
        type="radio"
        name="count-choice"
        value="4+"
        class="visually-hidden"
      >
      <span class="count-option__button">4+</span>
    </label>
  </div>
</div>
```

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-question | string | What to count |
| data-min | number | Minimum value |
| data-max | number | Maximum value (+ for "or more") |
| data-step | number | Value increments |

### Accessibility

- Large number buttons (minimum 60x60px)
- Clear focus states
- Semantic radio group

---

## TaskQueue

### Purpose and Use Cases

TaskQueue manages the list of pending tasks and provides queue visualization for users who want to see upcoming work. Use for:
- Early Learner task selection
- Expert review queue
- Progress visualization

### Anatomy

```
+------------------------------------------+
| UP NEXT                                  |
+------------------------------------------+
| 1. [Sign match] YBC 4644         (~30s)  |  <- Current
|    ===============================        |
| 2. [Transcribe] P123456          (~2min) |
| 3. [Verify] CBS 10467            (~1min) |
| 4. [Sign match] BM 106056        (~30s)  |
+------------------------------------------+
```

### HTML Structure

```html
<aside class="task-queue" aria-label="Task queue">
  <header class="task-queue__header">
    <h2>Up Next</h2>
    <span class="task-queue__count">4 tasks remaining</span>
  </header>

  <ol class="task-queue__list" role="list">
    <li
      class="task-queue__item"
      data-task-id="task-1"
      data-status="current"
      aria-current="true"
    >
      <span class="task-queue__type">Sign match</span>
      <span class="task-queue__tablet">YBC 4644</span>
      <span class="task-queue__estimate">~30s</span>
      <div class="task-queue__progress" role="progressbar" aria-valuenow="50">
        <!-- Progress bar for current task -->
      </div>
    </li>

    <li class="task-queue__item" data-task-id="task-2">
      <span class="task-queue__type">Transcribe</span>
      <span class="task-queue__tablet">P123456</span>
      <span class="task-queue__estimate">~2min</span>
    </li>

    <li class="task-queue__item" data-task-id="task-3">
      <span class="task-queue__type">Verify</span>
      <span class="task-queue__tablet">CBS 10467</span>
      <span class="task-queue__estimate">~1min</span>
    </li>

    <li class="task-queue__item" data-task-id="task-4">
      <span class="task-queue__type">Sign match</span>
      <span class="task-queue__tablet">BM 106056</span>
      <span class="task-queue__estimate">~30s</span>
    </li>
  </ol>
</aside>
```

### Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| minimal | Just progress indicator | Passerby flow |
| list | Shows upcoming tasks | Early Learner |
| selectable | Can choose next task | Expert queue |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-tasks | string | JSON task array |
| data-current | string | Current task ID |
| data-selectable | boolean | Allow task selection |
| data-show-estimates | boolean | Show time estimates |

### Accessibility

- Ordered list semantics
- Current task marked with aria-current
- Clickable items (if selectable) are buttons
- Progress announced for screen readers

---

## Task Footer Actions

### "I'm Not Sure" Pattern

This is a critical interaction that must feel positive:

```html
<button
  type="button"
  class="button"
  data-variant="secondary"
  data-action="unsure"
  aria-describedby="unsure-explanation"
>
  I'm not sure
</button>
<span id="unsure-explanation" class="visually-hidden">
  Mark this task as uncertain. Uncertainty is valuable data.
</span>
```

**Behavior:**
1. User clicks "I'm not sure"
2. Task marked with uncertainty flag
3. Special RewardFeedback variant shows:
   - "Uncertainty is helpful!"
   - Explains why flagging difficulty matters
4. Counts toward session progress
5. User continues to next task

### "Skip" Pattern

Skip is secondary and does not count as contribution:

```html
<button
  type="button"
  class="button"
  data-variant="ghost"
  data-action="skip"
>
  Skip
  <svg aria-hidden="true"><!-- arrow --></svg>
</button>
```

**Behavior:**
1. User clicks "Skip"
2. No feedback shown (silent skip)
3. Task goes back to queue (may reappear later)
4. Does not count toward session progress
5. Next task loads immediately

---

## Usage Guidelines

### Task Card Composition

```html
<article class="task-card" data-task-type="sign-match">
  <header class="task-card__header">...</header>
  <div class="task-card__progress">...</div>

  <div class="task-card__content">
    <p class="task-card__prompt">Which sign matches?</p>

    <!-- Inject task-specific component -->
    <div class="sign-match-task">
      ...
    </div>
  </div>

  <footer class="task-card__footer">
    <button data-action="unsure">I'm not sure</button>
    <button data-action="skip">Skip</button>
  </footer>
</article>
```

### Task Flow State Machine

```
[Loading] --> [Ready] --> [Submitting] --> [Feedback] --> [Transitioning]
                 |                              |
                 +--- [Skip] ------------------->
                 |
                 +--- [Unsure] --> [Unsure Feedback] --> [Transitioning]
```

### Performance Requirements

- Task loads in < 500ms
- Next task prefetched during current
- Selection feedback in < 200ms
- Transition animation: 300ms

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial task components |
