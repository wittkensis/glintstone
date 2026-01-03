# Progress and Feedback Components

**Component Category:** Core
**Document Version:** 1.0

Progress and feedback components implement the Contribution-Reward Cycle, providing users with immediate, positive feedback for their contributions and clear visualization of their progress.

**Design Principles:**
- Celebrate every contribution
- Make progress visible and concrete
- Educate without lecturing
- Reward honest uncertainty
- Never punish or shame

---

## ProgressBar

### Purpose and Use Cases

ProgressBar visualizes progress toward a goal as a linear fill. Use for:
- Session progress (task 3 of 10)
- Tablet completion percentage
- Learning module progress
- Skill development tracking

### Anatomy

```
Linear:
[========----------------------] 30%

Segmented:
[*][*][*][ ][ ][ ][ ][ ][ ][ ]
```

### HTML Structure

```html
<!-- Linear progress bar -->
<div
  class="progress-bar"
  role="progressbar"
  aria-valuenow="30"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-label="Session progress: 3 of 10 tasks complete"
>
  <div class="progress-bar__track">
    <div
      class="progress-bar__fill"
      style="width: 30%"
    ></div>
  </div>
  <span class="progress-bar__label">3 of 10</span>
</div>

<!-- Segmented progress bar -->
<div
  class="progress-bar"
  data-variant="segmented"
  role="progressbar"
  aria-valuenow="3"
  aria-valuemin="0"
  aria-valuemax="10"
  aria-label="3 of 10 tasks complete"
>
  <div class="progress-bar__segments">
    <span class="progress-bar__segment" data-filled="true"></span>
    <span class="progress-bar__segment" data-filled="true"></span>
    <span class="progress-bar__segment" data-filled="true"></span>
    <span class="progress-bar__segment"></span>
    <span class="progress-bar__segment"></span>
    <span class="progress-bar__segment"></span>
    <span class="progress-bar__segment"></span>
    <span class="progress-bar__segment"></span>
    <span class="progress-bar__segment"></span>
    <span class="progress-bar__segment"></span>
  </div>
</div>
```

### Variants

| Variant | Visual | Use Case |
|---------|--------|----------|
| linear | Continuous fill | General progress |
| segmented | Individual segments | Discrete steps |
| slim | Thin bar, no label | Inline/compact |
| thick | Bold bar with label | Primary indicator |

### States

| State | Description | Animation |
|-------|-------------|-----------|
| default | Static display | None |
| updating | Value changing | Smooth fill transition |
| milestone | Hit milestone value | Pulse/glow effect |
| complete | 100% reached | Celebration animation |

### Props/Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| data-variant | string | "linear" | Visual variant |
| data-value | number | 0 | Current value |
| data-max | number | 100 | Maximum value |
| data-show-label | boolean | true | Display text label |
| data-label-format | string | "{value} of {max}" | Label template |
| data-milestones | string | "" | Milestone values (comma-separated) |
| data-animated | boolean | true | Animate changes |

### Accessibility

- Uses role="progressbar" with aria-valuenow, min, max
- aria-label provides context for screen readers
- Visual progress does not rely on color alone
- Animation can be disabled (prefers-reduced-motion)

### Behavior

**Animation Timing:**
- Fill transitions: 300ms ease-out
- Milestone pulse: 500ms
- Complete celebration: 800ms

**Milestone Events:**
- Emit event when milestone reached
- Trigger celebration animation
- Can trigger RewardFeedback component

---

## ProgressCircle

### Purpose and Use Cases

ProgressCircle shows progress as a circular indicator. Use for:
- Tablet completion (compact display)
- Skill level indicators
- Countdown timers (optional)

### Anatomy

```
    ___
   /   \
  |  3  |
  | /10 |
   \___/
```

### HTML Structure

