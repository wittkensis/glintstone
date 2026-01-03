import { useEffect, useState } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { Container, Stack, Button, TabletViewer } from '../../components'
import { useTaskStore } from '../../stores/taskStore'
import { useSessionStore } from '../../stores/sessionStore'
import type { Tablet, Task } from '../../types'

/**
 * J2 Screen 1: Welcome
 * Displays tablet context and prepares the user for contribution
 */
export function ContributeWelcome() {
  const navigate = useNavigate()
  const { resetSession, setTasks, setCurrentTablet } = useTaskStore()
  const { startSession } = useSessionStore()
  const [tablet, setTablet] = useState<Tablet | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Reset session state
    resetSession()

    // Load tasks and select a tablet
    Promise.all([
      fetch('/data/tasks.json').then(res => res.json()),
      fetch('/data/tablets.json').then(res => res.json()),
    ])
      .then(([tasksData, tabletsData]: [Task[], Tablet[]]) => {
        // Pick a random tablet with untranscribed status, or fallback to first
        const untranscribed = tabletsData.filter(t => t.transcription_status === 'untranscribed')
        const selectedTablet = untranscribed.length > 0
          ? untranscribed[Math.floor(Math.random() * untranscribed.length)]
          : tabletsData[0]

        setTablet(selectedTablet)

        // Filter tasks for this tablet and take first 10
        const tabletTasks = tasksData.filter((t: Task) => t.tabletId === selectedTablet.id)
        // If not enough tasks for this tablet, shuffle all tasks and take 10
        const sessionTasks = tabletTasks.length >= 10
          ? tabletTasks.slice(0, 10)
          : tasksData.sort(() => Math.random() - 0.5).slice(0, 10)

        setTasks(sessionTasks)
        setCurrentTablet(selectedTablet)
        startSession(selectedTablet.id)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load data:', err)
        setError('Failed to load contribution data. Please try again.')
        setLoading(false)
      })
  }, [resetSession, setTasks, setCurrentTablet, startSession])

  const handleStart = () => {
    navigate({ to: '/contribute/tutorial' })
  }

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[rgb(var(--accent))] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[rgb(var(--text-secondary))]">Loading your contribution session...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Container size="narrow">
          <div className="text-center bg-[rgb(var(--surface))] border border-red-500/50 rounded-xl p-8">
            <p className="text-red-400 mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </div>
        </Container>
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] py-8 animate-fadeIn">
      <Container size="narrow">
        <Stack space="xl">
          {/* Welcome header */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-[rgb(var(--text))] mb-2">
              Welcome, Contributor!
            </h1>
            <p className="text-[rgb(var(--text-secondary))]">
              You are about to help transcribe an ancient cuneiform tablet
            </p>
          </div>

          {/* Tablet preview card */}
          <article className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl overflow-hidden">
            {/* Tablet image */}
            <div className="aspect-video bg-[rgb(var(--background))] relative">
              {tablet && (
                <TabletViewer
                  tablet={tablet}
                  className="w-full h-full"
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-[rgb(var(--surface))] to-transparent" />
            </div>

            {/* Tablet info */}
            <div className="p-6">
              <Stack space="md">
                <div>
                  <span className="text-xs text-[rgb(var(--accent))] uppercase tracking-wide">
                    Today's Tablet
                  </span>
                  <h2 className="text-xl font-semibold text-[rgb(var(--text))]">
                    {tablet?.cdli_id || 'CDLI Tablet'}
                  </h2>
                </div>

                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-[rgb(var(--text-muted))]">Period</dt>
                    <dd className="text-[rgb(var(--text))]">{tablet?.period || 'Unknown'}</dd>
                  </div>
                  <div>
                    <dt className="text-[rgb(var(--text-muted))]">Genre</dt>
                    <dd className="text-[rgb(var(--text))]">{tablet?.genre || 'Unknown'}</dd>
                  </div>
                  <div>
                    <dt className="text-[rgb(var(--text-muted))]">Museum Number</dt>
                    <dd className="text-[rgb(var(--text))]">{tablet?.museum_number || 'N/A'}</dd>
                  </div>
                  <div>
                    <dt className="text-[rgb(var(--text-muted))]">Status</dt>
                    <dd className="text-[rgb(var(--accent))] capitalize">
                      {tablet?.transcription_status?.replace('_', ' ') || 'Pending'}
                    </dd>
                  </div>
                </dl>
              </Stack>
            </div>
          </article>

          {/* Session info */}
          <div className="bg-[rgb(var(--surface)/.5)] rounded-lg p-4 border border-[rgb(var(--border))]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[rgb(var(--accent)/.1)] flex items-center justify-center">
                <svg className="w-5 h-5 text-[rgb(var(--accent))]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
              </div>
              <div>
                <p className="text-[rgb(var(--text))] font-medium">Takes approximately 3 minutes</p>
                <p className="text-sm text-[rgb(var(--text-secondary))]">
                  10 quick sign-matching tasks
                </p>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button size="lg" variant="primary" onClick={handleStart}>
              Start Contributing
            </Button>
            <Link to="/">
              <Button size="lg" variant="secondary">
                Back to Home
              </Button>
            </Link>
          </div>
        </Stack>
      </Container>
    </div>
  )
}
