import { type ReactNode } from 'react'

type ContainerSize = 'narrow' | 'default' | 'wide' | 'full'

interface ContainerProps {
  children: ReactNode
  size?: ContainerSize
  className?: string
}

const sizeClasses: Record<ContainerSize, string> = {
  narrow: 'max-w-[640px]',
  default: 'max-w-[1024px]',
  wide: 'max-w-[1280px]',
  full: 'max-w-full',
}

/**
 * Container - Constrains content width and centers it within the viewport.
 * Use for page-level content containment and readable line lengths.
 */
export function Container({
  children,
  size = 'default',
  className = ''
}: ContainerProps) {
  return (
    <div
      className={`
        w-full mx-auto px-4 sm:px-6 lg:px-8
        ${sizeClasses[size]}
        ${className}
      `.trim()}
    >
      {children}
    </div>
  )
}
