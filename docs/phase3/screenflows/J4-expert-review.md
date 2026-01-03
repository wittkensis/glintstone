# J4: Expert Review Workflow Preview Screenflow

**Journey:** Expert Review Workflow
**User Type:** Expert (academic/scholar)
**Priority:** P1 (Should Have)
**PRD Reference:** J4-expert-review-preview.md

---

## Journey Overview

```
[Expert Landing] --> [Review Queue Demo] --> [Review Detail Demo] --> [Action Demo]
                                                                           |
                                                                           v
                                                                  [Integration Preview]
                                                                           |
                                                                           v
                                                                  [Interest Form]
```

**Goal:** Demonstrate expert review workflow to convince academics of platform value.

**Release 1 Scope:** Demonstration/preview with dummy data. No actual review submission.

**Success Metrics:**
- Expert understands review workflow: > 80%
- Completes demo walkthrough: > 60%
- Interest in pilot participation: > 30%

---

## Screen 1: Expert Landing

### Screen ID
`J4-S1-landing`

### Entry Points
- Marketing page "For Scholars" or "Access review tools"
- Direct link (/expert)
- Navigation "Review" tab (if authenticated as expert)

### User Goal
Understand what Glintstone offers for expert scholars.

### Wireframe

```
+------------------------------------------------------------------+
| [Header: default]                                                 |
+------------------------------------------------------------------+
|                                                                   |
|                       FOR SCHOLARS                                |
|                                                                   |
|              Accelerate Your Transcription Workflow               |
|                                                                   |
|          Glintstone brings AI-assisted drafts and                 |
|          crowdsourced verification to your desktop.               |
|          You review. You approve. You publish.                    |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|                   HOW IT WORKS FOR EXPERTS                        |
|                                                                   |
|   +---------------------------+  +---------------------------+    |
|   |                           |  |                           |    |
|   | [Icon: AI + Crowd]        |  | [Icon: Checkmark]         |    |
|   |                           |  |                           |    |
|   | 1. AI + CROWD PREPARE     |  | 2. YOU REVIEW             |    |
|   |                           |  |                           |    |
|   | AI proposes initial       |  | Approve, correct, or      |    |
|   | readings. Volunteers      |  | reject. Full control      |    |
|   | verify. You get a         |  | remains with you.         |    |
|   | head start.               |  |                           |    |
|   |                           |  |                           |    |
|   +---------------------------+  +---------------------------+    |
|                                                                   |
|   +---------------------------+  +---------------------------+    |
|   |                           |  |                           |    |
|   | [Icon: Document]          |  | [Icon: CDLI]              |    |
|   |                           |  |                           |    |
|   | 3. YOU PUBLISH            |  | 4. INTEGRATION            |    |
|   |                           |  |                           |    |
|   | ATF export, full          |  | CDLI linking, ORACC-      |    |
|   | attribution, your name    |  | ready formats, familiar   |    |
|   | on it.                    |  | tools.                    |    |
|   |                           |  |                           |    |
|   +---------------------------+  +---------------------------+    |
|                                                                   |
|                                                                   |
|                 [Button: See the Review Interface]                |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Header | navigation.md | default |
| Grid | layout.md | columns="2" |
| Stack | layout.md | space="lg" |
| Button | forms.md | variant="primary", size="lg" |

### Key Messages

| Academic Concern | Message |
|-----------------|---------|
| Loss of control | "You review. You approve." |
| Quality | "Experts verify. That's how it works." |
| Attribution | "Full attribution. Your name on it." |
| Integration | "CDLI linking. ORACC-ready." |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| "See the Review Interface" | Click | Navigate to J4-S2 |

### Accessibility Notes

- Professional, jargon-appropriate language
- Clear value proposition
- No dumbing down

---

## Screen 2: Review Queue Demo

### Screen ID
`J4-S2-queue`

### Entry Points
- "See the Review Interface" from J4-S1

### User Goal
See what the review workflow looks like.

### Wireframe

```
+------------------------------------------------------------------+
| [Demo Mode Banner: "Viewing sample data - this is a demo"]        |
+------------------------------------------------------------------+
| [Header: default]                                                 |
+------------------------------------------------------------------+
|                                                                   |
|   REVIEW QUEUE                                  [Filters v]       |
|                                                                   |
|   8 items awaiting review                                         |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  YBC 4644 - Old Babylonian Letter                        |   |
|   |  P123456 | Sippar                                        |   |
|   |                                                          |   |
|   |  [ConfidenceMeter: 78%]   Contributors: 12               |   |
|   |                                                          |   |
|   |  [StatusBadge: Provisionally Accepted]  [1 expert review]|   |
|   |                                                          |   |
|   |                                       [Button: Review ->]|   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  BM 106056 - Ur III Labor Account                        |   |
|   |  P789012 | Drehem                                        |   |
|   |                                                          |   |
|   |  [ConfidenceMeter: 65%]   Contributors: 8                |   |
|   |                                                          |   |
|   |  [StatusBadge: Under Review]  [Awaiting first expert]    |   |
|   |                                                          |   |
|   |                                       [Button: Review ->]|   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  CBS 10467 - Administrative Receipt                      |   |
|   |  P345678 | Nippur                                        |   |
|   |                                                          |   |
|   |  [ConfidenceMeter: 89%]   Contributors: 15               |   |
|   |                                                          |   |
|   |  [StatusBadge: Under Review]  [High consensus]           |   |
|   |                                                          |   |
|   |                                       [Button: Review ->]|   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   (3 more items below)                                            |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| StatusBadge | trust.md | various statuses |
| ConfidenceMeter | progress.md | variant="standard" |
| Stack | layout.md | space="md" |
| Button | forms.md | variant="secondary" |

