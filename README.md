# Glintstone Release 1 - Frontend Application

A modern web application for Mesopotamian tablet transcription and community contribution, built with Vite, React 18, TypeScript, and Tailwind CSS.

## Project Structure

```
src/
├── components/          # React components
├── stores/              # Zustand store definitions
│   ├── taskStore.ts     # Task management state
│   └── sessionStore.ts  # Session and contribution tracking
├── routes/              # TanStack Router configuration
│   └── router.tsx       # Route definitions
├── lib/                 # Utilities and helpers
│   └── utils.ts         # cn() utility for class merging
├── types/               # TypeScript type definitions
│   └── index.ts         # Core data types
├── App.tsx              # Root application component
├── main.tsx             # React entry point
└── index.css            # Global styles with Tailwind
```

## Tech Stack

- **Frontend Framework:** React 18 with TypeScript
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS 3 with dark mode support
- **State Management:** Zustand
- **Routing:** TanStack Router v1
- **UI Components:** Shadcn/UI (ready to install)
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

## Next Steps

1. **Create Dummy Data**
   - `/public/data/tablets.json` - 5-10 sample tablets
   - `/public/data/tasks.json` - 30-50 sample tasks
   - `/public/images/` - Tablet and sign images

2. **Build J1 (Marketing) Journey**
   - Hero section with CTA
   - Social proof section
   - How you can help
   - How it works (4 steps)
   - For scholars section
   - Final CTA and footer

3. **Build J2 (Passerby Contribution) Journey**
   - Welcome screen
   - Mini tutorial
   - Task loop (3-5 screens)
   - Session summary
   - Error handling states

4. **Implement Router Configuration**
   - Connect journey pages to routes
   - Setup navigation between screens

## Development Notes

- Project initialization complete with all build configs
- Tailwind CSS configured with design token colors
- Zustand stores ready for implementation
- Type definitions match IMPLEMENTATION-QUICK-REF.md
- `.gitignore` properly configured for production build

## References

- Architecture: `/docs/phase3/component-architecture-proposal.md`
- Component specs: `/docs/phase3/components/*.html`
- Screenflows: `/docs/phase3/screenflows/*.html`
- Implementation guide: `IMPLEMENTATION-QUICK-REF.md`

## License

All rights reserved. Glintstone Release 1 - 2026
