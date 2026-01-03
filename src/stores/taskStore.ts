import { create } from 'zustand'
import type { Task } from '../types'

interface TaskStore {
  currentTask: Task | null
  taskQueue: Task[]
  completedTasks: number
  sessionStart: Date | null
  loadNextTask: () => void
  completeTask: (answer: string) => void
  resetSession: () => void
}

export const useTaskStore = create<TaskStore>((set) => ({
  currentTask: null,
  taskQueue: [],
  completedTasks: 0,
  sessionStart: null,

  loadNextTask: () => {
    set((state) => ({
      currentTask: state.taskQueue[0] || null,
      taskQueue: state.taskQueue.slice(1),
    }))
  },

  completeTask: (_answer: string) => {
    set((state) => ({
      completedTasks: state.completedTasks + 1,
    }))
  },

  resetSession: () => {
    set({
      currentTask: null,
      taskQueue: [],
      completedTasks: 0,
      sessionStart: null,
    })
  },
}))
