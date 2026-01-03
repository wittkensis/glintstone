import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { SessionStats } from '../types'

interface SessionStore {
  contributionCount: number
  tabletId: string | null
  sessionStats: SessionStats | null
  startTime: Date | null

  // Actions
  startSession: (tabletId: string) => void
  endSession: (completedTasks: number, accuracy: number) => SessionStats | null
  incrementContributions: (count: number) => void
  getTotalContributions: () => number
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      contributionCount: 0,
      tabletId: null,
      sessionStats: null,
      startTime: null,

      startSession: (tabletId: string) => {
        set({
          tabletId,
          startTime: new Date(),
          sessionStats: null,
        })
      },

      endSession: (completedTasks: number, accuracy: number) => {
        const state = get()
        const endTime = new Date()
        const startTime = state.startTime || new Date()
        const duration = Math.round((endTime.getTime() - startTime.getTime()) / 1000)

        const stats: SessionStats = {
          completedTasks,
          tabletId: state.tabletId || 'unknown',
          accuracy,
          duration,
          startTime,
          endTime,
        }

        set({
          sessionStats: stats,
          contributionCount: state.contributionCount + completedTasks,
        })

        return stats
      },

      incrementContributions: (count: number) => {
        set((state) => ({
          contributionCount: state.contributionCount + count,
        }))
      },

      getTotalContributions: () => {
        return get().contributionCount
      },
    }),
    {
      name: 'glintstone-session-store',
      partialize: (state) => ({
        contributionCount: state.contributionCount,
      }),
    }
  )
)
