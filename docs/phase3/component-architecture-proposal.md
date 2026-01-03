# Glintstone Component Architecture Proposal

**Document Type:** Phase 3 Technical Architecture
**Author:** Engineering Architect Agent
**Date:** January 3, 2026
**Version:** 1.0
**Status:** Draft for Review

---

[@Claude @ux-architect the recommended Approach works, I want to caution against too much complexity in the beginning through. Before getting started, find a way to incorporate these best practices from YCombinator as rules for development: https://x.com/uttam_singhk/status/2007366453864120366?s=20]

## Executive Summary

This document proposes three distinct architectural approaches for implementing Glintstone Release 1 (POC) that can scale to Release 4 (1.0). Each approach is evaluated against key criteria: scalability, development velocity, maintainability, and alignment with the "vibe-coding" rapid prototyping methodology.

**Key Architectural Decisions:**
1. **Framework Selection**: Modern frontend framework with strong TypeScript support
2. **Component Strategy**: Atomic design principles with progressive complexity layers
3. **Data Architecture**: Schema-first design supporting dummy data (R1) → live integrations (R4)
4. **Asset Management**: Local hosting for POC, CDN-ready structure for production
5. **State Management**: Tier-appropriate complexity from simple to sophisticated

**Recommendation**: Approach 2 - "Vite + React + TypeScript Stack" provides optimal balance of developer experience, ecosystem maturity, and deployment flexibility for this project's trajectory.

---

## Table of Contents

1. [Architectural Approaches](#1-architectural-approaches)
2. [Component Library Structure](#2-component-library-structure)
3. [Data Model Design](#3-data-model-design)
4. [Image and Asset Strategy](#4-image-and-asset-strategy)
5. [Technology Stack Comparison](#5-technology-stack-comparison)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Appendices](#7-appendices)

---

## 1. Architectural Approaches

### Approach 1: "Static Site Generator + Hydration"

**Core Philosophy**: Build Release 1 as a static site with minimal JavaScript, progressively enhance with interactivity where needed.

#### Technology Stack
```
├── Framework: Astro 4.x
├── UI Components: React islands (for interactive elements only)
├── Styling: Tailwind CSS + CSS Custom Properties
├── Build Tool: Astro's built-in Vite integration
├── Deployment: Cloudflare Pages / Netlify / Vercel
├── Type Safety: TypeScript (strict mode)
└── Data: JSON files + content collections
```

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                    STATIC PAGES                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Marketing   │  │   Explore    │  │    Learn     │ │
│  │   (Static)   │  │ (Static+JS)  │  │ (Static+JS)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              INTERACTIVE ISLANDS (React)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Task Card   │  │ Tablet Viewer│  │Progress Track│ │
│  │  (Hydrated)  │  │  (Hydrated)  │  │  (Hydrated)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   SHARED UTILITIES                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Data Schemas │  │  Formatters  │  │  Constants   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    STATIC DATA                          │
│  tablets.json │ experts.json │ institutions.json        │
└─────────────────────────────────────────────────────────┘
```

#### Strengths
- **Performance**: Lightning-fast initial load (static HTML)
- **SEO**: Perfect for marketing page and public tablet archive
- **Simplicity**: Minimal runtime JavaScript = fewer bugs
- **Cost**: Static hosting is essentially free at scale
- **Scalability**: Can add API routes later without architectural change

#### Weaknesses
- **Interactivity Complexity**: Island architecture adds mental overhead
- **Session State**: Client-side only, needs localStorage for persistence
- **Real-time Features**: Would require significant rearchitecture in R2+
- **Developer Experience**: Hybrid paradigm (static + islands) requires context switching

#### Best Fit For
- Projects prioritizing performance and SEO
- Teams comfortable with progressive enhancement
- POCs that need to "feel fast" immediately

#### Scaling Path R1 → R4
```
R1 (POC):    Static pages + React islands + JSON data
R2 (Pilot):  + API routes (Astro server endpoints) + Auth middleware
R3 (Beta):   + Dedicated API layer (separate service) + Database
R4 (1.0):    + Real-time features (WebSocket service) + CDN optimization
```

---

### Approach 2: "Vite + React + TypeScript Stack" (RECOMMENDED)

**Core Philosophy**: Build as a modern SPA with server-side rendering capability, optimized for rapid iteration and "vibe-coding" workflows.

#### Technology Stack
```
├── Framework: React 18+ (with concurrent features)
├── Build Tool: Vite 5.x
├── Routing: TanStack Router (type-safe, file-based)
├── Styling: Tailwind CSS + shadcn/ui components
├── State: Zustand (simple) + TanStack Query (async)
├── Type Safety: TypeScript (strict mode)
├── Deployment: Vercel (with SSR via Vite SSR)
└── Data: TypeScript schemas + Zod validation + JSON fixtures
```

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Page Components                      │  │
│  │  Marketing │ Contribute │ Explore │ Review       │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↓                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Feature-Specific Layouts                │  │
│  │  PasserbyFlow │ LearnerWorkspace │ ExpertQueue  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  COMPONENT LIBRARY                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  ATOMS     │  │ MOLECULES  │  │ ORGANISMS  │       │
│  │ Button     │  │ SignCard   │  │TabletViewer│       │
│  │ Badge      │  │ TaskStep   │  │ReviewQueue │       │
│  │ Avatar     │  │ ConfMeter  │  │CurriculumMod│      │
│  └────────────┘  └────────────┘  └────────────┘       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   STATE MANAGEMENT                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Zustand   │  │  TanStack  │  │   Local    │       │
│  │  (Global)  │  │  (Server)  │  │  (Form)    │       │
│  │ user tier  │  │ tablet data│  │ task input │       │
│  │ progress   │  │ expert list│  │ filters    │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     DATA LAYER                          │
│  ┌────────────────────────────────────────────────┐    │
│  │           API Client (R1: Mock / R4: REST)     │    │
│  │  getTablet() │ getExperts() │ submitTask()    │    │
│  └────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────┐    │
│  │         TypeScript Data Models (Zod)           │    │
│  │  Tablet │ Expert │ Institution │ Transcription │    │
│  └────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────┐    │
│  │         JSON Fixtures (R1) / API (R2+)         │    │
│  │  /data/tablets.json │ /data/experts.json       │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### Project Structure
```
glintstone-frontend/
├── src/
│   ├── app/                      # Application entry points
│   │   ├── main.tsx              # React app root
│   │   └── routes/               # TanStack Router file-based routes
│   │       ├── index.tsx         # Marketing page
│   │       ├── app/              # Main application
│   │       │   ├── contribute/   # Contribution flows
│   │       │   ├── explore/      # Tablet exploration
│   │       │   ├── learn/        # Curriculum
│   │       │   └── review/       # Expert review
│   │       └── __root.tsx        # Root layout
│   │
│   ├── components/               # Component library
│   │   ├── ui/                   # Shadcn components (atoms)
│   │   │   ├── button.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── avatar.tsx
│   │   │   └── ...
│   │   ├── molecules/            # Composed components
│   │   │   ├── sign-card.tsx
│   │   │   ├── confidence-meter.tsx
│   │   │   ├── task-progress.tsx
│   │   │   └── expert-avatar.tsx
│   │   └── organisms/            # Complex feature components
│   │       ├── tablet-viewer.tsx
│   │       ├── review-queue.tsx
│   │       ├── transcription-workspace.tsx
│   │       └── curriculum-module.tsx
│   │
│   ├── features/                 # Feature-specific logic
│   │   ├── passerby/             # Passerby experience
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── stores/
│   │   ├── learner/              # Early learner experience
│   │   └── expert/               # Expert experience
│   │
│   ├── lib/                      # Shared utilities
│   │   ├── api/                  # API client abstraction
│   │   │   ├── client.ts         # Base client
│   │   │   ├── tablets.ts        # Tablet endpoints
│   │   │   ├── experts.ts        # Expert endpoints
│   │   │   └── mock-data.ts      # R1 mock layer
│   │   ├── hooks/                # Shared React hooks
│   │   ├── utils/                # Helper functions
│   │   └── constants.ts          # App-wide constants
│   │
│   ├── types/                    # TypeScript definitions
│   │   ├── models/               # Data models
│   │   │   ├── tablet.ts
│   │   │   ├── expert.ts
│   │   │   ├── institution.ts
│   │   │   ├── transcription.ts
│   │   │   └── user-tier.ts
│   │   └── schemas/              # Zod validation schemas
│   │       └── ...
│   │
│   ├── data/                     # Static data (R1)
│   │   ├── fixtures/
│   │   │   ├── tablets.json
│   │   │   ├── experts.json
│   │   │   ├── institutions.json
│   │   │   └── transcriptions.json
│   │   └── images/               # Local images (R1)
│   │       ├── tablets/
│   │       ├── experts/
│   │       └── institutions/
│   │
│   ├── styles/                   # Global styles
│   │   ├── globals.css           # Tailwind directives
│   │   └── theme.css             # CSS custom properties
│   │
│   └── config/                   # App configuration
│       ├── env.ts                # Environment variables
│       └── feature-flags.ts      # Release toggles
│
├── public/                       # Static assets
│   └── assets/                   # Images, fonts, etc.
│
├── tests/                        # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── vite.config.ts                # Vite configuration
├── tailwind.config.ts            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
└── package.json
```

#### Strengths
- **Developer Experience**: Hot module replacement, instant feedback
- **Type Safety**: Full stack type safety with TypeScript + Zod
- **Component Ecosystem**: Shadcn/ui provides production-ready primitives
- **Flexibility**: Easy to add features without architectural constraints
- **Vibe-Coding Friendly**: Fast iteration, visual feedback, AI-friendly patterns
- **Scalability**: Clear path from mock data to real API integration

#### Weaknesses
- **Bundle Size**: Larger initial JS payload than static approach
- **SEO Complexity**: Requires SSR configuration for marketing page
- **State Management**: Needs disciplined patterns to avoid prop drilling
- **Deployment**: Slightly more complex than pure static hosting

#### Best Fit For
- Projects prioritizing developer velocity and flexibility
- Teams familiar with React ecosystem
- POCs that will evolve into full SPAs

#### Scaling Path R1 → R4
```
R1 (POC):    Mock API layer + JSON fixtures + Local images
R2 (Pilot):  + Real API endpoints + Auth context + CloudFlare R2 images
R3 (Beta):   + WebSocket for real-time updates + Optimistic UI patterns
R4 (1.0):    + Service workers + Offline support + CDN optimization
```

---

### Approach 3: "Full-Stack Framework (Next.js App Router)"

**Core Philosophy**: Build with a full-stack framework that handles routing, data fetching, and server-side logic in a unified paradigm.

#### Technology Stack
```
├── Framework: Next.js 14+ (App Router)
├── UI Components: React Server Components + Client Components
├── Styling: Tailwind CSS + shadcn/ui
├── State: React Context + Server Actions
├── Database: (R1: JSON files, R2+: Prisma + PostgreSQL)
├── Type Safety: TypeScript (strict mode)
├── Deployment: Vercel
└── Data: Server-side data fetching + streaming
```

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│               SERVER COMPONENTS (RSC)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │       Page Components (Server-Rendered)          │  │
│  │  Marketing │ TabletList │ ExpertDirectory        │  │
│  │  (Fetches data on server, streams to client)     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              CLIENT COMPONENTS (CSR)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Interactive Components                    │  │
│  │  TaskCard │ TabletViewer │ TranscriptionEditor   │  │
│  │  (Hydrated on client for interactivity)          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                 SERVER ACTIONS                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  submitTask() │ updateProfile() │ exportTablet() │  │
│  │  (Type-safe RPC from client to server)           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                           │
│  ┌────────────────────────────────────────────────┐    │
│  │         Data Access Functions                  │    │
│  │  getTablets() │ getExperts() │ getInstitutions│    │
│  │  (R1: Read JSON, R2+: Query Database)         │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### Strengths
- **Performance**: Automatic code splitting, image optimization
- **SEO**: Server-side rendering by default
- **Unified Paradigm**: Same framework for frontend and backend
- **Production-Ready**: Battle-tested at scale (Vercel)
- **Streaming**: Can progressively render complex pages

#### Weaknesses
- **Complexity**: App Router learning curve, RSC mental model shift
- **Lock-In**: Tightly coupled to Vercel ecosystem
- **Overkill for R1**: Server components don't add value for static dummy data
- **Debugging**: Server/client boundary bugs can be subtle

#### Best Fit For
- Projects needing immediate SSR and SEO
- Teams already invested in Next.js ecosystem
- Long-term plans requiring complex server-side logic

#### Scaling Path R1 → R4
```
R1 (POC):    JSON data + Static generation + Client components
R2 (Pilot):  + Server actions + Prisma + Auth (NextAuth.js)
R3 (Beta):   + Middleware + Edge functions + Real-time via Pusher
R4 (1.0):    + ISR (Incremental Static Regeneration) + Advanced caching
```

---

## 2. Component Library Structure

### 2.1 Atomic Design Principles

The component library follows modified atomic design with **4 layers** optimized for the three user tiers:

```
ATOMS (UI Primitives - Framework Agnostic)
└─ Pure visual elements with no business logic

MOLECULES (Functional Units - Domain Agnostic)
└─ Combinations of atoms with simple behaviors

ORGANISMS (Feature Components - Domain Specific)
└─ Complex assemblies implementing Glintstone features

TEMPLATES (User Tier Layouts)
└─ Page-level compositions for Passerby, Learner, Expert
```

### 2.2 Component Inventory

#### ATOMS (Shadcn/UI Foundation)
```typescript
// Leveraging shadcn/ui for design system consistency

├── Button           // Primary actions, secondary actions, icon buttons
├── Badge            // Status indicators (Proposed, Accepted, Disputed)
├── Avatar           // Expert headshots, institutional logos
├── Card             // Content containers
├── Input            // Text fields, number fields
├── Select           // Dropdowns for filters
├── Tooltip          // Contextual help
├── Progress         // Task completion, session progress
├── Separator        // Visual dividers
├── Tabs             // View switching (Image/Transcription/Translation)
└── Dialog           // Modals for detailed info
```

**Key Design Token Requirements:**
```typescript
// theme.css - Glintstone-specific tokens

:root {
  /* Authority Status Colors */
  --status-proposed: hsl(210 50% 60%);      /* Muted blue */
  --status-under-review: hsl(45 90% 60%);   /* Amber */
  --status-accepted: hsl(142 76% 36%);      /* Green */
  --status-disputed: hsl(0 70% 50%);        /* Red */
  --status-superseded: hsl(0 0% 60%);       /* Gray */

  /* Confidence Levels */
  --confidence-uncertain: hsl(0 70% 50%);   /* Red */
  --confidence-possible: hsl(30 90% 60%);   /* Orange */
  --confidence-likely: hsl(45 90% 60%);     /* Yellow */
  --confidence-confident: hsl(142 76% 36%); /* Green */
  --confidence-verified: hsl(142 76% 26%);  /* Dark green */

  /* User Tier Colors */
  --tier-passerby: hsl(200 70% 50%);
  --tier-learner: hsl(260 70% 50%);
  --tier-expert: hsl(30 70% 50%);

  /* Brand Alignment (From "Stargazer's Script" if defined) */
  --brand-primary: ...;
  --brand-secondary: ...;
}
```

#### MOLECULES (Glintstone-Specific)

```typescript
// src/components/molecules/

// Sign Recognition Components
├── SignCard                  // Isolated sign + option buttons
│   Props: { signImage, options[], onSelect, allowSkip }
│   States: idle | selected | correct | incorrect
│
├── ConfidenceMeter          // Visual confidence indicator
│   Props: { level: 0-100, variant: 'compact' | 'detailed' }
│   Displays: Color-coded dot/bar + optional percentage
│
├── StatusBadge              // Transcription status display
│   Props: { status: TranscriptionStatus }
│   Variants: Proposed | Under Review | Accepted | Disputed | Superseded
│
├── ExpertAvatar             // Expert headshot with name/affiliation
│   Props: { expert: Expert, size: 'sm' | 'md' | 'lg' }
│   Displays: Avatar image, name, institution logo
│
├── InstitutionLogo          // University/museum logo with name
│   Props: { institution: Institution, variant: 'logo-only' | 'with-name' }
│
├── TaskProgress             // Session progress indicator
│   Props: { current: number, total: number, variant: 'bar' | 'counter' }
│
├── SignHighlight            // Highlighted region overlay for tablet images
│   Props: { region: Region, color: string, onClick }
│
└── FunFact                  // Educational snippet between tasks
    Props: { fact: string, category: 'sign' | 'history' | 'language' }
```

#### ORGANISMS (Complex Features)

```typescript
// src/components/organisms/

// Tablet Interaction
├── TabletViewer             // Main tablet image viewer with interactions
│   Props: { tabletId, highlightRegions?, onRegionClick }
│   Features:
│   - Zoom/pan controls
│   - Sign highlighting
│   - Image loading states
│   - Multiple image angles support (for R2+)
│
├── TranscriptionWorkspace   // Full transcription interface
│   Props: { tabletId, userTier }
│   Features:
│   - Side-by-side: tablet image | transcription input
│   - AI suggestion overlay
│   - Confidence indicators per sign
│   - Save/submit controls
│   - Tier-appropriate tools (simplified for Learner, full for Expert)
│
├── ReviewQueue              // Expert review interface
│   Props: { queueItems, filters }
│   Features:
│   - Priority-sorted list
│   - Batch actions
│   - Quick verdict buttons
│   - Detailed review modal
│
├── CurriculumModule         // Learning module player
│   Props: { moduleId }
│   Features:
│   - Lesson content display
│   - Interactive exercises
│   - Progress tracking
│   - Navigation (prev/next)
│
└── ContributionHistory      // User's contribution timeline
    Props: { userId }
    Features:
    - Chronological list of contributions
    - Status changes visualization
    - Impact metrics
    - Filter by status/type
```

#### TEMPLATES (User Tier Layouts)

```typescript
// src/app/routes/app/ (route-based layouts)

// Passerby Templates
├── PasserbyTaskFlow         // Quick task sequence UI
│   Layout: Full-screen task card → Progress bar → Session summary
│   Components: SignCard, TaskProgress, FunFact, SessionSummary
│
// Early Learner Templates
├── LearnerDashboard         // Main learner workspace
│   Layout: Sidebar nav | Main content | Context panel
│   Components: CurriculumModule, TranscriptionWorkspace, ProgressTracker
│
// Expert Templates
├── ExpertReviewDashboard    // Expert queue and tools
│   Layout: Queue sidebar | Review panel | Evidence panel
│   Components: ReviewQueue, TabletViewer, TranscriptionWorkspace
│
// Shared Templates
└── TabletDetailPage         // Universal tablet view
    Layout: Image viewer | Tabbed content (Transcription/Translation/Context)
    Components: TabletViewer, StatusBadge, ExpertAvatar, ContributionHistory
```

### 2.3 Component Design Specifications

#### Example: SignCard Component

```typescript
// src/components/molecules/sign-card.tsx

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export interface SignOption {
  id: string;
  signImage: string;
  label?: string;
}

export interface SignCardProps {
  signImage: string;
  signImageAlt?: string;
  options: SignOption[];
  allowSkip?: boolean;
  onSelect: (optionId: string) => void;
  onSkip?: () => void;
}

export type SignCardState = 'idle' | 'selected' | 'feedback';

export function SignCard({
  signImage,
  signImageAlt = 'Cuneiform sign to identify',
  options,
  allowSkip = true,
  onSelect,
  onSkip,
}: SignCardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [state, setState] = useState<SignCardState>('idle');

  const handleSelect = (optionId: string) => {
    setSelectedId(optionId);
    setState('selected');
    onSelect(optionId);

    // Automatic transition to next task after brief feedback
    setTimeout(() => {
      setState('idle');
      setSelectedId(null);
    }, 800);
  };

  return (
    <Card className="sign-card p-6 max-w-2xl mx-auto">
      {/* Isolated Sign Display */}
      <div className="sign-display mb-6 flex justify-center">
        <img
          src={signImage}
          alt={signImageAlt}
          className="max-h-32 object-contain border-2 border-border rounded-md p-4 bg-muted"
        />
      </div>

      {/* Instructions */}
      <p className="text-sm text-muted-foreground text-center mb-4">
        Which sign matches the highlighted area?
      </p>

      {/* Options Grid */}
      <div className={`options-grid grid gap-3 mb-4 ${
        options.length === 2 ? 'grid-cols-2' :
        options.length === 3 ? 'grid-cols-3' :
        'grid-cols-2 md:grid-cols-4'
      }`}>
        {options.map((option) => (
          <Button
            key={option.id}
            variant={selectedId === option.id ? 'default' : 'outline'}
            className="sign-option h-24 flex flex-col gap-2 p-2"
            onClick={() => handleSelect(option.id)}
            disabled={state === 'feedback'}
          >
            <img
              src={option.signImage}
              alt={option.label || 'Sign option'}
              className="max-h-12 object-contain"
            />
            {option.label && (
              <span className="text-xs">{option.label}</span>
            )}
          </Button>
        ))}
      </div>

      {/* Skip Option */}
      {allowSkip && (
        <div className="flex justify-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={onSkip}
            disabled={state === 'feedback'}
          >
            None of these / Skip
          </Button>
        </div>
      )}
    </Card>
  );
}
```

#### Example: TabletViewer Component

```typescript
// src/components/organisms/tablet-viewer.tsx

import { useState, useCallback } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { Tablet, Region } from '@/types/models/tablet';
import { SignHighlight } from '@/components/molecules/sign-highlight';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, RotateCw, Maximize } from 'lucide-react';

export interface TabletViewerProps {
  tablet: Tablet;
  highlightRegions?: Region[];
  onRegionClick?: (region: Region) => void;
  enableControls?: boolean;
}

export function TabletViewer({
  tablet,
  highlightRegions = [],
  onRegionClick,
  enableControls = true,
}: TabletViewerProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleRegionClick = useCallback((region: Region) => {
    onRegionClick?.(region);
  }, [onRegionClick]);

  if (imageError) {
    return (
      <div className="tablet-viewer-error flex flex-col items-center justify-center h-96 bg-muted rounded-lg">
        <p className="text-muted-foreground mb-4">Failed to load tablet image</p>
        <Button onClick={() => setImageError(false)}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="tablet-viewer relative w-full h-full bg-muted rounded-lg overflow-hidden">
      <TransformWrapper
        initialScale={1}
        minScale={0.5}
        maxScale={3}
        centerOnInit
      >
        {({ zoomIn, zoomOut, resetTransform }) => (
          <>
            {/* Zoom Controls */}
            {enableControls && (
              <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
                <Button
                  size="icon"
                  variant="secondary"
                  onClick={() => zoomIn()}
                  aria-label="Zoom in"
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  variant="secondary"
                  onClick={() => zoomOut()}
                  aria-label="Zoom out"
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  variant="secondary"
                  onClick={() => resetTransform()}
                  aria-label="Reset view"
                >
                  <Maximize className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Tablet Image with Highlights */}
            <TransformComponent
              wrapperClass="w-full h-full"
              contentClass="w-full h-full flex items-center justify-center"
            >
              <div className="relative">
                {/* Loading State */}
                {!imageLoaded && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="animate-pulse text-muted-foreground">
                      Loading tablet image...
                    </div>
                  </div>
                )}

                {/* Tablet Image */}
                <img
                  src={tablet.imageUrl}
                  alt={`Tablet ${tablet.id}`}
                  className={`max-w-full max-h-full object-contain ${
                    !imageLoaded ? 'opacity-0' : 'opacity-100'
                  } transition-opacity`}
                  onLoad={() => setImageLoaded(true)}
                  onError={() => setImageError(true)}
                />

                {/* Sign Highlights */}
                {highlightRegions.map((region) => (
                  <SignHighlight
                    key={region.id}
                    region={region}
                    onClick={() => handleRegionClick(region)}
                  />
                ))}
              </div>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>

      {/* Tablet Metadata Overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-background/80 backdrop-blur-sm p-3">
        <div className="flex items-center justify-between text-sm">
          <div>
            <span className="font-medium">{tablet.id}</span>
            {tablet.period && (
              <span className="text-muted-foreground ml-2">
                {tablet.period}
              </span>
            )}
          </div>
          {tablet.museum && (
            <span className="text-muted-foreground">{tablet.museum}</span>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 2.4 Tier-Specific Component Variations

Components adapt their complexity based on user tier:

```typescript
// src/components/organisms/transcription-workspace.tsx

export function TranscriptionWorkspace({ tabletId, userTier }: Props) {
  // Simplified interface for Passerby (view-only)
  if (userTier === 'passerby') {
    return <TranscriptionViewer tabletId={tabletId} />;
  }

  // Guided interface for Early Learner (AI assistance, tooltips)
  if (userTier === 'early-learner') {
    return (
      <TranscriptionEditor
        tabletId={tabletId}
        showAISuggestions
        showTooltips
        allowPartialSave
      />
    );
  }

  // Full-featured interface for Expert (all tools, review controls)
  return (
    <TranscriptionEditor
      tabletId={tabletId}
      showAISuggestions
      showConfidenceScores
      showContributorHistory
      allowDisputeCreation
      allowDirectPublication
    />
  );
}
```

---

## 3. Data Model Design

### 3.1 Core Entities

#### Tablet Entity
```typescript
// src/types/models/tablet.ts

import { z } from 'zod';

export const TabletStatusSchema = z.enum([
  'catalog-entry',      // Just imported from CDLI
  'preparation',        // Passerby tasks in progress
  'draft-transcription',// AI + Learners working
  'expert-review',      // In expert queue
  'provisionally-accepted', // One expert approved
  'accepted',           // Multiple experts approved
  'translation',        // Translation in progress
  'published',          // Exported to ORACC/CDLI
]);

export const TabletSchema = z.object({
  // Primary Identification
  id: z.string(),                    // Internal UUID
  cdliId: z.string().nullable(),     // P-number (e.g., "P123456")

  // Metadata
  period: z.string().nullable(),     // "Neo-Assyrian", "Old Babylonian"
  language: z.string().nullable(),   // "Akkadian", "Sumerian"
  genre: z.string().nullable(),      // "Administrative", "Letter", "Literary"
  provenance: z.string().nullable(), // "Nippur", "Ur"
  dateWritten: z.string().nullable(),// "ca. 2100 BCE"

  // Physical Information
  museum: z.string().nullable(),     // "British Museum"
  museumNumber: z.string().nullable(),// "BM 12345"
  institutionId: z.string().nullable(), // FK to Institution

  // Images
  imageUrl: z.string(),              // Primary image URL
  imageUrls: z.array(z.string()),    // Additional angles/RTI
  imageCopyright: z.string().nullable(),

  // Transcription State
  status: TabletStatusSchema,
  transcriptionId: z.string().nullable(), // FK to current Transcription
  translationId: z.string().nullable(),   // FK to current Translation

  // Statistics
  signCount: z.number().int().nullable(),
  lineCount: z.number().int().nullable(),
  contributorCount: z.number().int().default(0),

  // Timestamps
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export type Tablet = z.infer<typeof TabletSchema>;
export type TabletStatus = z.infer<typeof TabletStatusSchema>;

// Region for sign highlighting
export const RegionSchema = z.object({
  id: z.string(),
  tabletId: z.string(),
  lineNumber: z.number().int().nullable(),
  signIndex: z.number().int().nullable(),
  boundingBox: z.object({
    x: z.number(),      // Percentage-based positioning
    y: z.number(),
    width: z.number(),
    height: z.number(),
  }),
  signId: z.string().nullable(), // FK to Sign
});

export type Region = z.infer<typeof RegionSchema>;
```

#### Expert Entity
```typescript
// src/types/models/expert.ts

import { z } from 'zod';

export const ExpertSchema = z.object({
  // Identity
  id: z.string(),
  name: z.string(),
  title: z.string().nullable(),      // "Dr.", "Professor"

  // Professional Information
  affiliation: z.string(),            // University/Institution name
  institutionId: z.string().nullable(), // FK to Institution
  specializations: z.array(z.string()), // ["Neo-Assyrian", "Royal Inscriptions"]

  // Visual Identity (for trust/credibility)
  avatarUrl: z.string().nullable(),   // Headshot photo
  bio: z.string().nullable(),         // Brief background

  // Credentials
  credentials: z.array(z.object({
    type: z.enum(['phd', 'publication', 'position']),
    description: z.string(),
    year: z.number().int().nullable(),
  })),

  // Platform Activity
  reviewCount: z.number().int().default(0),
  acceptedCount: z.number().int().default(0),
  disputesInitiated: z.number().int().default(0),

  // Contact (optional, for collaboration)
  email: z.string().email().nullable(),
  website: z.string().url().nullable(),
  orcid: z.string().nullable(),       // ORCID identifier

  // Timestamps
  joinedAt: z.string().datetime(),
  lastActiveAt: z.string().datetime().nullable(),
});

export type Expert = z.infer<typeof ExpertSchema>;
```

#### Institution Entity
```typescript
// src/types/models/institution.ts

import { z } from 'zod';

export const InstitutionTypeSchema = z.enum([
  'university',
  'museum',
  'research-institute',
  'library',
  'archaeological-mission',
]);

export const InstitutionSchema = z.object({
  // Identity
  id: z.string(),
  name: z.string(),
  shortName: z.string().nullable(),   // "BM" for British Museum
  type: InstitutionTypeSchema,

  // Visual Identity (for trust/credibility)
  logoUrl: z.string().nullable(),     // Official logo
  logoVariant: z.enum(['full', 'mark', 'wordmark']).default('full'),

  // Location
  country: z.string(),
  city: z.string().nullable(),

  // Online Presence
  website: z.string().url().nullable(),

  // Collection Information (for museums)
  collectionSize: z.number().int().nullable(), // Number of tablets held
  hasDigitalCatalog: z.boolean().default(false),

  // Platform Integration
  partnerStatus: z.enum(['none', 'informal', 'formal']).default('none'),

  // Timestamps
  createdAt: z.string().datetime(),
});

export type Institution = z.infer<typeof InstitutionSchema>;
export type InstitutionType = z.infer<typeof InstitutionTypeSchema>;
```

#### Transcription Entity
```typescript
// src/types/models/transcription.ts

import { z } from 'zod';

export const TranscriptionStatusSchema = z.enum([
  'proposed',            // AI-generated or single contributor
  'under-review',        // Multiple contributors, awaiting expert
  'provisionally-accepted', // One expert approved
  'accepted',            // Multiple experts approved
  'disputed',            // Experts disagree
  'superseded',          // Replaced by newer transcription
]);

export const ContributorRoleSchema = z.enum([
  'ai',                  // AI-generated proposal
  'passerby',            // Anonymous/casual contributor
  'early-learner',       // Identified learner
  'expert',              // Verified expert
]);

export const TranscriptionSchema = z.object({
  // Identity
  id: z.string(),
  tabletId: z.string(),           // FK to Tablet
  version: z.number().int(),      // Version number (incremental)

  // Status
  status: TranscriptionStatusSchema,

  // Content (ATF format for compatibility with CDLI/ORACC)
  content: z.string(),            // Full ATF transcription

  // Line-by-Line Breakdown
  lines: z.array(z.object({
    lineNumber: z.number().int(),
    content: z.string(),          // ATF for this line
    confidence: z.number().min(0).max(100).nullable(),
    contributorId: z.string().nullable(),
    contributorRole: ContributorRoleSchema,
  })),

  // Attribution
  contributors: z.array(z.object({
    userId: z.string(),
    role: ContributorRoleSchema,
    contributionType: z.enum([
      'full-transcription',
      'line-correction',
      'sign-identification',
      'review-approval',
    ]),
    timestamp: z.string().datetime(),
  })),

  // Expert Review
  expertReviews: z.array(z.object({
    expertId: z.string(),         // FK to Expert
    verdict: z.enum(['accept', 'reject', 'request-revision', 'dispute']),
    rationale: z.string().nullable(),
    timestamp: z.string().datetime(),
  })),

  // Timestamps
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  publishedAt: z.string().datetime().nullable(),
});

export type Transcription = z.infer<typeof TranscriptionSchema>;
export type TranscriptionStatus = z.infer<typeof TranscriptionStatusSchema>;
export type ContributorRole = z.infer<typeof ContributorRoleSchema>;
```

#### User Contribution Entity
```typescript
// src/types/models/contribution.ts

import { z } from 'zod';

export const ContributionTypeSchema = z.enum([
  'sign-match',          // Passerby task: matched a sign
  'damage-marking',      // Passerby task: marked damaged area
  'line-segmentation',   // Passerby task: identified line breaks
  'sign-transcription',  // Learner: transcribed specific sign
  'line-transcription',  // Learner: transcribed full line
  'translation-draft',   // Learner: attempted translation
  'expert-review',       // Expert: reviewed and approved/rejected
  'dispute-creation',    // Expert: initiated formal disagreement
]);

export const ContributionSchema = z.object({
  // Identity
  id: z.string(),
  userId: z.string().nullable(),     // null for anonymous Passerby
  userTier: z.enum(['passerby', 'early-learner', 'expert']),

  // Target
  type: ContributionTypeSchema,
  tabletId: z.string(),
  transcriptionId: z.string().nullable(),

  // Content
  payload: z.record(z.any()),        // Type-specific data

  // Outcome
  accepted: z.boolean().nullable(),  // null if pending review
  feedback: z.string().nullable(),   // Optional feedback from reviewers

  // Timestamps
  createdAt: z.string().datetime(),
});

export type Contribution = z.infer<typeof ContributionSchema>;
export type ContributionType = z.infer<typeof ContributionTypeSchema>;
```

### 3.2 Data Relationships

```
┌─────────────┐
│ Institution │
│  (logos)    │
└──────┬──────┘
       │ 1
       │
       │ N
┌──────┴──────┐      ┌──────────────┐
│   Expert    │      │    Tablet    │
│ (avatars)   │      │   (images)   │
└──────┬──────┘      └───────┬──────┘
       │ N                   │ 1
       │                     │
       │               N     │
       │          ┌──────────┴──────────┐
       │          │   Transcription     │
       └──────────┤  (status, content)  │
           N      └──────────┬──────────┘
                             │ 1
                             │
                             │ N
                      ┌──────┴──────┐
                      │Contribution │
                      │  (payload)  │
                      └─────────────┘
```

### 3.3 Demo Data Structure

For Release 1, all data is static JSON with local images.

#### Directory Structure
```
src/data/
├── fixtures/
│   ├── tablets.json          // 20-30 representative tablets
│   ├── experts.json          // 10-15 fictional but realistic experts
│   ├── institutions.json     // 5-10 real institutions (with permission)
│   ├── transcriptions.json   // Sample transcriptions at various statuses
│   └── contributions.json    // Sample contribution history
│
└── images/
    ├── tablets/
    │   ├── t001-primary.jpg
    │   ├── t001-reverse.jpg
    │   └── ...
    ├── experts/
    │   ├── e001-avatar.jpg   // AI-generated or stock photos
    │   └── ...
    └── institutions/
        ├── i001-logo.svg     // Real logos (fair use/permission)
        └── ...
```

#### Sample Data: tablets.json
```json
{
  "tablets": [
    {
      "id": "t001",
      "cdliId": "P123456",
      "period": "Neo-Assyrian",
      "language": "Akkadian",
      "genre": "Royal Inscription",
      "provenance": "Nineveh",
      "dateWritten": "ca. 700 BCE",
      "museum": "British Museum",
      "museumNumber": "BM 12345",
      "institutionId": "i001",
      "imageUrl": "/data/images/tablets/t001-primary.jpg",
      "imageUrls": [
        "/data/images/tablets/t001-primary.jpg",
        "/data/images/tablets/t001-reverse.jpg"
      ],
      "imageCopyright": "© Trustees of the British Museum",
      "status": "expert-review",
      "transcriptionId": "tr001",
      "signCount": 47,
      "lineCount": 8,
      "contributorCount": 12,
      "createdAt": "2025-12-01T00:00:00Z",
      "updatedAt": "2026-01-02T15:30:00Z"
    }
  ]
}
```

#### Sample Data: experts.json
```json
{
  "experts": [
    {
      "id": "e001",
      "name": "Dr. Sarah Müller",
      "title": "Associate Professor",
      "affiliation": "University of Chicago",
      "institutionId": "i002",
      "specializations": ["Neo-Assyrian", "Royal Inscriptions"],
      "avatarUrl": "/data/images/experts/e001-avatar.jpg",
      "bio": "Specializes in Neo-Assyrian royal inscriptions with 15 years of experience in cuneiform paleography.",
      "credentials": [
        {
          "type": "phd",
          "description": "PhD in Assyriology, University of Oxford",
          "year": 2010
        },
        {
          "type": "publication",
          "description": "Author of 'Annals of Sennacherib: A Critical Edition'",
          "year": 2018
        }
      ],
      "reviewCount": 47,
      "acceptedCount": 43,
      "disputesInitiated": 2,
      "joinedAt": "2025-11-15T00:00:00Z",
      "lastActiveAt": "2026-01-02T14:22:00Z"
    }
  ]
}
```

#### Sample Data: institutions.json
```json
{
  "institutions": [
    {
      "id": "i001",
      "name": "British Museum",
      "shortName": "BM",
      "type": "museum",
      "logoUrl": "/data/images/institutions/i001-logo.svg",
      "logoVariant": "full",
      "country": "United Kingdom",
      "city": "London",
      "website": "https://www.britishmuseum.org",
      "collectionSize": 130000,
      "hasDigitalCatalog": true,
      "partnerStatus": "formal",
      "createdAt": "2025-11-01T00:00:00Z"
    },
    {
      "id": "i002",
      "name": "University of Chicago",
      "shortName": "UChicago",
      "type": "university",
      "logoUrl": "/data/images/institutions/i002-logo.svg",
      "logoVariant": "mark",
      "country": "United States",
      "city": "Chicago",
      "website": "https://oi.uchicago.edu",
      "partnerStatus": "formal",
      "createdAt": "2025-11-01T00:00:00Z"
    }
  ]
}
```

### 3.4 Scaling Strategy: Dummy Data → Live Data

```
RELEASE 1 (POC)
├── Data Source: JSON files in /src/data/fixtures/
├── Images: Local files in /src/data/images/
└── API Layer: Mock functions reading from JSON

RELEASE 2 (Pilot)
├── Data Source: PostgreSQL database (Prisma ORM)
├── Images: CloudFlare R2 or AWS S3
├── API Layer: REST API (Next.js API routes or Express)
└── Migration: Script to import JSON fixtures into database

RELEASE 3 (Beta)
├── Data Source: PostgreSQL + Redis (caching)
├── Images: CDN (CloudFlare CDN or CloudFront)
├── API Layer: GraphQL (optional) or enhanced REST
└── Integration: CDLI import pipeline (scheduled jobs)

RELEASE 4 (1.0)
├── Data Source: PostgreSQL + Redis + Elasticsearch (search)
├── Images: CDN + image optimization service
├── API Layer: GraphQL + REST + WebSocket (real-time)
└── Integration: Full CDLI/ORACC bidirectional sync
```

#### API Abstraction Layer (supports scaling)

```typescript
// src/lib/api/client.ts

// Abstract client that works with both mock and real data
export interface APIClient {
  tablets: {
    list: (filters?: TabletFilters) => Promise<Tablet[]>;
    get: (id: string) => Promise<Tablet>;
    update: (id: string, data: Partial<Tablet>) => Promise<Tablet>;
  };
  experts: {
    list: () => Promise<Expert[]>;
    get: (id: string) => Promise<Expert>;
  };
  institutions: {
    list: () => Promise<Institution[]>;
    get: (id: string) => Promise<Institution>;
  };
  transcriptions: {
    get: (id: string) => Promise<Transcription>;
    submit: (data: CreateTranscriptionDTO) => Promise<Transcription>;
    review: (id: string, verdict: ReviewVerdict) => Promise<Transcription>;
  };
  contributions: {
    submit: (data: CreateContributionDTO) => Promise<Contribution>;
    list: (userId: string) => Promise<Contribution[]>;
  };
}

// R1 Implementation: Mock data from JSON
// src/lib/api/mock-client.ts
import tabletsData from '@/data/fixtures/tablets.json';
import expertsData from '@/data/fixtures/experts.json';

export const mockClient: APIClient = {
  tablets: {
    list: async (filters) => {
      let tablets = tabletsData.tablets;
      // Apply filters
      if (filters?.status) {
        tablets = tablets.filter(t => t.status === filters.status);
      }
      return tablets;
    },
    get: async (id) => {
      const tablet = tabletsData.tablets.find(t => t.id === id);
      if (!tablet) throw new Error('Tablet not found');
      return tablet;
    },
    update: async (id, data) => {
      // Mock update (no persistence in R1)
      const tablet = await mockClient.tablets.get(id);
      return { ...tablet, ...data };
    },
  },
  // ... similar implementations for other resources
};

// R2+ Implementation: Real API calls
// src/lib/api/http-client.ts
export const httpClient: APIClient = {
  tablets: {
    list: async (filters) => {
      const response = await fetch('/api/tablets', {
        method: 'GET',
        body: JSON.stringify(filters),
      });
      return response.json();
    },
    // ... real implementations
  },
};

// Conditional export based on environment
export const apiClient =
  import.meta.env.MODE === 'demo' ? mockClient : httpClient;
```

---

## 4. Image and Asset Strategy

### 4.1 Image Categories

```
IMAGE ASSETS
├── Tablet Images (Primary)
│   ├── Format: JPEG (lossy compression acceptable)
│   ├── Resolution: 2000px wide max (R1), scalable for R2+
│   ├── Hosting: Local /data/images/ (R1) → CDN (R2+)
│   └── Copyright: Requires attribution (metadata embedded)
│
├── Expert Avatars (Trust Signal)
│   ├── Format: JPEG or WebP
│   ├── Resolution: 400x400px (square)
│   ├── Hosting: Local /data/images/ (R1) → CDN (R2+)
│   └── Source: AI-generated (R1) → Real photos (R2+)
│
├── Institutional Logos (Credibility)
│   ├── Format: SVG preferred, PNG fallback
│   ├── Resolution: Vector (SVG) or 800px wide (PNG)
│   ├── Hosting: Local /data/images/ (R1) → CDN (R2+)
│   └── Usage: Fair use / Permission required
│
└── UI Assets (Brand)
    ├── Format: SVG (icons), WebP (photos)
    ├── Hosting: /public/assets/
    └── Includes: Logo, icons, marketing images
```

### 4.2 R1 (POC) Image Strategy

**Philosophy: Local hosting with production-ready structure**

```
src/data/images/
├── tablets/
│   ├── t001-primary.jpg         # 1500x2000px, JPEG 80% quality
│   ├── t001-reverse.jpg
│   ├── t002-primary.jpg
│   └── ...
│
├── experts/
│   ├── e001-avatar.jpg          # 400x400px, JPEG 90% quality
│   ├── e002-avatar.jpg
│   └── ...
│
└── institutions/
    ├── i001-logo.svg            # Vector preferred
    ├── i002-logo.png            # Fallback if SVG unavailable
    └── ...
```

**Image Sources for R1:**
- Tablet images: Public domain from CDLI or museum open collections
- Expert avatars: AI-generated (e.g., ThisPersonDoesNotExist.com) to avoid rights issues
- Institution logos: Fair use for demo purposes, seek permission for R2+

**Optimization:**
```bash
# Use sharp or imagemagick for batch optimization
npm install sharp

# Optimize all tablet images (example script)
for file in src/data/images/tablets/*.jpg; do
  npx sharp -i "$file" -o "$file.optimized" --jpeg-quality 80 --resize 1500
done
```

### 4.3 R2+ Image Strategy

**Philosophy: CDN-hosted with responsive variants**

```
CLOUDFLARE R2 (or AWS S3) STRUCTURE
├── tablets/
│   ├── t001/
│   │   ├── primary-original.jpg    # Full resolution
│   │   ├── primary-large.webp      # 2000px
│   │   ├── primary-medium.webp     # 1000px
│   │   ├── primary-thumb.webp      # 400px
│   │   └── reverse-original.jpg
│   └── ...
│
├── experts/
│   ├── e001-400.webp
│   ├── e001-200.webp (for list views)
│   └── ...
│
└── institutions/
    ├── i001-logo.svg
    └── ...
```

**Image Delivery:**
- CDN: CloudFlare CDN with automatic WebP conversion
- Lazy loading: Intersection Observer API for below-fold images
- Placeholder strategy: BlurHash or low-quality image placeholder (LQIP)

```typescript
// Example: Responsive Image Component

export function ResponsiveTabletImage({ tablet, priority = false }: Props) {
  const imageUrl = getImageUrl(tablet.imageUrl); // CDN URL helper

  return (
    <img
      src={imageUrl}
      srcSet={`
        ${getImageUrl(tablet.imageUrl, 'thumb')} 400w,
        ${getImageUrl(tablet.imageUrl, 'medium')} 1000w,
        ${getImageUrl(tablet.imageUrl, 'large')} 2000w
      `}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      alt={`Tablet ${tablet.id}`}
      loading={priority ? 'eager' : 'lazy'}
      decoding="async"
    />
  );
}
```

### 4.4 Copyright and Attribution

**Tablet Images:**
- Include copyright metadata in Tablet model (`imageCopyright` field)
- Display attribution in tablet viewer footer
- Link to source institution when available

**Expert Photos:**
- R1: AI-generated (no attribution needed)
- R2+: Require expert consent, store permission in database

**Institution Logos:**
- R1: Fair use for non-commercial demo
- R2+: Formal partnership agreements with logo usage rights

---

## 5. Technology Stack Comparison

### 5.1 Decision Matrix

| Criteria | Approach 1 (Astro) | Approach 2 (Vite+React) | Approach 3 (Next.js) |
|----------|-------------------|------------------------|---------------------|
| **Development Velocity** | Medium | ⭐ High | Medium |
| **Vibe-Coding Fit** | Medium | ⭐ High | Medium |
| **R1 Simplicity** | ⭐ High | High | Medium |
| **Scalability to R4** | Medium | ⭐ High | High |
| **SEO (Marketing Page)** | ⭐ High | Medium | ⭐ High |
| **Learning Curve** | Medium | Low | High |
| **Ecosystem Maturity** | Medium | ⭐ High | ⭐ High |
| **Type Safety** | ⭐ High | ⭐ High | ⭐ High |
| **Deployment Flexibility** | ⭐ High | ⭐ High | Medium (Vercel-optimized) |
| **Cost (Free Tier)** | ⭐ High | ⭐ High | High |
| **Bundle Size** | ⭐ Low | Medium | Medium |
| **AI Agent Friendliness** | Medium | ⭐ High | Medium |

### 5.2 Recommended Stack: Approach 2 (Vite + React + TypeScript)

**Rationale:**

1. **Vibe-Coding Optimized**: Vite's instant HMR and React's component model enable rapid visual iteration
2. **Familiar Ecosystem**: Largest community, most AI agents trained on React patterns
3. **Flexibility**: No framework lock-in, can add SSR later via Vite SSR plugin
4. **Shadcn/UI**: Production-ready component library accelerates R1 delivery
5. **Scaling Path**: Clear progression from client-side to hybrid to full-stack

**Final Stack Specification:**

```yaml
Core:
  - React: 18.3+
  - TypeScript: 5.3+
  - Vite: 5.0+

Routing:
  - TanStack Router: 1.15+ (type-safe, file-based)

UI Components:
  - Shadcn/UI: Latest (Radix primitives + Tailwind)
  - Tailwind CSS: 3.4+
  - Lucide Icons: Latest

State Management:
  - Zustand: 4.5+ (simple global state)
  - TanStack Query: 5.0+ (server state)
  - React Hook Form: 7.5+ (form state)

Data Validation:
  - Zod: 3.22+

Image Optimization:
  - react-zoom-pan-pinch: 3.3+ (tablet viewer)
  - sharp: 0.33+ (build-time optimization)

Development:
  - ESLint: 8.56+
  - Prettier: 3.2+
  - Vitest: 1.2+ (testing)

Deployment:
  - Vercel / Netlify / Cloudflare Pages (static build)
```

---

## 6. Implementation Roadmap

### 6.1 Phase 1: Foundation (Week 1)

**Goal: Establish project structure and design system**

```
Tasks:
├── Initialize Vite + React + TypeScript project
├── Configure Tailwind + Shadcn/UI
├── Define design tokens (colors, typography, spacing)
├── Create foundational atoms (Button, Badge, Avatar, Card)
├── Set up TypeScript models (Tablet, Expert, Institution)
├── Create sample data fixtures (10 tablets, 5 experts, 3 institutions)
└── Set up project structure (components/, types/, data/)

Deliverables:
- Runnable dev environment
- Design system documentation (Storybook optional)
- Sample data loaded and accessible
```

### 6.2 Phase 2: Core Components (Week 2)

**Goal: Build reusable components for all user tiers**

```
Tasks:
├── Molecules
│   ├── SignCard component
│   ├── ConfidenceMeter component
│   ├── StatusBadge component
│   ├── ExpertAvatar component
│   └── TaskProgress component
│
└── Organisms
    ├── TabletViewer component (zoom/pan/highlight)
    ├── ReviewQueue component (expert dashboard)
    └── ContributionHistory component

Deliverables:
- Component library (isolated, testable)
- Unit tests for each component
- Component documentation
```

### 6.3 Phase 3: User Flows (Week 3)

**Goal: Implement primary user journeys**

```
Tasks:
├── Marketing Page
│   ├── Hero section with CTA
│   ├── Value proposition sections
│   └── Social proof (contribution counter)
│
├── Passerby Flow
│   ├── Quick task entry point
│   ├── SignCard task sequence
│   ├── Progress tracking
│   └── Session summary
│
└── Tablet Exploration
    ├── Tablet listing with filters
    ├── Tablet detail page
    └── Transcription display

Deliverables:
- Functional user flows (static data)
- Routing configured
- Basic state management
```

### 6.4 Phase 4: Polish & Integration (Week 4)

**Goal: Refine UX and integrate all flows**

```
Tasks:
├── Early Learner Preview
│   ├── Curriculum landing page
│   └── Guided transcription workspace (simplified)
│
├── Expert Review Preview
│   ├── Review queue with dummy items
│   └── Verdict submission UI
│
├── Cross-Flow Integration
│   ├── Navigation between flows
│   ├── Consistent layouts
│   └── Loading/error states
│
└── Visual Polish
    ├── Animations (task completion, status changes)
    ├── Responsive design (mobile/tablet/desktop)
    └── Accessibility audit

Deliverables:
- Complete POC demo
- Responsive across devices
- Polished animations
```

### 6.5 Phase 5: Deployment & Documentation (Week 5)

**Goal: Deploy and document for stakeholder review**

```
Tasks:
├── Deployment
│   ├── Configure Vercel deployment
│   ├── Set up custom domain (if applicable)
│   └── Performance optimization (bundle analysis)
│
├── Documentation
│   ├── Component architecture document (this document)
│   ├── Deployment guide
│   ├── Contributor guide
│   └── Demo script
│
└── Stakeholder Prep
    ├── Demo walkthrough script
    ├── Feedback collection mechanism
    └── Known limitations document

Deliverables:
- Live demo URL
- Complete documentation suite
- Demo script for presentations
```

---

## 7. Appendices

### Appendix A: File Naming Conventions

```
Components:
  - PascalCase for files: TabletViewer.tsx
  - kebab-case for CSS modules: tablet-viewer.module.css
  - Named exports for components

Types:
  - PascalCase for type files: Tablet.ts
  - Suffix with Schema for Zod: TabletSchema

Data:
  - kebab-case: tablets.json, experts.json
  - Plural for collections

Routes:
  - kebab-case: /app/contribute/transcribe
  - index.tsx for route entry points
```

### Appendix B: Environment Configuration

```bash
# .env.example

# App Configuration
VITE_APP_NAME=Glintstone
VITE_APP_VERSION=1.0.0-poc

# Feature Flags
VITE_ENABLE_EXPERT_REVIEW=true
VITE_ENABLE_LEARNER_CURRICULUM=true
VITE_ENABLE_CDLI_INTEGRATION=false

# Data Source (R1: mock, R2+: api)
VITE_DATA_SOURCE=mock

# API Configuration (R2+)
# VITE_API_BASE_URL=https://api.glintstone.app
# VITE_API_KEY=

# Image Hosting (R1: local, R2+: cdn)
VITE_IMAGE_HOST=local
# VITE_CDN_BASE_URL=https://cdn.glintstone.app
```

### Appendix C: Accessibility Checklist

```
Component Accessibility Requirements:
├── All interactive elements have ARIA labels
├── Color is not the only indicator of status
│   (use icons + patterns alongside color)
├── Keyboard navigation works throughout
│   - Tab order is logical
│   - Escape closes modals/menus
│   - Enter activates buttons
├── Focus indicators are visible
├── Images have alt text
├── Contrast ratios meet WCAG AA (4.5:1 for text)
└── Screen reader testing completed
```

### Appendix D: Component Testing Strategy

```typescript
// Example: SignCard.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { SignCard } from './sign-card';

describe('SignCard', () => {
  const mockOptions = [
    { id: '1', signImage: '/sign1.jpg', label: 'AN' },
    { id: '2', signImage: '/sign2.jpg', label: 'KI' },
  ];

  it('renders sign image and options', () => {
    render(
      <SignCard
        signImage="/target-sign.jpg"
        options={mockOptions}
        onSelect={() => {}}
      />
    );

    expect(screen.getByAltText('Cuneiform sign to identify')).toBeInTheDocument();
    expect(screen.getByText('AN')).toBeInTheDocument();
  });

  it('calls onSelect when option clicked', () => {
    const handleSelect = vi.fn();
    render(
      <SignCard
        signImage="/target-sign.jpg"
        options={mockOptions}
        onSelect={handleSelect}
      />
    );

    fireEvent.click(screen.getByText('AN'));
    expect(handleSelect).toHaveBeenCalledWith('1');
  });

  it('shows skip button when allowSkip is true', () => {
    render(
      <SignCard
        signImage="/target-sign.jpg"
        options={mockOptions}
        onSelect={() => {}}
        allowSkip
      />
    );

    expect(screen.getByText(/skip/i)).toBeInTheDocument();
  });
});
```

### Appendix E: Git Commit Strategy

Following the project's requirement to commit after every key task:

```
Commit Message Format:
<type>(<scope>): <subject>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation only
- style: Formatting, missing semi colons, etc
- refactor: Code change that neither fixes a bug nor adds a feature
- test: Adding missing tests
- chore: Maintain

Examples:
feat(components): Add TabletViewer organism with zoom controls
feat(data): Create sample tablet fixtures with expert attributions
docs(architecture): Complete Phase 3 component architecture proposal
chore(config): Initialize Vite project with TypeScript and Tailwind
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Engineering Architect Agent | Initial architecture proposal |

---

## Next Steps

1. **Stakeholder Review**: Present this proposal for feedback on architectural approach
2. **Technology Validation**: Spin up a minimal Vite + React + Shadcn prototype to validate stack
3. **Data Sourcing**: Identify 20-30 public domain tablet images for R1 fixtures
4. **Asset Creation**: Generate expert avatars and gather institution logos (with permissions)
5. **PRD Alignment**: Ensure this architecture aligns with UX Strategy and PRD Structure documents
6. **Sprint Planning**: Break down Phase 1-5 roadmap into granular tasks for agent execution

---

**This architecture is designed to be actionable, scalable, and aligned with Glintstone's mission to make ancient history accessible through modern technology.**
