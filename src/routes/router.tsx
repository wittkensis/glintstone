import { createRootRoute, createRouter } from '@tanstack/react-router'
import App from '../App'

// Root route placeholder
const rootRoute = createRootRoute({
  component: App,
})

// Route structure for J1 (Marketing) and J2 (Contribution)
// Additional routes will be created once journey pages are built:
// - J1: Marketing page route - path: /
// - J2: Contribution routes
//   - /contribute - Welcome screen
//   - /contribute/task - Task loop
//   - /contribute/summary - Session summary

const routeTree = rootRoute.addChildren([])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
