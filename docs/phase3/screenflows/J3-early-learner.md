# J3: Early Learner Curriculum Preview Screenflow

**Journey:** Early Learner Onboarding / Curriculum Preview
**User Type:** Early Learner (motivated Passerby)
**Priority:** P1 (Should Have)
**PRD Reference:** J3-early-learner-onboarding.md

---

## Journey Overview

```
[Curriculum Landing] --> [Module 1 Preview] --> [Lesson Content] --> [Practice] --> [Preview Complete]
                                                      |                    |
                                                      +----[Continue]------+
                                                                           |
                                                                           v
                                                                  [Email Signup]
                                                                           |
                                                                           v
                                                           [Return to Contribute/Explore]
```

**Goal:** Show users what learning cuneiform involves and validate interest in curriculum features.

**Release 1 Scope:** Preview only (not full curriculum). 5-minute experience with email capture.

**Success Metrics:**
- Preview module interaction rate: > 50%
- Early access signup rate: > 20%
- User understands curriculum scope: > 80% clarity

---

## Screen 1: Curriculum Landing

### Screen ID
`J3-S1-landing`

### Entry Points
- Marketing page "Start learning" CTA
- Passerby session summary "Learn more"
- Navigation "Learn" tab

### User Goal
Understand the learning pathway and what commitment is involved.

### Wireframe

```
+------------------------------------------------------------------+
| [Header: default]                                                 |
+------------------------------------------------------------------+
|                                                                   |
|                   LEARN TO READ CUNEIFORM                         |
|                                                                   |
|          Master humanity's oldest writing system.                 |
|          From first signs to full translations.                   |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   LEARNING PATHWAY                                                |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  [1] FOUNDATIONS                          [Unlocked]     |   |
|   |      What is cuneiform?                                  |   |
|   |      Time: 2-3 hours | 5 lessons                         |   |
|   |      |                                                   |   |
|   |      v                                                   |   |
|   |  [2] BASIC SIGNS                          [Coming soon]  |   |
|   |      25 essential signs                                  |   |
|   |      Time: 5-10 hours                                    |   |
|   |      |                                                   |   |
|   |      v                                                   |   |
|   |  [3] READING WORDS                        [Coming soon]  |   |
|   |      Vocabulary building                                 |   |
|   |      Time: 5-10 hours                                    |   |
|   |      |                                                   |   |
|   |      v                                                   |   |
|   |  [4] READING LINES                        [Coming soon]  |   |
|   |      Complete sentences                                  |   |
|   |      Time: 10-20 hours                                   |   |
|   |      |                                                   |   |
|   |      v                                                   |   |
|   |  [5] TRANSLATION                          [Coming soon]  |   |
|   |      From text to meaning                                |   |
|   |      Time: 10-20 hours                                   |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   Total: 30-60 hours to basic reading competency                  |
|                                                                   |
|                                                                   |
|              [Button: Preview Module 1: Foundations]              |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Header | navigation.md | default |
| Stack | layout.md | space="lg" |
| Button | forms.md | variant="primary", size="lg" |

### Module Card Anatomy

```
+----------------------------------------------------------+
|  [Number Circle]  MODULE TITLE           [Status Badge]   |
|                   Description                             |
|                   Time: X hours | N lessons               |
|                   |                                       |
|                   v (connector line)                      |
+----------------------------------------------------------+
```

### Status Badges

| Status | Display | Interaction |
|--------|---------|-------------|
| Unlocked | "Preview available" (clickable) | Opens module |
| Coming soon | "Coming soon" (muted) | No interaction |
| Locked | "Complete previous" (muted) | Tooltip explains |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Module 1 | Click | Navigate to J3-S2 |
| "Preview Module 1" | Click | Navigate to J3-S2 |
| Other modules | None | Visual only (coming soon) |

### Accessibility Notes

- Pathway is semantic list
- Module status announced
- Time estimates help planning
- Focus on primary CTA

---

## Screen 2: Module Preview Intro

### Screen ID
`J3-S2-module-intro`

### Entry Points
- "Preview Module 1" click from landing

### User Goal
Start learning immediately.

### Wireframe

```
+------------------------------------------------------------------+
| [< Back to Curriculum]                                            |
+------------------------------------------------------------------+
|                                                                   |
|                  MODULE 1: FOUNDATIONS                            |
|                                                                   |
|                  What is Cuneiform?                               |
|                                                                   |
|                  Lesson 1 of 5    [=====-----------------]        |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|                                                                   |
|          +----------------------------------------+               |
|          |                                        |               |
|          |  [Image: Close-up of cuneiform         |               |
|          |   wedges on clay tablet]               |               |
|          |                                        |               |
|          +----------------------------------------+               |
|                                                                   |
|                                                                   |
|   Cuneiform is the world's oldest known writing system,           |
|   invented in ancient Mesopotamia around 3400 BCE.                |
|                                                                   |
|   The name comes from Latin "cuneus" meaning "wedge" -            |
|   because every mark is made by pressing a wedge-shaped           |
|   reed into soft clay.                                            |
|                                                                   |
|                                                                   |
|                        [Button: Continue ->]                      |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Breadcrumb | navigation.md | minimal |
| ProgressBar | progress.md | variant="linear" |
| Stack | layout.md | space="lg" |
| Button | forms.md | variant="primary" |