```html
<div
  class="progress-circle"
  role="progressbar"
  aria-valuenow="30"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-label="30% complete"
>
  <svg
    class="progress-circle__svg"
    viewBox="0 0 36 36"
    aria-hidden="true"
  >
    <!-- Background circle -->
    <path
      class="progress-circle__track"
      d="M18 2.0845
         a 15.9155 15.9155 0 0 1 0 31.831
         a 15.9155 15.9155 0 0 1 0 -31.831"
      fill="none"
      stroke-width="3"
    />
    <!-- Progress arc -->
    <path
      class="progress-circle__fill"
      d="M18 2.0845
         a 15.9155 15.9155 0 0 1 0 31.831
         a 15.9155 15.9155 0 0 1 0 -31.831"
      fill="none"
      stroke-width="3"
      stroke-dasharray="30, 100"
    />
  </svg>

  <div class="progress-circle__content">
    <span class="progress-circle__value">3</span>
    <span class="progress-circle__separator">/</span>
    <span class="progress-circle__max">10</span>
  </div>
</div>
```

### Variants

| Variant | Size | Content |
|---------|------|---------|
| sm | 40px | Percentage only |
| md | 64px | Value + max |
| lg | 96px | Value + label |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-value | number | Current value |
| data-max | number | Maximum value |
| data-size | string | Size variant |
| data-show-text | boolean | Show center text |

### Accessibility

- Same ARIA as ProgressBar
- SVG is decorative (aria-hidden)
- Text content provides accessible value

---

## ConfidenceMeter

### Purpose and Use Cases

ConfidenceMeter displays the confidence level of AI-generated or crowd-aggregated content. Use for:
- Transcription line confidence
- Sign identification confidence
- Overall tablet confidence score

### Anatomy

```
Compact (dot):
[*]   <- Colored indicator only

Standard (bar):
[====----] 65%

Detailed (full):
+---------------------------+
| Confidence: Likely (72%)  |
| [=========-------]        |
| AI + 8 contributors       |
+---------------------------+
```

### HTML Structure

```html
<!-- Compact variant -->
<span
  class="confidence-meter"
  data-variant="compact"
  data-level="65"
  aria-label="Confidence: Likely, 65%"
>
  <span class="confidence-meter__dot" data-confidence="likely"></span>
</span>

<!-- Standard variant -->
<div
  class="confidence-meter"
  data-variant="standard"
  role="meter"
  aria-valuenow="65"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-label="Confidence: 65%"
>
  <div class="confidence-meter__bar">
    <div
      class="confidence-meter__fill"
      data-confidence="likely"
      style="width: 65%"
    ></div>
  </div>
  <span class="confidence-meter__value">65%</span>
</div>

<!-- Detailed variant -->
<div class="confidence-meter" data-variant="detailed">
  <div class="confidence-meter__header">
    <span class="confidence-meter__label">Confidence:</span>
    <span class="confidence-meter__level" data-confidence="likely">
      Likely (72%)
    </span>
  </div>

  <div
    class="confidence-meter__bar"
    role="meter"
    aria-valuenow="72"
    aria-valuemin="0"
    aria-valuemax="100"
  >
    <div
      class="confidence-meter__fill"
      data-confidence="likely"
      style="width: 72%"
    ></div>
  </div>

  <span class="confidence-meter__source">
    AI + 8 contributors
  </span>
</div>
```

### Confidence Levels

| Level | Range | Label | Visual Indicator |
|-------|-------|-------|------------------|
| uncertain | 0-20% | Uncertain | + Question mark icon |
| possible | 21-50% | Possible | + Tilde icon |
| likely | 51-75% | Likely | + Single check icon |
| confident | 76-90% | Confident | + Double check icon |
| verified | 91-100% | Verified | + Shield icon |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-level | number | 0-100 confidence |
| data-variant | string | compact/standard/detailed |
| data-source | string | ai/crowd/expert/aggregated |
| data-show-icon | boolean | Display level icon |
| data-animated | boolean | Animate on change |

### Accessibility

- Uses role="meter" (or progressbar if role unsupported)
- Color is NEVER the only indicator (icons required)
- Tooltip explains what confidence means
- Screen reader announces level name and percentage

---

## RewardFeedback

### Purpose and Use Cases

