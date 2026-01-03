import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Task, Tablet } from '../types'

interface TaskStore {
  currentTask: Task | null
  taskQueue: Task[]
  completedTasks: number
  correctAnswers: number
  sessionStart: Date | null
  currentTablet: Tablet | null
  taskIndex: number
  totalTasks: number

  // Actions
  setTasks: (tasks: Task[]) => void
  setCurrentTablet: (tablet: Tablet) => void
  loadNextTask: () => void
  completeTask: (answer: string, isCorrect: boolean) => void
  skipTask: () => void
  resetSession: () => void
  getAccuracy: () => number
}

export const useTaskStore = create<TaskStore>()(
  persist(
    (set, get) => ({
      currentTask: null,
      taskQueue: [],
      completedTasks: 0,
      correctAnswers: 0,
      sessionStart: null,
      currentTablet: null,
      taskIndex: 0,
      totalTasks: 10,

      setTasks: (tasks: Task[]) => {
        set({
          taskQueue: tasks.slice(1),
          currentTask: tasks[0] || null,
          totalTasks: tasks.length,
          taskIndex: 1,
          completedTasks: 0,
          correctAnswers: 0,
          sessionStart: new Date(),
        })
      },

      setCurrentTablet: (tablet: Tablet) => {
        set({ currentTablet: tablet })
      },

      loadNextTask: () => {
        const state = get()
        if (state.taskQueue.length > 0) {
          set({
            currentTask: state.taskQueue[0],
            taskQueue: state.taskQueue.slice(1),
            taskIndex: state.taskIndex + 1,
          })
        } else {
          set({ currentTask: null })
        }
      },

      completeTask: (_answer: string, isCorrect: boolean) => {
        set((state) => ({
          completedTasks: state.completedTasks + 1,
          correctAnswers: isCorrect ? state.correctAnswers + 1 : state.correctAnswers,
        }))
      },

      skipTask: () => {
        const state = get()
        if (state.taskQueue.length > 0) {
          set({
            currentTask: state.taskQueue[0],
            taskQueue: state.taskQueue.slice(1),
            taskIndex: state.taskIndex + 1,
          })
        } else {
          set({ currentTask: null })
        }
      },

      resetSession: () => {
        set({
          currentTask: null,
          taskQueue: [],
          completedTasks: 0,
          correctAnswers: 0,
          sessionStart: null,
          currentTablet: null,
          taskIndex: 0,
          totalTasks: 10,
        })
      },

      getAccuracy: () => {
        const state = get()
        if (state.completedTasks === 0) return 0
        return Math.round((state.correctAnswers / state.completedTasks) * 100)
      },
    }),
    {
      name: 'glintstone-task-store',
      partialize: (state) => ({
        completedTasks: state.completedTasks,
        correctAnswers: state.correctAnswers,
      }),
    }
  )
)
