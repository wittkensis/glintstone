# J3: Early Learner Curriculum Preview Journey

**Document Type:** Journey PRD
**Priority:** P1 (Should Have)
**Status:** Ready
**Estimated Complexity:** M
**Dependencies:** L1-L4 (All Layer PRDs), J2 (Can upgrade from Passerby)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| User Type | Early Learner (aspirational from Passerby) |
| Journey Scope | Curriculum Landing -> Module Preview -> First Lesson Teaser |
| UX Strategy Reference | Section 6: Educational Guidance UX Approach; Section 1.1: Progressive Disclosure (Level 2) |
| Curriculum Reference | curriculum-research-report.md Section 1.2 (Tier 2) |

---

## Journey Narrative

A motivated Passerby who has completed several sessions wants to go deeper. They click "Learn more" or "Start learning" and discover the structured curriculum that will teach them to actually read cuneiform. For Release 1, this is a **preview experience** - showing what's coming rather than a full curriculum.

The learner sees:
- The learning pathway laid out visually
- A preview of the first module (interactive teaser)
- How learning connects to more meaningful contributions
- An invitation to sign up for early access

This journey validates user interest in the curriculum track and builds anticipation for Release 2.

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Experience | User understands curriculum scope | > 80% clarity |
| Behavior | Preview module interaction rate | > 50% of visitors |
| Behavior | Early access signup rate | > 20% of visitors |
| Outcome | Validates curriculum feature investment | Qualitative feedback |

---

## Journey Map

### Stage 1: Curriculum Landing

**User Goal:** Understand what learning cuneiform involves

**System Response:**
- Visual learning pathway
- Clear time investment expectations
- Engaging "what you'll learn" preview

**Entry Points:**
1. Marketing page "Start learning" CTA
2. Passerby session summary "Learn more" link
3. Navigation "Learn" tab (when authenticated)

**Landing Page Specification:**

```
+--------------------------------------------------+
|  [Logo]  Contribute  Explore  Learn  [Profile]   |
+--------------------------------------------------+
|                                                   |
|   LEARN TO READ CUNEIFORM                         |
|                                                   |
|   Master humanity's oldest writing system.        |
|   From first signs to full translations.          |
|                                                   |
|   +-------------------------------------------+   |
|   |  LEARNING PATHWAY                         |   |
|   |                                           |   |
|   |  [1] FOUNDATIONS          [Unlocked]      |   |
|   |      What is cuneiform?   2-3 hours       |   |
|   |      |                                    |   |
|   |      v                                    |   |
|   |  [2] BASIC SIGNS          [Coming soon]   |   |
|   |      25 essential signs   5-10 hours      |   |
|   |      |                                    |   |
|   |      v                                    |   |
|   |  [3] READING WORDS        [Coming soon]   |   |
|   |      Vocabulary building  5-10 hours      |   |
|   |      |                                    |   |
|   |      v                                    |   |
|   |  [4] READING LINES        [Coming soon]   |   |
|   |      Complete sentences   10-20 hours     |   |
|   |      |                                    |   |
|   |      v                                    |   |
|   |  [5] TRANSLATION          [Coming soon]   |   |
|   |      From text to meaning 10-20 hours     |   |
|   +-------------------------------------------+   |
|                                                   |
|          [Preview Module 1: Foundations]          |
|                                                   |
+--------------------------------------------------+
```

**Learning Pathway Visualization:**

| Module | Title | Duration | Status (R1) |
|--------|-------|----------|-------------|
| 1 | Foundations | 2-3 hours | Preview available |
| 2 | Basic Signs | 5-10 hours | Coming soon |
| 3 | Reading Words | 5-10 hours | Coming soon |
| 4 | Reading Lines | 10-20 hours | Coming soon |
| 5 | Translation | 10-20 hours | Coming soon |

**Total Time Commitment:** 30-60 hours to basic competency

**Acceptance Criteria:**
- [ ] Pathway visualization is clear and vertical
- [ ] Time estimates shown for each module
- [ ] Only Module 1 is interactive (Preview)
- [ ] "Coming soon" states for future modules
- [ ] Total time investment visible
- [ ] Preview CTA is prominent

---

### Stage 2: Module Preview

**User Goal:** Experience a taste of the curriculum

**System Response:**
- Interactive lesson teaser (5 minutes max)
- Shows learning format without full depth
- Ends with "coming soon" for full content

**Module 1: Foundations Preview Content:**

