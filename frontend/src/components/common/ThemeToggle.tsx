/**
 * Theme Toggle Component - Icon Only (Compact)
 */

import { Sun, Moon, Monitor } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'
import { cn } from '@/lib/utils'

export default function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()

  const options = [
    { value: 'light' as const, icon: Sun, label: 'Light' },
    { value: 'dark' as const, icon: Moon, label: 'Dark' },
    { value: 'system' as const, icon: Monitor, label: 'System' },
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