RewardFeedback provides immediate positive feedback after task completion. This is the "reward" part of the Contribution-Reward Cycle.

### Anatomy

```
+----------------------------------+
|  [Icon]  Primary message         |
|                                  |
|  Secondary explanation or        |
|  fun fact goes here.             |
|                                  |
|  [Optional action] [Continue ->] |
+----------------------------------+
```

### HTML Structure

```html
<aside
  class="reward-feedback"
  data-type="success"
  role="status"
  aria-live="polite"
>
  <div class="reward-feedback__icon" aria-hidden="true">
    <svg><!-- checkmark icon --></svg>
  </div>

  <div class="reward-feedback__content">
    <p class="reward-feedback__message">
      Great job!
    </p>
    <p class="reward-feedback__detail">
      Your answer matched 7 other contributors.
    </p>
  </div>

  <div class="reward-feedback__actions">
    <button
      type="button"
      class="button"
      data-variant="primary"
      data-action="continue"
    >
      Continue
      <svg aria-hidden="true"><!-- arrow icon --></svg>
    </button>
  </div>
</aside>
```

### Variants

| Type | Icon | Primary Message | Secondary |
|------|------|-----------------|-----------|
| success | Checkmark | "Great job!" | Consensus match info |
| consensus | Star | "You matched the experts!" | Sign learning opportunity |
| valuable-uncertainty | Flag | "Uncertainty is helpful!" | Explanation of value |
| milestone | Trophy | "10 tasks complete!" | Impact summary |
| fun-fact | Lightbulb | "Did you know?" | Educational tidbit |

### States

| State | Description |
|-------|-------------|
| entering | Sliding/fading in |
| visible | Displayed to user |
| exiting | Sliding/fading out |
| dismissed | Removed from DOM |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-type | string | Feedback variant |
| data-message | string | Primary message |
| data-detail | string | Secondary message |
| data-duration | number | Auto-dismiss ms (0 = manual) |
| data-action-label | string | Continue button text |

### Animation Specification

**Enter Animation:**
- Slide up from bottom (mobile) or fade in (desktop)
- Duration: 250ms
- Easing: ease-out

**Icon Animation:**
- Checkmark: draw stroke animation
- Star: scale + rotate
- Trophy: bounce
- Duration: 400ms
- Easing: bounce (cubic-bezier(0.34, 1.56, 0.64, 1))

**Exit Animation:**
- Fade out + slide down
- Duration: 200ms
- Easing: ease-in

**Reduced Motion:**
- Replace all animations with simple fade
- Duration: 150ms

### Accessibility

- Uses role="status" and aria-live="polite"
- Announced to screen readers on appear
- Continue button receives focus
- Escape key dismisses
- Auto-dismiss pauses on hover/focus

### Content Guidelines

**Message Tone:**
- Always positive, never condescending
- Specific over generic ("matched 7 others" vs "good job")
- Educational when appropriate
- Never use "correct" or "wrong"

**Fun Facts (appear ~15% of tasks):**
- Maximum 15 words
- Relate to the current tablet/sign when possible
- Mix of history, linguistics, culture
- Avoid technical jargon

---

## SessionSummary

### Purpose and Use Cases

SessionSummary displays end-of-session impact and encourages continued engagement. Use for:
- End of contribution session
- Achievement unlocked moments
- Return user welcome back

### Anatomy

