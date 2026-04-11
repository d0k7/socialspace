/**
 * ThemeToggle - Light/Dark Mode Toggle
 *
 * WHY: Single canonical theme control using ThemeContext.
 * System preference is handled automatically by ThemeContext on load.
 * Removed useThemeStore (duplicate system) - canonical is ThemeContext.
 */

import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const options = [
    { value: 'light' as const, icon: Sun, label: 'Light' },
    { value: 'dark' as const, icon: Moon, label: 'Dark' },
  ]

  return (
    <div className="inline-flex w-fit shrink-0 items-center gap-0 p-0.5 bg-gray-100 dark:bg-gray-800 rounded-md">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={cn(
            'flex items-center justify-center w-8 h-8 rounded-sm transition-all',
            theme === value
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          )}
          title={label}
          aria-label={label}
          aria-pressed={theme === value}
        >
          <Icon size={15} />
        </button>
      ))}
    </div>
  )
}
