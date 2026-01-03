import { type ReactNode } from 'react'

interface TaskCardProps {
  children: ReactNode
  title: string
  current: number
  total: number
  onSkip?: () => void
  className?: string
}

/**
 * TaskCard - Container for a task with progress indicator.
 * Wraps task content with consistent header, progress, and actions.
 */
export function TaskCard({
  children,
  title,
  current,
  total,
  onSkip,
  className = ''
}: TaskCardProps) {
  const progress = Math.round((current / total) * 100)

  return (
    <article
      className={`
        bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl
        overflow-hidden
        ${className}
      `.trim()}
      aria-label={title}
    >
      {/* Header */}
      <header className="p-4 border-b border-[rgb(var(--border))] flex items-center justify-between">
        <h2 className="m-0 text-lg font-semibold text-[rgb(var(--text))]">
          {title}
        </h2>
        <span
          className="text-sm text-[rgb(var(--text-secondary))]"
          aria-label={`Task ${current} of ${total}`}
        >
          {current} / {total}
        </span>
      </header>

      {/* Progress bar */}
      <div
        className="h-1 bg-[rgb(var(--background))]"
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`Progress: ${progress}%`}
      >
        <div
          className="h-full bg-[rgb(var(--accent))] transition-[width] duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Content */}
      <div className="p-4 sm:p-6">
        {children}
      </div>

      {/* Footer actions */}
      {onSkip && (
        <footer className="p-4 border-t border-[rgb(var(--border))] flex justify-end">
          <button
            type="button"
            onClick={onSkip}
            className="
              px-4 py-2 bg-transparent border border-[rgb(var(--border))]
              rounded text-sm text-[rgb(var(--text-secondary))]
              cursor-pointer transition-colors
              hover:bg-[rgb(var(--background))] hover:text-[rgb(var(--text))]
              focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))]
            "
          >
            Skip task
          </button>
        </footer>
      )}
    </article>
  )
}
