import { create } from 'zustand'
import type { SessionStats } from '../types'

interface SessionStore {
  contributionCount: number
  tabletId: string | null
  sessionStats: SessionStats | null
  startSession: (tabletId: string) => void
  endSession: () => SessionStats | null
  incrementContributions: (count: number) => void
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  contributionCount: 0,
  tabletId: null,
  sessionStats: null,

  startSession: (tabletId: string) => {
    set({
      tabletId,
      sessionStats: {
        completedTasks: 0,
        tabletId,
        accuracy: 0,
        duration: 0,
        startTime: new Date(),
        endTime: new Date(),
      },
    })
  },

  endSession: () => {
    const state = get()
    if (state.sessionStats) {
      const endTime = new Date()
      const stats: SessionStats = {
        ...state.sessionStats,
        endTime,
        duration: Math.round((endTime.getTime() - state.sessionStats.startTime.getTime()) / 1000),
      }
      set({ sessionStats: stats })
      return stats
    }
    return null
  },

  incrementContributions: (count: number) => {
    set((state) => ({
      contributionCount: state.contributionCount + count,
    }))
  },
}))
