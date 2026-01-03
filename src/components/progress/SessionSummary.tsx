import type { SessionStats } from '../../types'
import { Stack } from '../layout/Stack'

interface SessionSummaryProps {
  stats: SessionStats
  onContinue?: () => void
  onFinish?: () => void
  className?: string
}

/**
 * SessionSummary - End-of-session statistics display.
 * Shows contribution impact, accuracy, and completion celebration.
 */
export function SessionSummary({
  stats,
  onContinue,
  onFinish,
  className = ''
}: SessionSummaryProps) {
  const minutes = Math.floor(stats.duration / 60)
  const seconds = stats.duration % 60

  return (
    <div
      className={`
        bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl p-6
        text-center
        ${className}
      `.trim()}
      role="region"
      aria-label="Session summary"
    >
      <Stack space="lg">
        {/* Celebration header */}
        <div>
          <span
            className="text-4xl block mb-2"
            role="img"
            aria-label="Celebration"
          >
            {stats.accuracy >= 80 ? '🎉' : stats.accuracy >= 50 ? '👍' : '💪'}
          </span>
          <h2 className="m-0 text-2xl font-semibold text-[rgb(var(--text))]">
            Great work!
          </h2>
          <p className="m-0 mt-1 text-[rgb(var(--text-secondary))]">
            You have helped decode ancient history
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-4 py-4 border-y border-[rgb(var(--border))]">
          <div className="text-center">
            <span className="block text-3xl font-bold text-[rgb(var(--accent))]">
              {stats.completedTasks}
            </span>
            <span className="text-sm text-[rgb(var(--text-secondary))]">
              Tasks
            </span>
          </div>
          <div className="text-center">
            <span className="block text-3xl font-bold text-[rgb(var(--accent))]">
              {stats.accuracy}%
            </span>
            <span className="text-sm text-[rgb(var(--text-secondary))]">
              Accuracy
            </span>
          </div>
          <div className="text-center">
            <span className="block text-3xl font-bold text-[rgb(var(--accent))]">
              {minutes}:{seconds.toString().padStart(2, '0')}
            </span>
            <span className="text-sm text-[rgb(var(--text-secondary))]">
              Duration
            </span>
          </div>
        </div>

        {/* Contribution message */}
        <div className="bg-[rgb(var(--background))] rounded-lg p-4">
          <p className="m-0 text-sm text-[rgb(var(--text-secondary))]">
            Your contributions have been added to tablet{' '}
            <strong className="text-[rgb(var(--text))]">{stats.tabletId}</strong>
            {' '}and will help scholars understand ancient Mesopotamian texts.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-center">
          {onContinue && (
            <button
              type="button"
              onClick={onContinue}
              className="
                px-6 py-3 bg-[rgb(var(--accent))] text-black rounded-lg
                font-semibold cursor-pointer transition-all
                hover:brightness-110
                focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))] focus:ring-offset-2
              "
            >
              Continue Contributing
            </button>
          )}
          {onFinish && (
            <button
              type="button"
              onClick={onFinish}
              className="
                px-6 py-3 bg-transparent border border-[rgb(var(--border))] rounded-lg
                text-[rgb(var(--text-secondary))] font-semibold cursor-pointer transition-colors
                hover:bg-[rgb(var(--background))] hover:text-[rgb(var(--text))]
                focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))]
              "
            >
              Finish Session
            </button>
          )}
        </div>
      </Stack>
    </div>
  )
}
