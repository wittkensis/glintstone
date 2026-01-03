# J4: Expert Review Workflow Preview Journey

**Document Type:** Journey PRD
**Priority:** P1 (Should Have)
**Status:** Ready
**Estimated Complexity:** M
**Dependencies:** L1-L4 (All Layer PRDs)
**Assigned Agent:** eng-frontend

---

## Meta

| Attribute | Value |
|-----------|-------|
| User Type | Expert (preview for academic audience) |
| Journey Scope | Expert Landing -> Review Queue Demo -> Workflow Preview |
| UX Strategy Reference | Section 2.3: Critical Path W-X1 (Expert Review Queue); Section 1.2: Contextual Authority Model |
| Academic Reference | academic-workflow-report.md Section 2.2 (Review Pipeline Design) |

---

## Journey Narrative

A scholar visits Glintstone, curious whether this platform could actually accelerate their work. They've seen the marketing page and are skeptical but intrigued. They click through to see the expert review interface - the tool they would actually use if they adopted the platform.

For Release 1, this is a **demonstration experience** - showing a functional UI with dummy data that illustrates how expert review would work. The goal is to convince academics that:

1. Their expertise is respected (they have final authority)
2. The workflow is efficient (not more work than current methods)
3. The system is trustworthy (transparent provenance, clear status)
4. Integration with existing tools is real (CDLI, ATF export)

---

## Success Metrics

| Type | Metric | Target |
|------|--------|--------|
| Experience | Expert understands review workflow | > 80% clarity |
| Experience | Expert perceives efficiency benefit | Qualitative positive |
| Behavior | Completes demo review walkthrough | > 60% of visitors |
| Trust | Perceives scholarly rigor | Qualitative positive |
| Outcome | Interest in pilot participation | > 30% express interest |

---

## Journey Map

### Stage 1: Expert Landing

**User Goal:** Understand what Glintstone offers for experts

**System Response:**
- Credibility-focused messaging
- Efficiency value proposition
- Integration highlights

**Entry Points:**
1. Marketing page "For Scholars" link
2. Marketing page "Access review tools" CTA
3. Direct link shared in academic channels

**Expert Landing Page Specification:**

```
+--------------------------------------------------+
|  [Logo]  Contribute  Explore  Learn  [Profile]   |
+--------------------------------------------------+
|                                                   |
|   FOR SCHOLARS                                    |
|                                                   |
|   Accelerate Your Transcription Workflow          |
|                                                   |
|   Glintstone brings AI-assisted drafts and        |
|   crowdsourced verification to your desktop.      |
|   You review. You approve. You publish.           |
|                                                   |
+--------------------------------------------------+
|                                                   |
|   HOW IT WORKS FOR EXPERTS                        |
|                                                   |
|   +------------------+  +------------------+      |
|   | 1. AI + CROWD    |  | 2. YOU REVIEW    |      |
|   |    PREPARE       |  |                  |      |
|   |                  |  | Approve, correct,|      |
|   | AI proposes,     |  | or reject. Full  |      |
|   | volunteers       |  | control remains  |      |
|   | verify. You get  |  | with you.        |      |
|   | a head start.    |  |                  |      |
|   +------------------+  +------------------+      |
|                                                   |
|   +------------------+  +------------------+      |
|   | 3. YOU PUBLISH   |  | 4. INTEGRATION   |      |
|   |                  |  |                  |      |
|   | ATF export,      |  | CDLI linking,    |      |
|   | full attribution,|  | ORACC-ready      |      |
|   | your name on it. |  | formats.         |      |
|   +------------------+  +------------------+      |
|                                                   |
|            [See the Review Interface]             |
|                                                   |
+--------------------------------------------------+
```

**Key Messages for Academics:**

| Concern | Message |
|---------|---------|
| Loss of control | "You review. You approve. Nothing publishes without your sign-off." |
| Quality | "AI and crowds prepare drafts. Experts verify. That's how it works." |
| Attribution | "Full attribution in ATF-compliant exports. Your name on your work." |
| Integration | "CDLI P-number linking. ORACC-compatible export. Familiar formats." |
| Time | "Spend your time on the hard problems. Let us handle the obvious ones." |