### Demo Mode Banner

```html
<div class="demo-banner" role="alert">
  <svg aria-hidden="true"><!-- info icon --></svg>
  <span>Demo Mode - Viewing sample data</span>
</div>
```

Always visible at top of demo screens.

### Queue Item Information

| Field | Description |
|-------|-------------|
| Title | Tablet name + genre |
| P-number | CDLI identifier (linked) |
| Provenience | Origin location |
| Confidence | Aggregate score |
| Contributors | Count |
| Status | Current state |
| Expert reviews | Count of expert actions |

### Filter Options (Demo)

| Filter | Options |
|--------|---------|
| Period | Ur III, OB, NA, NB |
| Language | Sumerian, Akkadian |
| Confidence | High/Medium/Low |
| Status | All statuses |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| "Review" button | Click | Navigate to J4-S3 |
| P-number | Click | (Future: link to CDLI) |
| Filters | Select | Filter queue items |

---

## Screen 3: Review Detail Demo

### Screen ID
`J4-S3-detail`

### Entry Points
- "Review" click from queue

### User Goal
Understand the expert review workflow in detail.

### Wireframe

```
+------------------------------------------------------------------+
| [Demo Mode Banner]                                                |
+------------------------------------------------------------------+
| [< Back to Queue]                                                 |
+------------------------------------------------------------------+
|  YBC 4644 - Old Babylonian Letter                                 |
|  P123456 | Yale Babylonian Collection                             |
+------------------------------------------------------------------+
|                              |                                    |
|  +------------------------+  |  TRANSCRIPTION                     |
|  |                        |  |                                    |
|  |  [TabletViewer]        |  |  @obverse                          |
|  |                        |  |                                    |
|  |  +----------------+    |  |  [TranscriptionLine]               |
|  |  |                |    |  |  1. a-na {d}utu be-li2-ia          |
|  |  |  [Tablet       |    |  |     [StatusBadge: Accepted] [92%]  |
|  |  |   image with   |    |  |                                    |
|  |  |   zoom/pan]    |    |  |  [TranscriptionLine] *selected*    |
|  |  |                |    |  |  2. um-ma {m}a-bi-e-szar2-rum      |
|  |  +----------------+    |  |     [StatusBadge: Under Review][78%]|
|  |                        |  |                                    |
|  |  [Obv] [Rev] [Edge]    |  |  [TranscriptionLine]               |
|  |                        |  |  3. ar-du-ka-a-ma                  |
|  +------------------------+  |     [StatusBadge: Proposed] [65%]  |
|                              |                                    |
|  CONTEXT                     |  @reverse                          |
|  Period: Old Babylonian      |  4. ...                            |
|  Genre: Letter               |  5. ...                            |
|  Language: Akkadian          |                                    |
|                              |                                    |
+------------------------------------------------------------------+
|                                                                   |
|  SELECTED: Line 2                                                 |
|                                                                   |
|  +----------------------------------------------------------+    |
|  |                                                          |    |
|  |  AI Proposal: um-ma {m}a-bi-e-szar2-rum                   |    |
|  |                                                          |    |
|  |  Crowd Consensus: 78% agreement (12 contributors)         |    |
|  |                                                          |    |
|  |  [ProvenanceTimeline - collapsed]                        |    |
|  |  [Show contribution history]                              |    |
|  |                                                          |    |
|  +----------------------------------------------------------+    |
|                                                                   |
|  [Button: Approve] [Button: Correct] [Button: Reject] [Skip]      |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Sidebar | layout.md | width="50%" |
| TabletViewer | tablet.md | default, regions enabled |
| SurfaceTabs | navigation.md | - |
| TranscriptionPanel | tablet.md | editable=false |
| TranscriptionLine | tablet.md | selectable |
| StatusBadge | trust.md | inline |
| ConfidenceMeter | progress.md | inline |
| ProvenanceTimeline | trust.md | collapsed |
| Button | forms.md | multiple variants |

### Line Selection Behavior

1. Click line in transcription panel
2. Corresponding region highlights in tablet viewer
3. Line detail appears below
4. Review actions become available

### Provenance Timeline (Expanded)

```
+----------------------------------------------------------+
|  CONTRIBUTION HISTORY                                     |
+----------------------------------------------------------+
|  [AI] Jan 3, 10:42 AM                                     |
|  Initial proposal: "um-ma {m}a-bi-e-szar-rum"             |
+----------------------------------------------------------+
|  [User] Contributor123 - Jan 3, 11:15 AM                  |
|  Corrected to: "um-ma {m}a-bi-e-szar2-rum"                |
|  Note: Added determinative, corrected szar                |
+----------------------------------------------------------+
|  [User] Contributor456 - Jan 3, 11:30 AM                  |
|  Confirmed reading                                        |
+----------------------------------------------------------+
|  [User] Contributor789 - Jan 3, 11:45 AM                  |
|  Confirmed reading                                        |
+----------------------------------------------------------+
```

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Transcription line | Click | Select line, show detail |
| Tablet region | Click | Select corresponding line |
| Surface tabs | Click | Switch tablet surface |
| Approve | Click | Navigate to J4-S4 (approve demo) |
| Correct | Click | Navigate to J4-S4 (correct demo) |
| Reject | Click | Navigate to J4-S4 (reject demo) |
| Skip | Click | Return to queue |
| Show history | Click | Expand ProvenanceTimeline |

---

## Screen 4: Action Demo

### Screen ID
`J4-S4-action`

### Entry Points
- Action button click from J4-S3

### User Goal
See how review actions work.

### Wireframe (Approve Demo)

```
+------------------------------------------------------------------+
| [Demo Mode Banner]                                                |
+------------------------------------------------------------------+
|                                                                   |
|   APPROVE READING                                                 |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  You are approving:                                      |   |
|   |                                                          |   |
|   |  Line 2: um-ma {m}a-bi-e-szar2-rum                       |   |
|   |                                                          |   |
|   |  This will:                                              |   |
|   |  - Mark the line as [Provisionally Accepted]             |   |
|   |  - Credit 12 contributors                                |   |
|   |  - Record your approval with timestamp                   |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   [Button: Cancel]                    [Button: Confirm Approval]  |
|                                                                   |
+------------------------------------------------------------------+
```

### Wireframe (Correct Demo)

```
+------------------------------------------------------------------+
|                                                                   |
|   CORRECT READING                                                 |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  Original: um-ma {m}a-bi-e-szar2-rum                     |   |
|   |                                                          |   |
|   |  Your correction:                                        |   |
|   |  [TextInput: pre-filled with original]                   |   |
|   |                                                          |   |
|   |  Note (optional):                                        |   |
|   |  [TextArea: explanation of correction]                   |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
|   [Button: Cancel]                  [Button: Submit Correction]   |
|                                                                   |
+------------------------------------------------------------------+
```

### Demo Confirmation

After any action:

```
+------------------------------------------------------------------+
|                                                                   |
|   [Checkmark icon]                                                |
|                                                                   |
|   In the live system, this would:                                 |
|                                                                   |
|   - Update the transcription                                      |
|   - Notify original contributors                                  |
|   - Add your name to attribution                                  |
|   - Record timestamp and provenance                               |
|                                                                   |
|   This is demo mode - no data was changed.                        |
|                                                                   |
|   [Button: Continue reviewing]                                    |
|   [Button: See export options]                                    |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Modal | overlays.md | size="md" |
| TextInput | forms.md | variant="monospace" |
| TextArea | forms.md | - |
| Button | forms.md | - |

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Cancel | Click | Return to J4-S3 |
| Confirm action | Click | Show demo confirmation |
| Continue reviewing | Click | Return to J4-S3 |
| See export options | Click | Navigate to J4-S5 |