### Lesson Content Pattern

Each lesson screen follows this pattern:
1. Module/lesson header with progress
2. Visual content (image or illustration)
3. Educational text (max 100 words)
4. Continue button

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Back link | Click | Return to J3-S1 |
| Continue | Click | Navigate to J3-S3 |

---

## Screen 3: The Wedges (Interactive)

### Screen ID
`J3-S3-wedges`

### Entry Points
- Continue from J3-S2

### User Goal
Understand basic wedge shapes through interaction.

### Wireframe

```
+------------------------------------------------------------------+
| [< Back to Curriculum]                                            |
+------------------------------------------------------------------+
|                                                                   |
|                  Lesson 2 of 5    [=======--------------]         |
|                                                                   |
|                        THE WEDGES                                 |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   Cuneiform has four basic wedge types:                          |
|                                                                   |
|   +--------+  +--------+  +--------+  +--------+                  |
|   |   |    |  |  --    |  |   /    |  |   \    |                  |
|   |   |    |  |        |  |  /     |  |    \   |                  |
|   | Vertical|  |Horizontal|  |Diagonal|  |Diagonal|                 |
|   +--------+  +--------+  +--------+  +--------+                  |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   PRACTICE: Which direction does this wedge point?                |
|                                                                   |
|          +----------------------+                                 |
|          |                      |                                 |
|          |    [Large wedge      |                                 |
|          |     image]           |                                 |
|          |                      |                                 |
|          +----------------------+                                 |
|                                                                   |
|   +--------+  +--------+  +--------+  +--------+                  |
|   | Left   |  | Right  |  | Up     |  | Down   |                  |
|   +--------+  +--------+  +--------+  +--------+                  |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Grid | layout.md | columns="4" |
| SignMatchTask | task.md | (adapted for direction) |
| Button | forms.md | variant="secondary" |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Direction button | Click | Show feedback, then continue |
| Correct answer | Click | "Correct!" + Continue enabled |
| Wrong answer | Click | "Try again" (no penalty) |

### Feedback Pattern

**Correct:**
```
+------------------+
| [Check] Correct! |
|                  |
| [Continue ->]    |
+------------------+
```

**Incorrect:**
```
+------------------+
| That's a         |
| horizontal wedge.|
|                  |
| [Try again]      |
+------------------+
```

No penalty - user can retry.

---

## Screen 4: Signs, Not Letters

### Screen ID
`J3-S4-signs`

### Entry Points
- Continue from J3-S3

### User Goal
Understand cuneiform is logographic, not alphabetic.

### Wireframe

```
+------------------------------------------------------------------+
| [< Back to Curriculum]                                            |
+------------------------------------------------------------------+
|                                                                   |
|                  Lesson 3 of 5    [============--------]          |
|                                                                   |
|                   SIGNS, NOT LETTERS                              |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   Unlike our alphabet, cuneiform signs can represent:             |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  [Visual comparison diagram]                             |   |
|   |                                                          |   |
|   |  Alphabet:  A = one sound, always "ah"                   |   |
|   |                                                          |   |
|   |  Cuneiform: AN = a word "god" OR a sound "an"            |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   This means the same sign can be read differently               |
|   depending on context - just like how "read" in English         |
|   can be present tense (reed) or past tense (red).               |
|                                                                   |
|                                                                   |
|                        [Button: Continue ->]                      |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

Same pattern as J3-S2.

### Content

Educational content only - no interaction on this screen.

---

## Screen 5: Your First Sign (Interactive)

### Screen ID
`J3-S5-first-sign`

### Entry Points
- Continue from J3-S4

### User Goal
Learn to recognize the AN sign.

### Wireframe