```
+--------------------------------------------------+
|                                                   |
|  [Celebration Animation]                          |
|                                                   |
|  Session Complete!                                |
|                                                   |
|  +------+  +------+  +------+                     |
|  |  15  |  |  3   |  |  87% |                     |
|  | tasks|  |tablets|  |accuracy|                  |
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

### HTML Structure

```html
<section class="session-summary" aria-label="Session summary">
  <header class="session-summary__header">
    <div class="session-summary__celebration" aria-hidden="true">
      <!-- Animation container -->
    </div>
    <h1 class="session-summary__title">Session Complete!</h1>
  </header>

  <!-- Statistics -->
  <div class="session-summary__stats">
    <article class="stat-card">
      <span class="stat-card__value">15</span>
      <span class="stat-card__label">tasks completed</span>
    </article>
    <article class="stat-card">
      <span class="stat-card__value">3</span>
      <span class="stat-card__label">tablets helped</span>
    </article>
    <article class="stat-card">
      <span class="stat-card__value">87%</span>
      <span class="stat-card__label">accuracy</span>
    </article>
  </div>

  <!-- Tablets helped -->
  <section class="session-summary__tablets" aria-label="Tablets you helped">
    <h2>You helped with:</h2>
    <ul class="session-summary__tablet-list">
      <li class="tablet-contribution">
        <img src="tablet-thumb.jpg" alt="" class="tablet-contribution__thumb">
        <div class="tablet-contribution__info">
          <strong>YBC 4644</strong>
          <span>Identified 5 signs</span>
        </div>
      </li>
      <!-- More tablets -->
    </ul>
  </section>

  <!-- Achievement (if any) -->
  <section class="session-summary__achievement" aria-label="Achievement unlocked">
    <div class="achievement-card" data-new="true">
      <svg class="achievement-card__icon" aria-hidden="true">
        <!-- Trophy icon -->
      </svg>
      <span class="achievement-card__name">First Session!</span>
    </div>
  </section>

  <!-- Call to action -->
  <footer class="session-summary__cta">
    <p class="session-summary__prompt">Want to track your progress?</p>

    <button type="button" class="button" data-variant="secondary">
      Create free account
    </button>

    <div class="session-summary__actions">
      <button type="button" class="button" data-variant="primary">
        Do more tasks
      </button>
      <button type="button" class="button" data-variant="ghost">
        Explore tablets
      </button>
      <button type="button" class="button" data-variant="ghost">
        Learn cuneiform
      </button>
    </div>
  </footer>
</section>
```

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-tasks | number | Tasks completed |
| data-tablets | number | Tablets helped |
| data-accuracy | number | Accuracy percentage |
| data-duration | number | Session duration (ms) |
| data-achievements | string | JSON achievement data |
| data-show-account-prompt | boolean | Show account CTA |

### Accessibility

- Semantic sections with labels
- Statistics are live regions
- Focus moves to summary on display
- All actions keyboard accessible

---

## StatCard

### Purpose and Use Cases

StatCard displays a single statistic with context. Use for:
- Session summary statistics
- Dashboard metrics
- Profile statistics

### Anatomy

```
+----------+
|    15    |  <- Value (large)
|  tasks   |  <- Label
| completed|
+----------+
```

### HTML Structure

```html
<article class="stat-card">
  <span class="stat-card__value" aria-describedby="stat-1-label">
    15
  </span>
  <span class="stat-card__label" id="stat-1-label">
    tasks completed
  </span>
</article>
```

### Variants

| Variant | Size | Use Case |
|---------|------|----------|
| sm | 80px | Inline stats |
| md | 120px | Default |
| lg | 160px | Hero stats |
| icon | with icon | Visual category |

### Props/Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| data-value | string | Stat value |
| data-label | string | Stat label |
| data-icon | string | Optional icon name |
| data-trend | string | up/down/neutral |

---

## Usage Guidelines

### Feedback Timing

| Event | Feedback | Timing |
|-------|----------|--------|
| Task selection | Selection highlight | Immediate |
| Task completion | RewardFeedback | < 200ms |
| Milestone hit | Milestone variant | With task feedback |
| Session complete | SessionSummary | After final feedback |

### Animation Sequencing

```
[Task Complete]
    |
    v (0ms)
[Selection Feedback]
    |
    v (200ms)
[RewardFeedback Enters]
    |
    v (2000ms or user action)
[RewardFeedback Exits]
    |
    v (300ms)
[Next Task Enters]
```

### Reduced Motion Support

All components must respect `prefers-reduced-motion`:
- Replace motion animations with opacity fades
- Shorten durations to 150ms maximum
- Remove bouncing/scaling effects
- Keep feedback timing the same

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial progress components |
