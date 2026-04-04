/**
 * Stats Card Component
 * 
 * Reusable stats display card
 */

import { Card, CardContent } from '@/components/ui/Card'
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatsCardProps {
  title: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  icon: LucideIcon
  color?: string
  bgColor?: string
  loading?: boolean
}

export default function StatsCard({
  title,
  value,
  change,
  trend = 'neutral',
  icon: Icon,
  color = 'text-blue-600',
  bgColor = 'bg-blue-100 dark:bg-blue-900/30',
  loading,
}: StatsCardProps) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus

  return (
    <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer hover:scale-[1.02]">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            {loading ? (
              <div className="h-9 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mt-2" />
            ) : (
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {value}
              </p>
            )}
            {change && !loading && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-1">
                <TrendIcon
                  size={16}
                  className={cn(
                    trend === 'up' && 'text-green-600',
                    trend === 'down' && 'text-red-600',
                    trend === 'neutral' && 'text-gray-600'
                  )}
                />
                {change}
              </p>
            )}
          </div>
          <div className={cn('p-3 rounded-xl', bgColor)}>
            <Icon className={color} size={24} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}