**Acceptance Criteria:**
- [ ] Expert-focused messaging above fold
- [ ] Four-step workflow clearly visualized
- [ ] Integration partners mentioned (CDLI, ORACC)
- [ ] CTA to see review interface
- [ ] No dumbing down of language (use appropriate terminology)

---

### Stage 2: Review Queue Demo

**User Goal:** See what the review workflow looks like

**System Response:**
- Functional review queue UI with dummy data
- Interactive demo (can click through)
- Clear "demo mode" indicator

**Review Queue Interface:**

```
+--------------------------------------------------+
|  [Demo Mode - Viewing sample data]               |
+--------------------------------------------------+
|                                                   |
|   REVIEW QUEUE                     [Filters v]   |
|                                                   |
|   8 items awaiting review                         |
|                                                   |
+--------------------------------------------------+
|   +----------------------------------------------+|
|   | YBC 4644 - Old Babylonian Letter             ||
|   | P123456 | Sippar                              ||
|   | Confidence: 78% | Contributors: 12            ||
|   | [Provisionally Accepted] [1 expert review]    ||
|   |                              [Review ->]      ||
|   +----------------------------------------------+|
|                                                   |
|   +----------------------------------------------+|
|   | BM 106056 - Ur III Labor Account             ||
|   | P789012 | Drehem                              ||
|   | Confidence: 65% | Contributors: 8             ||
|   | [Under Review] [Awaiting first expert]        ||
|   |                              [Review ->]      ||
|   +----------------------------------------------+|
|                                                   |
|   +----------------------------------------------+|
|   | CBS 10467 - Administrative Receipt           ||
|   | P345678 | Nippur                              ||
|   | Confidence: 89% | Contributors: 15            ||
|   | [Under Review] [High consensus]               ||
|   |                              [Review ->]      ||
|   +----------------------------------------------+|
|                                                   |
+--------------------------------------------------+
```

**Queue Item Information:**
- Tablet name and museum number
- CDLI P-number (linked)
- Provenience
- Aggregate confidence score
- Contributor count
- Current status (with badge)
- Quick action to review

**Filter Options (demo):**
- By period (Ur III, OB, NA, NB)
- By language (Sumerian, Akkadian)
- By confidence level
- By status

**Acceptance Criteria:**
- [ ] Queue displays 5-8 sample items
- [ ] Each item shows key metadata
- [ ] Status badges use correct styling (L1)
- [ ] Confidence scores displayed
- [ ] P-numbers visible and formatted correctly
- [ ] "Demo mode" banner clearly visible
- [ ] Clicking "Review" opens detail view

---

### Stage 3: Review Detail Demo

**User Goal:** Understand the expert review workflow

**System Response:**
- Full review interface with sample tablet
- Side-by-side tablet image and transcription
- Approve/correct/reject controls
- Contribution provenance visible

**Review Detail Interface:**

```
+--------------------------------------------------+
|  < Back to Queue            [Demo Mode]           |
+--------------------------------------------------+
|  YBC 4644 - Old Babylonian Letter                 |
|  P123456 | Yale Babylonian Collection             |
+--------------------------------------------------+
|                          |                        |
|  +-------------------+   |  TRANSCRIPTION         |
|  |                   |   |                        |
|  |  [Tablet image    |   |  @obverse              |
|  |   with zoom/pan]  |   |  1. a-na {d}utu be-li2-|
|  |                   |   |     ia                 |
|  |  [Obv] [Rev]      |   |     [Accepted] [92%]   |
|  +-------------------+   |                        |
|                          |  2. um-ma {m}a-bi-e-   |
|  CONTEXT                 |     szar2-rum          |
|  Period: Old Babylonian  |     [Under Review][78%]|
|  Genre: Letter           |                        |
|  Language: Akkadian      |  3. ar-du-ka-a-ma      |
|                          |     [Proposed] [65%]   |
|                          |                        |
+--------------------------------------------------+
|                                                   |
|  SELECTED: Line 2                                 |
|                                                   |
|  AI Proposal: um-ma {m}a-bi-e-szar2-rum           |
|  Crowd Consensus: 78% agreement (12 contributors) |
|                                                   |
|  Contribution History:                            |
|  - AI initial: "um-ma {m}a-bi-e-szar-rum"         |
|  - Contributor A: Corrected szar2                 |
|  - Contributor B: Confirmed                       |
|  - Contributor C: Confirmed                       |
|                                                   |
|  [Approve] [Correct] [Reject] [Skip for now]      |
|                                                   |
+--------------------------------------------------+
```

