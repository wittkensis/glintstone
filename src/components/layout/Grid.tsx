import { type ReactNode } from 'react'

type GridColumns = 'auto' | 2 | 3 | 4
type GridGap = 'sm' | 'md' | 'lg'

interface GridProps {
  children: ReactNode
  columns?: GridColumns
  gap?: GridGap
  className?: string
}

const gapClasses: Record<GridGap, string> = {
  sm: 'gap-2',
  md: 'gap-4',
  lg: 'gap-6',
}

/**
 * Grid - Creates multi-column layouts with responsive behavior.
 * Use for card grids, feature sections, and dashboard widgets.
 */
export function Grid({
  children,
  columns = 'auto',
  gap = 'md',
  className = ''
}: GridProps) {
  // Determine grid column classes
  let columnClass = ''
  if (columns === 'auto') {
    columnClass = 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-[repeat(auto-fit,minmax(250px,1fr))]'
  } else if (columns === 2) {
    columnClass = 'grid-cols-1 md:grid-cols-2'
  } else if (columns === 3) {
    columnClass = 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
  } else if (columns === 4) {
    columnClass = 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
  }

  return (
    <div
      className={`
        grid
        ${columnClass}
        ${gapClasses[gap]}
        ${className}
      `.trim()}
    >
      {children}
    </div>
  )
}
