type StatusType =
  | 'proposed'
  | 'under-review'
  | 'provisionally-accepted'
  | 'accepted'
  | 'disputed'
  | 'superseded'

type StatusVariant = 'default' | 'compact' | 'pill'

interface StatusBadgeProps {
  status: StatusType
  variant?: StatusVariant
  interactive?: boolean
  onClick?: () => void
  className?: string
}

const statusConfig: Record<
  StatusType,
  { label: string; icon: string; colorClass: string; borderStyle: string }
> = {
  proposed: {
    label: 'Proposed',
    icon: 'M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01',
    colorClass: 'bg-amber-50 text-amber-800 border-amber-400',
    borderStyle: 'border-dashed',
  },
  'under-review': {
    label: 'Under Review',
    icon: 'M12 6v6l4 2',
    colorClass: 'bg-blue-50 text-blue-800 border-blue-500',
    borderStyle: 'border-solid',
  },
  'provisionally-accepted': {
    label: 'Provisionally Accepted',
    icon: 'M20 6L9 17l-5-5',
    colorClass: 'bg-emerald-50 text-emerald-700 border-emerald-500',
    borderStyle: 'border-solid',
  },
  accepted: {
    label: 'Accepted',
    icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 12l2 2 4-4',
    colorClass: 'bg-green-100 text-green-800 border-green-500',
    borderStyle: 'border-solid border-2',
  },
  disputed: {
    label: 'Disputed',
    icon: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
    colorClass: 'bg-red-50 text-red-800 border-red-500',
    borderStyle: 'border-double border-[3px]',
  },
  superseded: {
    label: 'Superseded',
    icon: 'M3 6h18M6 6v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6',
    colorClass: 'bg-gray-100 text-gray-500 border-gray-300 line-through',
    borderStyle: 'border-solid',
  },
}

/**
 * StatusBadge - Display verification status per Contextual Authority Model.
 * Authority is always visible, never hidden. Use to indicate trust level of content.
 */
export function StatusBadge({
  status,
  variant = 'default',
  interactive = false,
  onClick,
  className = ''
}: StatusBadgeProps) {
  const config = statusConfig[status]
  const Element = interactive ? 'button' : 'span'

  if (variant === 'compact') {
    return (
      <Element
        type={interactive ? 'button' : undefined}
        onClick={interactive ? onClick : undefined}
        aria-label={`Status: ${config.label}`}
        className={`
          w-5 h-5 p-0.5 rounded-full border flex items-center justify-center
          ${config.colorClass}
          ${config.borderStyle}
          ${interactive ? 'cursor-pointer hover:shadow' : 'cursor-default'}
          ${className}
        `.trim()}
      >
        <svg
          className="w-3 h-3"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d={config.icon} />
          {(status === 'proposed' || status === 'under-review') && (
            <circle cx="12" cy="12" r="10" />
          )}
        </svg>
      </Element>
    )
  }

  return (
    <Element
      type={interactive ? 'button' : undefined}
      onClick={interactive ? onClick : undefined}
      aria-label={interactive ? `Status: ${config.label}. Click for details` : undefined}
      className={`
        inline-flex items-center gap-1 px-2 py-1 text-xs font-medium border
        ${variant === 'pill' ? 'rounded-full px-3' : 'rounded'}
        ${config.colorClass}
        ${config.borderStyle}
        ${interactive ? 'cursor-pointer hover:shadow transition-shadow focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))]' : 'cursor-default'}
        ${className}
      `.trim()}
    >
      <svg
        className="w-3 h-3"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d={config.icon} />
        {(status === 'proposed' || status === 'under-review') && (
          <circle cx="12" cy="12" r="10" />
        )}
      </svg>
      <span>{config.label}</span>
    </Element>
  )
}
