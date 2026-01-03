import { useState } from 'react'
import LogoDingir from '../../assets/logo-dingir-mono.svg?react'

type NavItem = {
  label: string
  href: string
  current?: boolean
}

interface HeaderProps {
  navItems?: NavItem[]
  onSearch?: () => void
  user?: { initials: string; name: string } | null
  className?: string
}

/**
 * Header - Site header with navigation.
 * Provides global navigation, branding, and user actions.
 */
export function Header({
  navItems = [],
  onSearch,
  user,
  className = ''
}: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <>
      {/* Skip link */}
      <a
        href="#main-content"
        className="
          absolute top-[-40px] left-0 z-[1000] px-4 py-2
          bg-[rgb(var(--accent))] text-black
          focus:top-0 transition-[top]
        "
      >
        Skip to main content
      </a>

      <header
        className={`
          bg-[rgb(var(--surface))] border-b border-[rgb(var(--border))]
          sticky top-0 z-50
          ${className}
        `.trim()}
        role="banner"
      >
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <a
              href="/"
              className="flex items-center gap-3 font-semibold text-[rgb(var(--text))] no-underline"
              aria-label="Glintstone home"
            >
              <LogoDingir className="w-8 h-8 text-[rgb(var(--accent))]" aria-hidden="true" />
              <span>Glintstone</span>
            </a>

            {/* Desktop navigation */}
            <nav
              className="hidden md:flex items-center gap-1"
              aria-label="Main navigation"
            >
              {navItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  aria-current={item.current ? 'page' : undefined}
                  className={`
                    inline-flex items-center gap-2 px-3 py-2
                    text-sm font-medium rounded transition-colors
                    no-underline
                    ${item.current
                      ? 'text-[rgb(var(--accent))] font-semibold relative after:content-[""] after:absolute after:bottom-0 after:left-3 after:right-3 after:h-0.5 after:bg-[rgb(var(--accent))] after:rounded'
                      : 'text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text))] hover:bg-[rgb(var(--background))]'
                    }
                  `}
                >
                  {item.label}
                </a>
              ))}
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* Search button */}
              {onSearch && (
                <button
                  type="button"
                  onClick={onSearch}
                  aria-label="Search"
                  className="
                    p-2 text-[rgb(var(--text-secondary))] rounded
                    hover:text-[rgb(var(--text))] hover:bg-[rgb(var(--background))]
                    transition-colors cursor-pointer
                    focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))]
                  "
                >
                  <svg
                    className="w-5 h-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                </button>
              )}

              {/* User menu */}
              {user && (
                <button
                  type="button"
                  aria-label="User menu"
                  aria-haspopup="menu"
                  className="
                    w-9 h-9 rounded-full
                    bg-[rgb(var(--accent)/.1)] text-[rgb(var(--accent))]
                    font-semibold text-sm
                    flex items-center justify-center cursor-pointer
                    hover:bg-[rgb(var(--accent)/.2)]
                    focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))]
                  "
                >
                  {user.initials}
                </button>
              )}

              {/* Mobile menu toggle */}
              <button
                type="button"
                aria-label="Open menu"
                aria-expanded={mobileMenuOpen}
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="
                  md:hidden p-2 text-[rgb(var(--text-secondary))]
                  rounded hover:bg-[rgb(var(--background))] cursor-pointer
                  focus:outline-none focus:ring-2 focus:ring-[rgb(var(--accent))]
                "
              >
                <svg
                  className="w-6 h-6"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  {mobileMenuOpen ? (
                    <>
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </>
                  ) : (
                    <>
                      <line x1="3" y1="12" x2="21" y2="12"/>
                      <line x1="3" y1="6" x2="21" y2="6"/>
                      <line x1="3" y1="18" x2="21" y2="18"/>
                    </>
                  )}
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <nav
            className="md:hidden border-t border-[rgb(var(--border))]"
            aria-label="Mobile navigation"
          >
            <ul className="p-4 space-y-1 list-none m-0">
              {navItems.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    aria-current={item.current ? 'page' : undefined}
                    className={`
                      block px-4 py-3 rounded text-base no-underline
                      ${item.current
                        ? 'bg-[rgb(var(--accent)/.1)] text-[rgb(var(--accent))] font-medium'
                        : 'text-[rgb(var(--text-secondary))] hover:bg-[rgb(var(--background))] hover:text-[rgb(var(--text))]'
                      }
                    `}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </header>
    </>
  )
}
