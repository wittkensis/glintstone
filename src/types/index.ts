/**
 * Core data types for Glintstone Release 1
 * Based on IMPLEMENTATION-QUICK-REF.md specifications
 */

export interface Tablet {
  id: string
  cdli_id: string
  museum_number: string
  period: string
  genre: string
  images: {
    obverse: string
    reverse: string
  }
  transcription_status: "untranscribed" | "in_progress" | "verified"
}

export interface Expert {
  id: string
  firstName: string
  lastName: string
  title: string
  affiliation: string
  avatarUrl: string
  specialization: string
  credibilityScore: number
}

export interface Institution {
  id: string
  name: string
  type: "university" | "museum" | "platform"
  logoUrl: string
  partnered: boolean
}

export interface TaskOption {
  id: string
  label: string
  image: string
}

export interface Task {
  id: string
  type: "sign_match"
  tabletId: string
  signImage: string
  options: TaskOption[]
  correctAnswer: string
}

export interface SessionStats {
  completedTasks: number
  tabletId: string
  accuracy: number
  duration: number // in seconds
  startTime: Date
  endTime: Date
}

export interface ContributionCounter {
  total: number
  tablets: number
  lastUpdated: Date
}
