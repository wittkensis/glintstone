# Glintstone Release 1 - Implementation Quick Reference

**Tech Stack:** Vite + React 18 + TypeScript + Shadcn/UI + Tailwind CSS
**Deployment:** Vercel
**Scope:** J1 (Marketing) + J2 (Passerby Contribution) only

---

## Design Tokens (L1)

### Colors
- **Background:** `#0a0e14` (Celestial Navy)
- **Surface:** `#151a23`
- **Border:** `#2d3748`
- **Text:** `#e2e8f0`
- **Accent:** `#f6ad55` (Warm Gold)
- **AI Indicator:** `#9f7aea` (Violet)

### Typography
- **Headers:** Serif (Eczar/Spectral)
- **Body:** Sans-serif (Inter/System)
- **Code:** Monospace

### Spacing Scale
- XS: 0.5rem, S: 1rem, M: 1.5rem, L: 2rem, XL: 3rem

---

## Data Schema (L2)

### Tablet
```typescript
{
  id: string
  cdli_id: string
  museum_number: string
  period: string
  genre: string
  images: { obverse: string, reverse: string }
  transcription_status: "untranscribed" | "in_progress" | "verified"
}
```

### Expert
```typescript
{
  id: string
  firstName: string
  lastName: string
  title: string
  affiliation: string
  avatarUrl: string
  specialization: string
  credibilityScore: number
}
```

### Institution
```typescript
{
  id: string
  name: string
  type: "university" | "museum" | "platform"
  logoUrl: string
  partnered: boolean
}
```

### Task (for J2)
```typescript
{
  id: string
  type: "sign_match"
  tabletId: string
  signImage: string
  options: Array<{ id: string, label: string, image: string }>
  correctAnswer: string
}
```

---

## Components Needed (L3 + L4)

### Critical for J1 + J2
1. **Layout:** Container, Stack, Grid
2. **Tablet:** TabletViewer (basic), SignCard
3. **Task:** TaskCard, SignMatchTask
4. **Progress:** ProgressBar, ConfidenceMeter, SessionSummary
5. **Trust:** ExpertCard, InstitutionBadge, StatusBadge
6. **Navigation:** Header, Button
7. **Forms:** Button (primary/secondary)
8. **Overlays:** Modal (for tutorial)

### Skip (Not Critical Path)
- Complex tablet interactions (zoom/pan)
- Advanced progress animations
- Full navigation system
- All form inputs except Button
- Tooltips, popovers, context panels

---

## J1: Marketing Page (6 Screens)

### Screen 1: Hero
- Large tablet image background
- H1: "Unlock Ancient Mesopotamia"
- CTA: "Start Contributing" → J2
- Live contribution counter (dummy animation)

### Screen 2: Social Proof
- Stats: "50,000 contributions", "1,200 tablets transcribed"
- Partner logos (Yale, British Museum, CDLI)

### Screen 3: How You Can Help
- 3 paths: Passerby, Early Learner, Expert
- Focus on Passerby (links to J2)

### Screen 4: How It Works (4 steps)
1. View ancient tablet
2. Identify cuneiform signs
3. AI validates your work
4. Experts review and publish

### Screen 5: For Scholars
- Integration badges (CDLI, ORACC)
- Expert testimonials (use dummy expert data)

### Screen 6: Final CTA
- "Ready to contribute?" → J2
- Footer with links

---

## J2: Passerby Contribution (7 Screens)

### Screen 1: Welcome
- "You'll help transcribe tablet [ID]"
- "Takes ~3 minutes"
- "Start" button
- Auto-advance after 2s

### Screen 2: Mini Tutorial
- Animated example of sign matching
- "Got it" button
- Skippable

### Screen 3-5: Task Loop (Main)
**TaskCard Component:**
- Tablet context (small thumbnail)
- Isolated sign image (large)
- 4 sign options (2x2 grid)
- "Skip" button
- Progress: "3 of 10"
- Timer (optional, can skip)