```
+--------------------------------------------------+
|  < Back to Curriculum                             |
+--------------------------------------------------+
|                                                   |
|   MODULE 1: FOUNDATIONS                           |
|                                                   |
|   What is Cuneiform?                              |
|                                                   |
|   Lesson 1 of 5                [=====---------]   |
|                                                   |
+--------------------------------------------------+
|                                                   |
|   [Image: Close-up of cuneiform wedges]           |
|                                                   |
|   Cuneiform is the world's oldest known           |
|   writing system, invented in ancient             |
|   Mesopotamia around 3400 BCE.                    |
|                                                   |
|   The name comes from Latin "cuneus" meaning      |
|   "wedge" - because every mark is made by         |
|   pressing a wedge-shaped reed into soft clay.    |
|                                                   |
|                  [Continue ->]                    |
|                                                   |
+--------------------------------------------------+
```

**Preview Lesson Sequence:**

1. **Introduction** (30 seconds)
   - What is cuneiform
   - Why it matters

2. **The Wedges** (1 minute)
   - Four basic wedge orientations
   - Interactive: identify wedge direction

3. **Signs, Not Letters** (1 minute)
   - Signs can be words or sounds
   - Example: AN sign

4. **Your First Sign** (2 minutes)
   - Learn to recognize AN (dingir)
   - Interactive: find AN in a tablet image

5. **Preview Complete** (30 seconds)
   - What's next in full module
   - Sign up for early access

**Interactive Element Specification:**

**Wedge Direction Task:**
```
+--------------------------------------------------+
|   Which direction does this wedge point?          |
|                                                   |
|   [Large wedge image]                             |
|                                                   |
|   [Left] [Right] [Up] [Down]                      |
+--------------------------------------------------+
```

**Find the Sign Task:**
```
+--------------------------------------------------+
|   Can you spot the AN sign in this tablet?        |
|                                                   |
|   [Tablet image with clickable regions]           |
|                                                   |
|   Hint: It looks like a star with 8 points        |
|                                                   |
|   [Show me ->]                                    |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] 5-minute preview experience
- [ ] At least 2 interactive elements
- [ ] Progress indicator shows 1 of 5 lessons
- [ ] Content is engaging and accurate
- [ ] Clear transition to "coming soon" state
- [ ] No account required for preview

---

### Stage 3: First Sign Learning

**User Goal:** Learn to recognize their first cuneiform sign

**System Response:**
- Focus on AN (dingir) - meaning "god" or "sky"
- Visual memorization aids
- Interactive practice

**AN Sign Introduction:**

```
+--------------------------------------------------+
|   YOUR FIRST SIGN: AN                             |
|                                                   |
|   +------------------+                            |
|   |                  |                            |
|   |   [Large AN      |  AN (also read "dingir")  |
|   |    sign image]   |                            |
|   |                  |  Meaning: god, sky, heaven |
|   +------------------+                            |
|                                                   |
|   This sign appears before the names of gods.     |
|   When you see it, you know a divine name         |
|   is coming next.                                 |
|                                                   |
|   Memory tip: It looks like a star - and it       |
|   literally means "sky"!                          |
|                                                   |
|                  [Practice ->]                    |
|                                                   |
+--------------------------------------------------+
```

**Practice Task:**

```
+--------------------------------------------------+
|   PRACTICE: Find the AN sign                      |
|                                                   |
|   [Tablet section with 3 signs, one is AN]        |
|                                                   |
|   Tap the sign that means "god" or "sky"          |
|                                                   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] AN sign clearly displayed with meaning
- [ ] Mnemonic provided (star = sky)
- [ ] Interactive find-the-sign practice
- [ ] Success feedback on correct identification
- [ ] Links sign learning to contribution value

---

### Stage 4: Preview Complete

**User Goal:** Understand what full curriculum offers

**System Response:**
- Summary of preview experience
- What full curriculum includes
- Early access signup

**Preview Complete Screen:**

```
+--------------------------------------------------+
|                                                   |
|   [Checkmark animation]                           |
|                                                   |
|   Preview Complete!                               |
|                                                   |
|   You just learned your first cuneiform sign.     |
|   In the full curriculum, you'll learn:           |
|                                                   |
|   - 100+ essential signs                          |
|   - Number systems and counting                   |
|   - Basic Sumerian and Akkadian vocabulary        |
|   - How to read complete lines of text            |
|   - Translation techniques                        |
|                                                   |
|   Full curriculum coming in Spring 2026           |
|                                                   |
+--------------------------------------------------+
|                                                   |
|   Get notified when it launches:                  |
|                                                   |
|   [Email address     ] [Notify me]                |
|                                                   |
|   or                                              |
|                                                   |
|   [Continue contributing as Passerby]             |
|   [Explore tablet archive]                        |
|                                                   |
+--------------------------------------------------+
```

