import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

type BadgeVariant = 'default' | 'success' | 'gray' | 'warning' | 'danger'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

const variants: Record<BadgeVariant, string> = {
  default:
    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  success:
    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  gray: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  warning:
    'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  danger: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
}

export function Badge({
  className,
  variant = 'default',
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold capitalize',
        variants[variant],
        className
      )}
      {...props}
    />
  )
}
