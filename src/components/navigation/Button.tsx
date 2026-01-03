import { type ReactNode, type ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  loading?: boolean
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: `
    bg-[rgb(var(--accent))] text-black
    hover:brightness-110 active:brightness-95
    focus:ring-[rgb(var(--accent))]
    shadow-[inset_0_2px_4px_0_rgba(255,255,255,0.2),inset_0_-2px_4px_0_rgba(0,0,0,0.3),0_4px_12px_0_rgba(246,173,85,0.25)]
    hover:shadow-[inset_0_2px_4px_0_rgba(255,255,255,0.25),inset_0_-2px_4px_0_rgba(0,0,0,0.35),0_6px_16px_0_rgba(246,173,85,0.35)]
    active:shadow-[inset_0_2px_4px_0_rgba(255,255,255,0.15),inset_0_-1px_2px_0_rgba(0,0,0,0.4),0_2px_4px_0_rgba(246,173,85,0.15)]
  `,
  secondary: `
    bg-[rgb(var(--surface))] border border-[rgb(var(--border))] text-[rgb(var(--text))]
    hover:bg-[rgb(var(--border))] hover:border-[rgb(var(--accent))]
    focus:ring-[rgb(var(--accent))]
    shadow-[inset_0_1px_2px_0_rgba(255,255,255,0.1),inset_0_-1px_2px_0_rgba(0,0,0,0.2),0_2px_8px_0_rgba(0,0,0,0.2)]
    hover:shadow-[inset_0_1px_2px_0_rgba(255,255,255,0.15),inset_0_-1px_2px_0_rgba(0,0,0,0.25),0_4px_12px_0_rgba(0,0,0,0.25)]
  `,
  ghost: `
    bg-transparent text-[rgb(var(--text-secondary))]
    hover:bg-[rgb(var(--background))] hover:text-[rgb(var(--accent))]
    focus:ring-[rgb(var(--accent))]
  `,
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2 text-base gap-2',
  lg: 'px-6 py-3 text-lg gap-2.5',
}

/**
 * Button - Primary/secondary button variants.
 * Use for actions, form submission, and navigation triggers.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <button
      type="button"
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center
        font-semibold rounded-lg cursor-pointer
        transition-all
        focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `.trim()}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  )
}