---

## Screen 5: Integration Preview

### Screen ID
`J4-S5-integration`

### Entry Points
- "See export options" from action demo
- Navigation from any demo screen

### User Goal
Understand data export and integration capabilities.

### Wireframe

```
+------------------------------------------------------------------+
| [Demo Mode Banner]                                                |
+------------------------------------------------------------------+
|                                                                   |
|   EXPORT OPTIONS                                                  |
|                                                                   |
|   This tablet can be exported to:                                 |
|                                                                   |
|   +----------------------------------------------------------+   |
|   |                                                          |   |
|   |  ATF FORMAT                                              |   |
|   |  Standard transliteration format - ORACC compatible      |   |
|   |                                                          |   |
|   |  Preview:                                                |   |
|   |  +------------------------------------------------------+|   |
|   |  | &P123456 = YBC 4644                                  ||   |
|   |  | #atf: lang akk                                       ||   |
|   |  | @tablet                                              ||   |
|   |  | @obverse                                             ||   |
|   |  | 1. a-na {d}utu be-li2-ia                             ||   |
|   |  | #lem: ana[to]PRP; +Šamaš[1]DN$; bēlu[lord]N$bēlīya   ||   |
|   |  | 2. um-ma {m}a-bi-e-szar2-rum                         ||   |
|   |  | ...                                                  ||   |
|   |  +------------------------------------------------------+|   |
|   |                                                          |   |
|   |  Attribution block:                                      |   |
|   |  # Glintstone Platform                                   |   |
|   |  # Contributors: [anonymized list]                       |   |
|   |  # Reviewer: [your name]                                 |   |
|   |                                                          |   |
|   |  [Button: Copy to clipboard]  [Button: Download .atf]    |   |
|   |                                                          |   |
|   +----------------------------------------------------------+   |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   VIEW IN CDLI                                                    |
|                                                                   |
|   This tablet is cataloged as P123456 in CDLI.                    |
|                                                                   |
|   [Button: Open in CDLI ->]                                       |
|                                                                   |
|   Glintstone syncs with CDLI metadata for:                        |
|   - Museum numbers                                                |
|   - Provenience data                                              |
|   - Physical dimensions                                           |
|   - Bibliography                                                  |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   [Button: Back to review]  [Button: Register for pilot access]   |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Stack | layout.md | space="lg" |
| TextArea | forms.md | readonly, monospace |
| InstitutionBadge | trust.md | CDLI |
| Button | forms.md | multiple variants |

### ATF Preview

Code block with syntax highlighting for ATF format.
- Monospace font (Fira Code)
- Line numbers
- Highlighting for structural elements

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Copy to clipboard | Click | Copy ATF, show toast confirmation |
| Download .atf | Click | Download ATF file |
| Open in CDLI | Click | Open CDLI page (new tab) |
| Back to review | Click | Return to J4-S3 |
| Register for pilot | Click | Navigate to J4-S6 |

---

## Screen 6: Interest Form

### Screen ID
`J4-S6-interest`

### Entry Points
- "Register for pilot access" from various screens
- Explicit CTA at demo end

### User Goal
Express interest in pilot participation.

### Wireframe

```
+------------------------------------------------------------------+
|                                                                   |
|               INTERESTED IN EARLY ACCESS?                         |
|                                                                   |
|   We're looking for expert reviewers to help shape                |
|   Glintstone during our pilot phase.                              |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   [Form]                                                          |
|                                                                   |
|   Name                                                            |
|   [TextInput]                                                     |
|                                                                   |
|   Institution                                                     |
|   [TextInput]                                                     |
|                                                                   |
|   Specialization (e.g., "Ur III administrative texts")            |
|   [TextInput]                                                     |
|                                                                   |
|   Email                                                           |
|   [EmailInput]                                                    |
|                                                                   |
|   How can Glintstone help your research?                          |
|   [TextArea]                                                      |
|                                                                   |
|                            [Button: Submit Interest]              |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|   Or contact us directly: expert@glintstone.io                    |
|                                                                   |
+------------------------------------------------------------------+
```

### Components Used

| Component | Source | Configuration |
|-----------|--------|---------------|
| Stack | layout.md | space="md" |
| TextInput | forms.md | - |
| EmailInput | forms.md | - |
| TextArea | forms.md | rows="4" |
| Button | forms.md | variant="primary" |

### Form Fields

| Field | Required | Validation |
|-------|----------|------------|
| Name | Yes | Non-empty |
| Institution | Yes | Non-empty |
| Specialization | No | - |
| Email | Yes | Email format |
| How can we help | No | - |

### Form Submission (Release 1)

For demo:
- Store in localStorage
- Show confirmation immediately
- No actual backend submission

### Confirmation

```
+------------------------------------------------------------------+
|                                                                   |
|   [Checkmark]                                                     |
|                                                                   |
|   Thank you for your interest!                                    |
|                                                                   |
|   We'll be in touch soon about pilot participation.               |
|                                                                   |
|   In the meantime, explore the demo further:                      |
|                                                                   |
|   [Button: Back to demo]  [Button: Visit marketing page]          |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Demo Mode Behavior

### Always Present

- Demo banner at top of all J4 screens
- Clear indication no real data is affected

### Sample Data Requirements

**Tablets (3-5):**
- Mix of periods (Ur III, OB)
- Mix of genres (administrative, letters)
- Mix of statuses

**Transcription lines:**
- Realistic ATF content
- Various confidence levels
- Plausible provenance data

### Navigation

User can navigate freely between demo screens.
No linear progression required.

---

## Responsive Behavior

### Mobile (< 768px)

**Queue:**
- Cards stack vertically
- Full-width items

**Review Detail:**
- Tablet viewer and transcription stack
- Tab navigation between sections

**Action dialogs:**
- Full-screen modals

### Desktop

- Side-by-side tablet + transcription
- Inline action dialogs

---

## Trust Building Elements

| Element | Purpose |
|---------|---------|
| Demo mode banner | Transparency about sample data |
| Provenance display | Shows nothing is hidden |
| ATF export preview | Familiar format builds trust |
| Attribution in export | Respects scholarly credit |
| CDLI integration | Shows ecosystem awareness |
| Professional UI | Signals serious scholarly tool |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial screenflow |
