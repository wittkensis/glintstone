import { createRootRoute, createRoute, createRouter, Outlet } from '@tanstack/react-router'
import { Suspense, lazy } from 'react'
import { Header } from '../components'

// Lazy load route components for code splitting
const MarketingPage = lazy(() => import('./index').then(m => ({ default: m.MarketingPage })))
const ContributeWelcome = lazy(() => import('./contribute/index').then(m => ({ default: m.ContributeWelcome })))
const ContributeTutorial = lazy(() => import('./contribute/tutorial').then(m => ({ default: m.ContributeTutorial })))
const ContributeTask = lazy(() => import('./contribute/task').then(m => ({ default: m.ContributeTask })))
const ContributeSummary = lazy(() => import('./contribute/summary').then(m => ({ default: m.ContributeSummary })))

// Loading component
function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-[rgb(var(--accent))] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-[rgb(var(--text-secondary))]">Loading...</p>
      </div>
    </div>
  )
}

// Layout component wrapping all routes
function RootLayout() {
  return (
    <div className="min-h-screen bg-[rgb(var(--background))]">
      <Header
        navItems={[
          { label: 'Home', href: '/' },
          { label: 'Contribute', href: '/contribute' },
        ]}
      />
      <main id="main-content">
        <Suspense fallback={<PageLoader />}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  )
}

// Root route
const rootRoute = createRootRoute({
  component: RootLayout,
})

// J1: Marketing Page (Homepage)
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <MarketingPage />,
})

// J2: Contribution Flow Routes
const contributeIndexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/contribute',
  component: () => <ContributeWelcome />,
})

const contributeTutorialRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/contribute/tutorial',
  component: () => <ContributeTutorial />,
})

const contributeTaskRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/contribute/task',
  component: () => <ContributeTask />,
})

const contributeSummaryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/contribute/summary',
  component: () => <ContributeSummary />,
})

// Build route tree
const routeTree = rootRoute.addChildren([
  indexRoute,
  contributeIndexRoute,
  contributeTutorialRoute,
  contributeTaskRoute,
  contributeSummaryRoute,
])

// Create router instance
export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
})

// Type registration for TypeScript
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