**After each:**
- Success feedback: "✓ Great work!"
- Or: Fun fact about cuneiform (every 3rd)

### Screen 6: Session Summary
- "You completed 10 tasks!"
- "You helped with tablet [CDLI ID]"
- Stats: signs identified, accuracy estimate (dummy %)
- CTA: "Do more" OR "Learn cuneiform"

### Screen 7: Error Handling
- If all tasks exhausted: "Check back soon!"
- If image fails: Auto-skip

---

## State Management (Zustand)

### Stores Needed
```typescript
// taskStore.ts
{
  currentTask: Task | null
  taskQueue: Task[]
  completedTasks: number
  sessionStart: Date
  loadNextTask: () => void
  completeTask: (answer: string) => void
}

// sessionStore.ts
{
  contributionCount: number
  tabletId: string
  startSession: (tabletId: string) => void
  endSession: () => SessionStats
}
```

---

## Routing (TanStack Router)

```
/ → J1 Marketing Page
/contribute → J2 Welcome
/contribute/task → J2 Task Loop
/contribute/summary → J2 Session Summary
```

---

## Dummy Data Files Needed

1. `/public/data/experts.json` ✅ (already exists)
2. `/public/data/institutions.json` ✅ (already exists)
3. `/public/data/tablets.json` (5-10 tablets)
4. `/public/data/tasks.json` (30-50 tasks)
5. `/public/images/tablets/` (5-10 tablet images - placeholder or CC0)
6. `/public/images/signs/` (20-30 sign images - can use simple SVG shapes)

---

## Acceptance Criteria (MVP)

### J1 Marketing
- [x] Hero loads in <2s
- [x] All 6 sections visible
- [x] CTA buttons navigate to J2
- [x] Partner logos display
- [x] Responsive (desktop + mobile)

### J2 Passerby
- [x] Welcome → Task Loop → Summary flow works
- [x] 10 tasks completable
- [x] Sign options clickable
- [x] Progress bar updates
- [x] Session summary shows correct stats
- [x] "Do more" resets to new session

---

## Sprint Breakdown

### Sprint 1: Foundation (Haiku)
- Vite project init
- Shadcn/UI + Tailwind setup
- Design tokens config
- Create tablets.json, tasks.json
- Placeholder images

### Sprint 2: Components (Sonnet)
- Layout components (Container, Stack, Grid)
- SignCard, TaskCard
- ProgressBar, SessionSummary
- ExpertCard, InstitutionBadge
- Header, Button

### Sprint 3: Journeys (Sonnet)
- J1: Marketing page (all 6 screens)
- J2: Full contribution flow
- Task store + session store
- Router setup

### Sprint 4: Polish (Mixed)
- Apply brand colors/textures
- Responsive layout
- Animation polish
- Vercel deployment
- Bug fixes

---

## What to Skip (Token Optimization)

❌ J3, J4, J5 journeys
❌ Complex tablet viewer (zoom, pan, overlays)
❌ Account system / auth
❌ Backend API (use localStorage)
❌ Advanced animations
❌ Multiple task types (only sign_match)
❌ Tutorial skip logic (just show it)
❌ Accessibility beyond basics
❌ Error boundaries
❌ Loading states (can add if time)
❌ Tablet image overlays/regions

---

## Priority Order (If Tokens Run Low)

**P0 (Must Have):**
- J1 Hero + CTA
- J2 Task Loop (3 screens minimum)
- Basic styling (colors only)
- Vercel deploy

**P1 (Should Have):**
- J1 Full 6 screens
- J2 Full 7 screens
- Session summary
- Brand textures

**P2 (Nice to Have):**
- Animations
- Responsive design
- Polish

---

## File Reference

- **Architecture:** `/docs/phase3/component-architecture-proposal.md`
- **Components:** `/docs/phase3/components/*.html`
- **Screenflows:** `/docs/phase3/screenflows/*.html`
- **Expert Data:** `/public/data/experts.json`
- **Institution Data:** `/public/data/institutions.json`
