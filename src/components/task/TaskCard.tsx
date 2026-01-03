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
        overflow-hidden relative
        shadow-[inset_0_1px_2px_0_rgba(255,255,255,0.05),0_4px_12px_0_rgba(0,0,0,0.3)]
        ${className}
      `.trim()}
      aria-label={title}
    >
      {/* Clay texture overlay */}
      <div
        className="absolute inset-0 rounded-xl pointer-events-none z-0"
        style={{
          backgroundImage: `
            radial-gradient(circle at 2px 2px, rgba(0, 0, 0, 0.08) 1px, transparent 1px),
            radial-gradient(circle at 5px 4px, rgba(0, 0, 0, 0.06) 1px, transparent 1px),
            radial-gradient(circle at 3px 6px, rgba(0, 0, 0, 0.1) 1px, transparent 1px),
            radial-gradient(circle at 6px 3px, rgba(0, 0, 0, 0.07) 1px, transparent 1px)
          `,
          backgroundSize: '7px 7px',
        }}
      />
      {/* Header */}
      <header className="relative z-10 p-4 border-b border-[rgb(var(--border))] flex items-center justify-between">
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
        className="relative z-10 h-1 bg-[rgb(var(--background))]"
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
      <div className="relative z-10 p-4 sm:p-6">
        {children}
      </div>

      {/* Footer actions */}
      {onSkip && (
        <footer className="relative z-10 p-4 border-t border-[rgb(var(--border))] flex justify-end">
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
