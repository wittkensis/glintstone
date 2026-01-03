import type { TaskOption } from '../../types'

interface SignCardProps {
  option: TaskOption
  selected?: boolean
  onSelect?: () => void
  showLabel?: boolean
  className?: string
}

/**
 * SignCard - Display isolated sign with option for selection.
 * Use for task options, sign learning, and reference display.
 */
export function SignCard({
  option,
  selected = false,
  onSelect,
  showLabel = true,
  className = ''
}: SignCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`
        relative bg-[rgb(var(--surface))] rounded-lg overflow-hidden
        border-2 transition-all cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))] focus:ring-offset-2 focus:ring-offset-[rgb(var(--background))]
        ${selected
          ? 'border-[rgb(var(--accent))] border-[3px] bg-[rgba(var(--accent),0.1)]'
          : 'border-[rgb(var(--border))] hover:border-[rgb(var(--accent))] hover:shadow-lg'}
        ${className}
      `.trim()}
    >
      {/* Sign Image */}
      <figure className="w-full aspect-square bg-[#f8f4f0] flex items-center justify-center">
        {option.image ? (
          <img
            src={option.image}
            alt={`Cuneiform sign: ${option.label}`}
            className="max-w-[80%] max-h-[80%] object-contain"
          />
        ) : (
          // Placeholder with label as text
          <span className="text-2xl font-serif text-[#5c4a3a]">
            {option.label}
          </span>
        )}
      </figure>

      {/* Label */}
      {showLabel && (
        <div className="p-3 text-center bg-[rgb(var(--surface))]">
          <h3 className="m-0 text-base font-semibold text-[rgb(var(--text))]">
            {option.label}
          </h3>
        </div>
      )}

      {/* Selection indicator */}
      {selected && (
        <span
          className="absolute top-2 right-2 w-6 h-6 bg-[rgb(var(--accent))] rounded-full flex items-center justify-center"
          aria-hidden="true"
        >
          <svg
            className="w-4 h-4 text-black"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
          >
            <path d="M20 6L9 17l-5-5" />
          </svg>
        </span>
      )}
    </button>
  )
}