```
+------------------------------------------------------------------+
| [< Back to Curriculum]                                            |
+------------------------------------------------------------------+
|                                                                   |
|                  Lesson 4 of 5    [===============----]           |
|                                                                   |
|                    YOUR FIRST SIGN: AN                            |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|          +------------------+                                     |
|          |                  |                                     |
|          |   [Large AN      |       AN (also read "dingir")       |
|          |    sign image]   |                                     |
|          |                  |       Meaning: god, sky, heaven     |
|          +------------------+                                     |
|                                                                   |
|   This sign appears before the names of gods. When you see        |
|   it, you know a divine name is coming next.                      |
|                                                                   |
|   Memory tip: It looks like a star - and it literally             |
|   means "sky"!                                                    |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   PRACTICE: Tap the AN sign in this tablet section                |
|                                                                   |
|          +--------------------------------------+                 |
|          |                                      |                 |
|          |  [TabletViewer with 3 signs,         |                 |
|          |   one of which is AN, clickable]     |                 |
|          |                                      |                 |
|          |      [?]    [AN]    [?]              |                 |
|          |                                      |                 |
|          +--------------------------------------+                 |
|                                                                   |
|   Hint: It looks like a star with 8 points                        |
|                                                                   |
|                      [Link: Show me ->]                           |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| SignCard | tablet.md | variant="detailed" |
| TabletViewer | tablet.md | variant="compact", regions enabled |
| RegionOverlay | tablet.md | clickable |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Correct region (AN) | Click | Success animation, reveal label |
| Wrong region | Click | "That's [sign name] - try again" |
| "Show me" | Click | Highlight correct region |

### Success Feedback

```
+------------------------------------------------------------------+
|                                                                   |
|   [Check] You found it!                                           |
|                                                                   |
|   That's AN - the sign for "god" or "sky".                        |
|   You'll see this sign very often in cuneiform texts.             |
|                                                                   |
|                        [Button: Continue ->]                      |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Screen 6: Preview Complete

### Screen ID
`J3-S6-complete`

### Entry Points
- Continue from J3-S5

### User Goal
Understand what full curriculum offers and express interest.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|                   [Checkmark animation]                           |
|                                                                   |
|                     Preview Complete!                             |
|                                                                   |
|   You just learned your first cuneiform sign.                     |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   In the full curriculum, you'll learn:                           |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  [Check] 100+ essential cuneiform signs                  |   |
|   |  [Check] Number systems and counting                     |   |
|   |  [Check] Basic Sumerian and Akkadian vocabulary          |   |
|   |  [Check] How to read complete lines of text              |   |
|   |  [Check] Translation techniques with AI assistance       |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   Full curriculum launching Spring 2026                           |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   Get notified when it launches:                                  |
|                                                                   |
|   [EmailInput]                        [Button: Notify me]         |
|                                                                   |
|                                                                   |
|   or continue exploring:                                          |
|                                                                   |
|   [Button: Continue contributing]                                 |
|   [Button: Explore tablet archive]                                |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Stack | layout.md | space="lg" |
| EmailInput | forms.md | - |
| Button | forms.md | variants |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| "Notify me" | Click | Submit email, show J3-S7 |
| Continue contributing | Click | Navigate to J2 |
| Explore archive | Click | Navigate to explore page |

---

## Screen 7: Signup Confirmation

### Screen ID
`J3-S7-confirmation`

### Entry Points
- Email submission from J3-S6

### User Goal
Confirmation of signup.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|   [Checkmark]                                                     |
|                                                                   |
|   You're on the list!                                             |
|                                                                   |
|   We'll notify you at email@example.com when the                  |
|   curriculum launches.                                            |
|                                                                   |
|                                                                   |
|   In the meantime:                                                |
|                                                                   |
|   [Button: Continue contributing]                                 |
|   [Button: Explore tablet archive]                                |
|                                                                   |
+------------------------------------------------------------------+
```

### Email Handling (Release 1)

For the demo/POC:
- Store email in localStorage
- Show confirmation immediately
- No actual email sent

Future implementation will connect to email service.

---

## State Management

### Progress State (localStorage)

```javascript
{
  curriculum: {
    previewCompleted: true,
    lessonsCompleted: [1, 2, 3, 4, 5],
    emailSubmitted: "user@example.com",
    completedAt: timestamp
  }
}
```

### Return Behavior

If user returns after completing preview:
- Show "Continue where you left off" or replay option
- Skip to completion screen if already done

---

## Responsive Behavior

### Mobile (< 768px)

- Full-width content
- Images scale to fit
- Single column throughout
- Touch-friendly interactions

### Tablet/Desktop

- Centered content (max-width: 720px)
- Side-by-side comparisons where appropriate

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial screenflow |
