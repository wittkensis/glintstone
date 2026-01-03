type ProgressSize = 'sm' | 'md' | 'lg'

interface ProgressBarProps {
  value: number
  max?: number
  size?: ProgressSize
  showLabel?: boolean
  className?: string
}

const sizeClasses: Record<ProgressSize, string> = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
}

/**
 * ProgressBar - Linear progress indicator.
 * Use for session progress, completion tracking, and loading states.
 */
export function ProgressBar({
  value,
  max = 100,
  size = 'md',
  showLabel = false,
  className = ''
}: ProgressBarProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div
      className={`flex items-center gap-3 ${className}`}
    >
      <div
        className={`
          flex-1 rounded-full bg-[rgb(var(--background))] overflow-hidden
          ${sizeClasses[size]}
        `}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={`Progress: ${Math.round(percent)}%`}
      >
        <div
          className="h-full bg-[rgb(var(--accent))] transition-[width] duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-[rgb(var(--text-secondary))] min-w-[3rem] text-right">
          {Math.round(percent)}%
        </span>
      )}
    </div>
  )
}