**Review Controls:**

| Action | Description | Result |
|--------|-------------|--------|
| Approve | Accept current reading | Status -> Accepted |
| Correct | Edit and approve | Opens inline editor |
| Reject | Mark as incorrect | Requires note |
| Skip | Come back later | Returns to queue |
| Dispute | Disagree with another expert | Opens dispute flow |

**Provenance Display:**
- AI initial proposal (with model version)
- Each contributor action
- Timestamps
- Agreement/disagreement patterns

**Acceptance Criteria:**
- [ ] Side-by-side image and transcription layout
- [ ] TabletViewer with zoom/pan functional
- [ ] Lines are individually selectable
- [ ] Selected line shows full provenance
- [ ] Status badges on each line
- [ ] Confidence meter per line
- [ ] All review actions visible as buttons
- [ ] Clicking action shows confirmation (demo mode)

---

### Stage 4: Action Demo

**User Goal:** See how review actions work

**System Response:**
- Interactive demonstration of each action
- Confirmation dialogs
- Status change preview

**Approve Action Demo:**

```
+--------------------------------------------------+
|   APPROVE READING                                 |
|                                                   |
|   You are approving:                              |
|   Line 2: um-ma {m}a-bi-e-szar2-rum               |
|                                                   |
|   This will:                                      |
|   - Mark the line as [Provisionally Accepted]     |
|   - Credit 12 contributors                        |
|   - Record your approval with timestamp           |
|                                                   |
|   [Cancel]                    [Confirm Approval]  |
+--------------------------------------------------+
```

**Correct Action Demo:**

```
+--------------------------------------------------+
|   CORRECT READING                                 |
|                                                   |
|   Original: um-ma {m}a-bi-e-szar2-rum             |
|                                                   |
|   Your correction:                                |
|   [um-ma {m}a-bi-e-szar2-rum                    ] |
|                                                   |
|   Note (optional):                                |
|   [Corrected szar to szar2 per collation        ]|
|                                                   |
|   [Cancel]                 [Submit Correction]    |
+--------------------------------------------------+
```

**Demo Confirmation:**

