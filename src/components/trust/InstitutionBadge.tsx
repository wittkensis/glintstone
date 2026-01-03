import type { Institution } from '../../types'

type BadgeVariant = 'default' | 'logo-only' | 'text'

interface InstitutionBadgeProps {
  institution: Institution
  variant?: BadgeVariant
  className?: string
}

/**
 * InstitutionBadge - Display institution logo and name.
 * Use for source attribution, partnerships, and credibility indicators.
 */
export function InstitutionBadge({
  institution,
  variant = 'default',
  className = ''
}: InstitutionBadgeProps) {
  return (
    <a
      href={`/institutions/${institution.id}`}
      className={`
        inline-flex items-center gap-2 px-3 py-2
        bg-[rgb(var(--background))] rounded-lg
        text-sm text-[rgb(var(--text-secondary))] no-underline
        transition-all
        hover:bg-[rgb(var(--surface))] hover:shadow-md
        ${className}
      `.trim()}
      aria-label={institution.name}
    >
      {/* Logo */}
      {variant !== 'text' && (
        <figure className="w-6 h-6 m-0 flex-shrink-0">
          {institution.logoUrl ? (
            <img
              src={institution.logoUrl}
              alt=""
              className="w-full h-full object-contain"
            />
          ) : (
            // Fallback icon
            <span className="w-full h-full rounded bg-[rgb(var(--accent)/.1)] flex items-center justify-center text-xs font-bold text-[rgb(var(--accent))]">
              {institution.name[0]}
            </span>
          )}
        </figure>
      )}

      {/* Name */}
      {variant !== 'logo-only' && (
        <span className="font-medium">
          {institution.name}
        </span>
      )}

      {/* Partner badge */}
      {institution.partnered && variant === 'default' && (
        <span
          className="ml-1 px-1.5 py-0.5 bg-[rgb(var(--accent)/.1)] text-[rgb(var(--accent))] text-xs rounded font-medium"
          aria-label="Partner institution"
        >
          Partner
        </span>
      )}
    </a>
  )
}