**What Full Curriculum Includes (messaging):**
- 100+ essential cuneiform signs
- Number systems and counting
- Basic Sumerian and Akkadian vocabulary
- How to read complete lines of text
- Translation techniques with AI assistance

**Acceptance Criteria:**
- [ ] Clear summary of preview accomplishment
- [ ] Full curriculum scope outlined
- [ ] Coming soon date indicated
- [ ] Email signup for notifications
- [ ] Alternative paths (Passerby, Explore) available
- [ ] Signup is optional, not blocking

---

### Stage 5: Email Signup (Optional)

**User Goal:** Get notified when curriculum launches

**System Response:**
- Simple email capture
- Confirmation of signup
- Continue to other experiences

**Email Signup Specification:**

```
+--------------------------------------------------+
|   Get Early Access                                |
|                                                   |
|   [email@example.com     ] [Notify me]            |
|                                                   |
|   We'll email you when the full curriculum        |
|   launches. No spam, promise.                     |
+--------------------------------------------------+
```

**Confirmation:**

```
+--------------------------------------------------+
|   [Checkmark] You're on the list!                 |
|                                                   |
|   We'll notify you at email@example.com           |
|   when the curriculum launches.                   |
|                                                   |
|   [Continue to contribute]                        |
+--------------------------------------------------+
```

**For Release 1:** Email submission can go to a simple form or be stored in localStorage (demo mode). No backend required.

**Acceptance Criteria:**
- [ ] Email field validates format
- [ ] Confirmation displayed on submit
- [ ] No blocking if skipped
- [ ] Privacy-respecting messaging

---

## Component Dependencies

| Component | Source PRD | Usage in J3 |
|-----------|------------|-------------|
| Design Tokens | L1 | All styling |
| TabletViewer | L3 | Sign identification practice |
| SignCard | L3 | Sign learning display |
| ProgressBar | L4 | Lesson progress |
| Dummy Signs | L2 | AN sign data and images |

---

## Content Requirements

**Module 1 Preview Content (5 lessons, only 1-2 for R1):**

| Lesson | Title | Content Type | Interactive |
|--------|-------|--------------|-------------|
| 1 | What is Cuneiform? | Text + image | No |
| 2 | The Wedges | Text + image | Wedge direction quiz |
| 3 | Signs, Not Letters | Text + image | No |
| 4 | Your First Sign | Text + image | Find the sign |
| 5 | Preview Complete | Summary | Email signup |

**AN Sign Content:**
- High-quality sign image
- Pronunciation: "an" or "dingir"
- Meaning: god, sky, heaven
- Usage: Determinative before divine names
- Mnemonic: "Looks like a star = sky"
- Fun fact: This is the most common sign in cuneiform

---

## Visual Design Notes

**Curriculum Pathway:**
- Vertical stepped layout (not horizontal timeline)
- Each module is a card with status indicator
- Connected by vertical line/dots
- Active modules glow, locked modules are muted

**Lesson Content:**
- Clean, readable layout
- Large images with good contrast
- Progress indicator at top
- Generous whitespace
- Mobile-friendly text size

**Interactive Elements:**
- Clear touch targets
- Immediate feedback on interaction
- Success state celebrations
- No penalty for incorrect attempts

---

## Edge Cases and Error States

| Scenario | Expected Behavior |
|----------|-------------------|
| Preview already completed | Show "Continue where you left off" |
| Email already submitted | Show "You're already on the list" |
| Offline during preview | Graceful degradation, cached content |
| Very wide screen | Content max-width 800px for readability |

---

## Out of Scope

- Full curriculum content (Modules 2-5)
- Spaced repetition system
- Quiz/test functionality beyond simple interaction
- Progress tracking across sessions (beyond localStorage)
- Certificate or badge system
- Sign learning flashcard system

---

## Future Integration Notes

This preview experience is designed to:
1. Validate interest in curriculum features
2. Collect email addresses for launch notification
3. Establish UI patterns for full curriculum (Release 2+)

**Release 2 Expansion:**
- Full Module 1 content (5 lessons, 2-3 hours)
- Sign learning with spaced repetition
- Progress tracking with account
- Integration with contribution system (unlock tasks)
- Achievement badges for curriculum milestones

---

## Testing Requirements

**Functional:**
- [ ] Preview flow completes without errors
- [ ] Interactive elements work correctly
- [ ] Email submission works (or logs for demo)
- [ ] Navigation back to curriculum works

**Content:**
- [ ] All text is accurate (academic advisor review)
- [ ] Images load correctly
- [ ] AN sign information is correct

**Accessibility:**
- [ ] Screen reader compatible
- [ ] Keyboard navigable
- [ ] Sufficient contrast

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
