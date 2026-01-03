import type { Expert } from '../../types'

type ExpertCardVariant = 'default' | 'compact'

interface ExpertCardProps {
  expert: Expert
  variant?: ExpertCardVariant
  showDetails?: boolean
  className?: string
}

/**
 * ExpertCard - Display expert with avatar and credentials.
 * Use for reviewer attribution and expert endorsements.
 */
export function ExpertCard({
  expert,
  variant = 'default',
  showDetails = true,
  className = ''
}: ExpertCardProps) {
  // Generate initials from name
  const initials = `${expert.firstName[0]}${expert.lastName[0]}`

  if (variant === 'compact') {
    return (
      <article
        className={`
          flex items-center gap-2 p-2
          bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-lg
          ${className}
        `.trim()}
        aria-label={`Expert: ${expert.firstName} ${expert.lastName}`}
      >
        {/* Avatar */}
        <figure className="w-8 h-8 rounded-full overflow-hidden bg-[rgb(var(--accent)/.1)] flex-shrink-0 flex items-center justify-center m-0">
          {expert.avatarUrl ? (
            <img
              src={expert.avatarUrl}
              alt=""
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-sm font-semibold text-[rgb(var(--accent))]">
              {initials}
            </span>
          )}
        </figure>

        {/* Identity */}
        <div className="flex-1 min-w-0">
          <h3 className="m-0 text-sm font-semibold text-[rgb(var(--text))] flex items-center gap-1">
            {expert.firstName} {expert.lastName}
            {expert.credibilityScore >= 90 && (
              <span className="text-[rgb(var(--accent))]" aria-label="Verified expert">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="M9 12l2 2 4-4"/>
                </svg>
              </span>
            )}
          </h3>
          <p className="m-0 text-xs text-[rgb(var(--text-secondary))] truncate">
            {expert.affiliation}
          </p>
        </div>
      </article>
    )
  }

  return (
    <article
      className={`
        bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-lg p-4
        max-w-[280px]
        ${className}
      `.trim()}
      aria-label={`Expert profile: ${expert.firstName} ${expert.lastName}`}
    >
      {/* Header with avatar */}
      <header className="flex gap-3 mb-4">
        <figure className="w-12 h-12 rounded-full overflow-hidden bg-[rgb(var(--accent)/.1)] flex-shrink-0 flex items-center justify-center m-0">
          {expert.avatarUrl ? (
            <img
              src={expert.avatarUrl}
              alt=""
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-lg font-semibold text-[rgb(var(--accent))]">
              {initials}
            </span>
          )}
        </figure>

        <div className="flex-1 min-w-0">
          <h3 className="m-0 text-base font-semibold text-[rgb(var(--text))] flex items-center gap-1">
            {expert.title} {expert.firstName} {expert.lastName}
            {expert.credibilityScore >= 90 && (
              <span className="text-[rgb(var(--accent))]" aria-label="Verified expert">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="M9 12l2 2 4-4"/>
                </svg>
              </span>
            )}
          </h3>
          <p className="m-0 text-sm text-[rgb(var(--text-secondary))]">
            {expert.affiliation}
          </p>
        </div>
      </header>

      {/* Details */}
      {showDetails && (
        <div className="mb-4">
          <dl className="m-0 text-sm">
            <dt className="text-xs text-[rgb(var(--text-muted))] uppercase tracking-wide mb-0.5">
              Specialization
            </dt>
            <dd className="m-0 mb-2 text-[rgb(var(--text-secondary))]">
              {expert.specialization}
            </dd>
            <dt className="text-xs text-[rgb(var(--text-muted))] uppercase tracking-wide mb-0.5">
              Credibility Score
            </dt>
            <dd className="m-0 text-[rgb(var(--text-secondary))]">
              {expert.credibilityScore}/100
            </dd>
          </dl>
        </div>
      )}

      {/* Actions */}
      <footer>
        <a
          href={`/experts/${expert.id}`}
          className="text-sm text-[rgb(var(--accent))] hover:underline"
        >
          View profile
        </a>
      </footer>
    </article>
  )
}
