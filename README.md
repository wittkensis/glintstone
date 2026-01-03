# Glintstone Release 1 - Frontend Application

A modern web application for Mesopotamian tablet transcription and community contribution, built with Vite, React 18, TypeScript, and Tailwind CSS.

**Demo Scope:** J1 (Marketing) + J2 (Passerby Contribution) journeys implemented. J3-J5 deferred to future phases.

## View Demo

The application is deployed on Vercel and ready for production use.

[View Live Demo on Vercel](https://glintstone.vercel.app) *(To be deployed by user)*

## Project Structure

```
src/
├── components/          # React components
│   ├── layout/         # Container, Stack, Grid layouts
│   ├── navigation/     # Header, Button components
│   ├── task/           # TaskCard, SignMatchTask
│   ├── progress/       # ProgressBar, SessionSummary
│   ├── tablet/         # TabletViewer, SignCard
│   └── trust/          # ExpertCard, InstitutionBadge, StatusBadge
├── routes/             # TanStack Router configuration
│   ├── index.tsx       # J1 Marketing Page
│   └── contribute/     # J2 Contribution Journey
├── stores/             # Zustand state management
│   ├── taskStore.ts    # Task management
│   └── sessionStore.ts # Session tracking
├── types/              # TypeScript type definitions
├── lib/                # Utilities and helpers
├── App.tsx             # Root application component
├── main.tsx            # React entry point
└── index.css           # Global styles with clay textures
```

## Tech Stack

- **Frontend Framework:** React 18 with TypeScript
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS 3 with clay texture overlays
- **State Management:** Zustand
- **Routing:** TanStack Router v1
- **UI Components:** Custom components with Shadcn/UI design patterns
- **Icons:** Lucide React

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will start at `http://localhost:5173`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

This will start a local production server at `http://localhost:4173` for testing.

## Design Tokens

Colors are defined in `tailwind.config.js` and CSS variables in `src/index.css`:

- **Background:** Celestial Navy (`#0a0e14`)
- **Surface:** `#151a23`
- **Border:** `#2d3748`
- **Text:** `#e2e8f0`
- **Accent (Gold):** `#f6ad55`
- **AI Indicator (Violet):** `#9f7aea`

Typography uses serif fonts for headers (Eczar/Spectral) and sans-serif for body (Inter/System).

## State Management

Two main Zustand stores manage application state:

### TaskStore (`src/stores/taskStore.ts`)
- Manages task queue and current task
- Tracks completed task count
- Provides methods to load next task and complete tasks

### SessionStore (`src/stores/sessionStore.ts`)
- Manages contribution sessions
- Tracks tablet ID and contribution count
- Records session statistics (duration, accuracy)

## Data Types

Core types are defined in `src/types/index.ts`:

- `Tablet` - Ancient tablet metadata and images
- `Expert` - Expert contributor profiles
- `Institution` - Partner institutions
- `Task` - Sign matching tasks for contribution
- `SessionStats` - Session completion statistics

## Deployment Instructions

### Deploy to Vercel

1. **Install Vercel CLI (optional)**
   ```bash
   npm i -g vercel
   ```

2. **Deploy with Vercel CLI**
   ```bash
   vercel deploy --prod
   ```

3. **Or Deploy via Vercel Web**
   - Connect your GitHub/GitLab repository to [Vercel Dashboard](https://vercel.com)
   - Select this project
   - Vercel will automatically detect Vite and configure build settings
   - Click "Deploy" to go live

4. **Verify Deployment**
   - Production build will be live at your Vercel URL
   - All routes will work correctly thanks to SPA routing configuration in `vercel.json`
   - Assets and data files are cached appropriately

## Features Implemented

### J1: Marketing Page (6 Sections)
- Hero section with live contribution counter animation
- Social proof with stats and partner institutions
- "How You Can Help" with 3 contribution paths (Passerby active, others deferred)
- "How It Works" 4-step process visualization
- "For Scholars" section with expert testimonials
- Final CTA and footer with navigation

### J2: Passerby Contribution Journey
- Welcome screen with tablet context
- Mini tutorial for sign matching (skippable)
- Task loop with 10 sign matching tasks per session
- Visual progress tracking throughout session
- Session summary with statistics
- "Do More" option to start new session

### Design & Branding
- Celestial Navy dark mode (`#0a0e14`)
- Warm Gold accents (`#f6ad55`) on CTAs
- Clay texture overlays on cards and buttons
- Inset shadow effects for "impressed into clay" feel
- Responsive design for mobile, tablet, and desktop
- Serif fonts for headers (heritage feel), sans-serif for body

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 15+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Notes

- Vite provides instant HMR during development
- Production build is optimized and tree-shaken
- Routes are code-split with lazy loading
- CSS is minified and critical path optimized
- Images should be optimized separately before deployment

## State Management

### TaskStore (Zustand)
Manages the task queue, current task display, and completion tracking for contribution sessions.

### SessionStore (Zustand)
Tracks contribution sessions, tablet context, timing data, and final session statistics.

Both stores persist minimal state to localStorage for session continuity.

## Data Files

- `/public/data/experts.json` - Expert profiles with credentials and avatars
- `/public/data/institutions.json` - Partner institutions and platforms
- `/public/data/tablets.json` - Ancient tablet metadata and images
- `/public/data/tasks.json` - Sign matching tasks for contribution

## Environment Variables

Create a `.env` file for environment-specific configuration:

```
VITE_API_BASE_URL=https://api.example.com
```

(Currently using local JSON files - API integration ready for future phases)

## Troubleshooting

### Build Fails
- Ensure Node.js version 16+ is installed: `node --version`
- Clear node_modules: `rm -rf node_modules && npm install`
- Check for TypeScript errors: `npm run build`

### Routes Not Working After Deploy
- Verify `vercel.json` is in project root
- Ensure SPA rewrites are configured correctly
- Check Vercel project settings for correct output directory (`dist`)

### Styling Issues
- Verify Tailwind CSS is processing: `npm run dev` should show CSS in dev tools
- Check that `src/index.css` imports are present
- Rebuild: `npm run build`

## Development Notes

- Project uses Vite for fast development and optimized builds
- TypeScript enforces type safety throughout
- Zustand provides minimal, scalable state management
- TanStack Router enables type-safe client-side routing
- Tailwind CSS with custom design tokens for consistent branding
- Components follow composition patterns for maximum reusability

## References

- Architecture: `/docs/phase3/component-architecture-proposal.md`
- Component specs: `/docs/phase3/components/*.html`
- Screenflows: `/docs/phase3/screenflows/*.html`
- Implementation guide: `IMPLEMENTATION-QUICK-REF.md`
- Brand identity: `/archive/Demo 1` (visual references)

## License

All rights reserved. Glintstone Release 1 - 2026

## Contact & Support

For issues or questions, refer to the project documentation in `/docs` directory.
