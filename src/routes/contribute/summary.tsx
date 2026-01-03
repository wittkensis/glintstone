import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Container, Stack, SessionSummary, Button } from '../../components'
import { useTaskStore } from '../../stores/taskStore'
import { useSessionStore } from '../../stores/sessionStore'
import type { SessionStats } from '../../types'

/**
 * J2 Screen 6: Session Summary
 * Shows contribution impact and options for next steps
 */
export function ContributeSummary() {
  const navigate = useNavigate()
  const { completedTasks, getAccuracy, currentTablet, resetSession, sessionStart } = useTaskStore()
  const { sessionStats, contributionCount } = useSessionStore()
  const [stats, setStats] = useState<SessionStats | null>(null)

  // Build session stats
  useEffect(() => {
    if (completedTasks === 0) {
      // No tasks completed - redirect to welcome
      navigate({ to: '/contribute' })
      return
    }

    // Calculate session duration
    const endTime = new Date()
    const startTime = sessionStart ? new Date(sessionStart) : endTime
    const duration = Math.round((endTime.getTime() - startTime.getTime()) / 1000)

    const calculatedStats: SessionStats = sessionStats || {
      completedTasks,
      tabletId: currentTablet?.cdli_id || 'Unknown',
      accuracy: getAccuracy(),
      duration,
      startTime,
      endTime,
    }

    setStats(calculatedStats)
  }, [completedTasks, getAccuracy, currentTablet, sessionStats, sessionStart, navigate])

  const handleContinue = () => {
    resetSession()
    navigate({ to: '/contribute' })
  }

  const handleFinish = () => {
    resetSession()
    navigate({ to: '/' })
  }

  const handleLearnMore = () => {
    // External link to cuneiform learning resource
    window.open('https://cdli.ucla.edu/tools/SignLists/protocuneiform/archsigns.html', '_blank')
  }

  if (!stats) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-[rgb(var(--accent))] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] py-8 animate-fadeIn">
      <Container size="narrow">
        <Stack space="xl">
          {/* Main summary card */}
          <SessionSummary
            stats={stats}
            onContinue={handleContinue}
            onFinish={handleFinish}
          />

          {/* Additional info card */}
          <div className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl p-6">
            <Stack space="md">
              <h3 className="text-lg font-semibold text-[rgb(var(--text))]">
                Your Impact
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[rgb(var(--background))] rounded-lg p-4 text-center">
                  <span className="block text-2xl font-bold text-[rgb(var(--accent))]">
                    {contributionCount}
                  </span>
                  <span className="text-sm text-[rgb(var(--text-secondary))]">
                    Total Contributions
                  </span>
                </div>
                <div className="bg-[rgb(var(--background))] rounded-lg p-4 text-center">
                  <span className="block text-2xl font-bold text-[rgb(var(--accent))]">
                    {currentTablet?.cdli_id || 'N/A'}
                  </span>
                  <span className="text-sm text-[rgb(var(--text-secondary))]">
                    Tablet Helped
                  </span>
                </div>
              </div>

              <p className="text-sm text-[rgb(var(--text-secondary))]">
                Your contributions help scholars at institutions like Yale, the British Museum,
                and CDLI to transcribe and understand ancient Mesopotamian texts.
              </p>
            </Stack>
          </div>

          {/* Learn more section */}
          <div className="bg-gradient-to-r from-[rgb(var(--accent)/.1)] to-transparent border border-[rgb(var(--accent)/.2)] rounded-xl p-6">
            <Stack space="md">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-[rgb(var(--accent)/.2)] flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-[rgb(var(--accent))]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-[rgb(var(--text))] mb-1">
                    Want to Learn Cuneiform?
                  </h3>
                  <p className="text-sm text-[rgb(var(--text-secondary))] mb-3">
                    Explore resources to learn more about this ancient writing system
                    and become a more advanced contributor.
                  </p>
                  <Button size="sm" variant="secondary" onClick={handleLearnMore}>
                    Explore Learning Resources
                  </Button>
                </div>
              </div>
            </Stack>
          </div>

          {/* Share section (simplified) */}
          <div className="text-center">
            <p className="text-sm text-[rgb(var(--text-muted))] mb-3">
              Share your contribution
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => {
                  const text = `I just helped transcribe ancient cuneiform tablets on Glintstone! ${stats.completedTasks} tasks completed with ${stats.accuracy}% accuracy.`
                  if (navigator.share) {
                    navigator.share({ title: 'Glintstone Contribution', text })
                  } else {
                    navigator.clipboard.writeText(text)
                    alert('Copied to clipboard!')
                  }
                }}
                className="p-3 bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-lg text-[rgb(var(--text-secondary))] hover:bg-[rgb(var(--background))] hover:text-[rgb(var(--text))] transition-colors"
                aria-label="Share"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="18" cy="5" r="3"/>
                  <circle cx="6" cy="12" r="3"/>
                  <circle cx="18" cy="19" r="3"/>
                  <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                  <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                </svg>
              </button>
            </div>
          </div>
        </Stack>
      </Container>
    </div>
  )
}