```
+--------------------------------------------------+
|   [Checkmark]                                     |
|                                                   |
|   In the live system, this would:                 |
|   - Update the transcription                      |
|   - Notify original contributors                  |
|   - Add your name to attribution                  |
|                                                   |
|   This is demo mode - no data was changed.        |
|                                                   |
|   [Continue reviewing]                            |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] Approve shows confirmation dialog
- [ ] Correct opens inline editor
- [ ] Demo clearly states no actual changes made
- [ ] What would happen is clearly explained
- [ ] Workflows feel responsive and professional

---

### Stage 5: Integration Preview

**User Goal:** Understand data export and integration

**System Response:**
- ATF export preview
- CDLI linking demonstration
- Integration messaging

**Export Preview:**

```
+--------------------------------------------------+
|   EXPORT OPTIONS                                  |
|                                                   |
|   This tablet can be exported to:                 |
|                                                   |
|   [ATF Format] - Standard transliteration format  |
|                  Compatible with ORACC            |
|                                                   |
|   Preview:                                        |
|   +--------------------------------------------+  |
|   | &P123456 = YBC 4644                        |  |
|   | #atf: lang akk                             |  |
|   | @tablet                                    |  |
|   | @obverse                                   |  |
|   | 1. a-na {d}utu be-li2-ia                   |  |
|   | #lem: ana[to]PRP; +Šamaš[1]DN$;           |  |
|   |       bēlu[lord]N$bēlīya                   |  |
|   | 2. um-ma {m}a-bi-e-szar2-rum               |  |
|   | ...                                        |  |
|   +--------------------------------------------+  |
|                                                   |
|   Attribution included:                           |
|   # Glintstone Platform                           |
|   # Contributors: [list]                          |
|   # Reviewer: [your name]                         |
|                                                   |
|   [Copy to clipboard] [Download .atf]             |
|                                                   |
+--------------------------------------------------+
```

**CDLI Link Preview:**

```
+--------------------------------------------------+
|   VIEW IN CDLI                                    |
|                                                   |
|   This tablet is cataloged as P123456 in CDLI.    |
|                                                   |
|   [Open in CDLI ->]                               |
|                                                   |
|   Glintstone syncs with CDLI metadata for:        |
|   - Museum numbers                                |
|   - Provenience data                              |
|   - Physical dimensions                           |
|   - Bibliography                                  |
|                                                   |
+--------------------------------------------------+
```

**Acceptance Criteria:**
- [ ] ATF export shown with syntax highlighting
- [ ] Attribution block visible in export
- [ ] Copy/download buttons present (functional in demo)
- [ ] CDLI link opens in new tab (to real CDLI if P-number exists)
- [ ] Integration messaging builds trust

---

### Stage 6: Call to Action

**User Goal:** Express interest or provide feedback

**System Response:**
- Pilot participation invitation
- Feedback form
- Contact information

**Interest Form:**

```
+--------------------------------------------------+
|                                                   |
|   INTERESTED IN EARLY ACCESS?                     |
|                                                   |
|   We're looking for expert reviewers to           |
|   help shape Glintstone during our pilot.         |
|                                                   |
|   Name: [                                  ]      |
|   Institution: [                           ]      |
|   Specialization: [                        ]      |
|   Email: [                                 ]      |
|                                                   |
|   How can Glintstone help your research?          |
|   [                                             ] |
|   [                                             ] |
|                                                   |
|   [Submit Interest]                               |
|                                                   |
+--------------------------------------------------+
```

**For Release 1:** Form submission can go to email or be logged. No backend required.

**Acceptance Criteria:**
- [ ] Interest form captures key information
- [ ] Form validates email format
- [ ] Submission shows confirmation
- [ ] Alternative contact method available
- [ ] No pressure or obligation messaging

---

## Component Dependencies

| Component | Source PRD | Usage in J4 |
|-----------|------------|-------------|
| Design Tokens | L1 | All styling |
| TabletViewer | L3 | Review detail image |
| TranscriptionLine | L3 | Line-by-line transcription |
| StatusBadge | L3 | Status indicators |
| ConfidenceMeter | L3 | Confidence display |
| ContextPanel | L3 | Tablet metadata |
| Dummy Tablets | L2 | Sample review data |
| Dummy Contributions | L2 | Provenance data |

---

## Data Requirements

**Sample Tablets for Demo (3-5 tablets):**

| Tablet | Status Mix | Purpose |
|--------|------------|---------|
| YBC 4644 | Mixed (some Accepted, some Under Review) | Show partial completion |
| BM 106056 | All Under Review | Show fresh queue item |
| CBS 10467 | High consensus | Show easy approval case |
| P789012 | Low confidence | Show difficult case |
| VAT 17480 | Disputed | Show expert disagreement |

**Provenance Data:**
- Each line needs 3-5 contributor actions
- AI initial proposal always present
- Mix of confirmations and corrections

---

## Academic Terminology Usage

This journey should use appropriate academic terminology:
- "Transcription" not "reading"
- "Transliteration" for ATF content
- "Collation" for physical verification
- "P-number" for CDLI identifiers
- "Lemmatization" for word parsing

---

## Out of Scope

- Real expert authentication
- Actual review submission
- Dispute resolution workflow
- Bulk review actions
- Email notifications
- Expert-to-expert messaging
- Publication pipeline

---

## Trust Building Elements

| Element | Purpose |
|---------|---------|
| Demo mode banner | Transparency about sample data |
| Provenance display | Shows nothing is hidden |
| ATF export | Familiar format builds trust |
| Attribution promise | Respects scholarly credit norms |
| CDLI integration | Shows ecosystem awareness |
| Professional UI | Signals serious scholarly tool |

---

## Testing Requirements

**Functional:**
- [ ] Demo flow completes without errors
- [ ] All demo actions show appropriate feedback
- [ ] TabletViewer works in review context
- [ ] ATF export renders correctly

**Content:**
- [ ] Sample transcriptions are plausible
- [ ] ATF format is valid
- [ ] Terminology is accurate

**User Experience:**
- [ ] Workflow is clear to academic user
- [ ] Trust-building elements are present
- [ ] Demo mode is clearly indicated throughout

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Manager Agent | Initial PRD |
