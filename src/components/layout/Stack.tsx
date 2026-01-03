import { type ReactNode } from 'react'

type StackSpace = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

interface StackProps {
  children: ReactNode
  space?: StackSpace
  dividers?: boolean
  className?: string
}

const spaceClasses: Record<StackSpace, string> = {
  xs: 'gap-1',
  sm: 'gap-2',
  md: 'gap-4',
  lg: 'gap-6',
  xl: 'gap-8',
}

/**
 * Stack - Creates consistent vertical spacing between child elements.
 * Use for form field groups, card content, and any vertical list of elements.
 */
export function Stack({
  children,
  space = 'md',
  dividers = false,
  className = ''
}: StackProps) {
  return (
    <div
      className={`
        flex flex-col
        ${spaceClasses[space]}
        ${dividers ? '[&>*+*]:border-t [&>*+*]:border-[rgb(var(--border))] [&>*+*]:pt-4' : ''}
        ${className}
      `.trim()}
    >
      {children}
    </div>
  )
}
