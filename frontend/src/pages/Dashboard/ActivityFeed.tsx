/**
 * Activity Feed Component
 * 
 * Shows recent activity timeline
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Clock, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { cn } from '@/lib/utils'

interface Activity {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  platform?: string
  message: string
  timestamp: string
}

interface ActivityFeedProps {
  activities?: Activity[]
  maxItems?: number
}

export default function ActivityFeed({ activities = [], maxItems = 10 }: ActivityFeedProps) {
  const getIcon = (type: Activity['type']) => {
    switch (type) {
      case 'success':
        return CheckCircle2
      case 'error':
        return AlertCircle
      case 'info':
        return Info
      case 'warning':
        return AlertCircle
      default:
        return Info
    }
  }

  const getIconColor = (type: Activity['type']) => {
    switch (type) {
      case 'success':
        return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30'
      case 'error':
        return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30'
      case 'warning':
        return 'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30'
      default:
        return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30'
    }
  }

  const displayActivities = activities.slice(0, maxItems)

  if (displayActivities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No recent activity
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayActivities.map((activity) => {
            const Icon = getIcon(activity.type)
            return (
              <div
                key={activity.id}
                className={cn(
                  'flex items-start gap-4 p-4 rounded-lg transition-colors',
                  'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
              >
                <div className={cn('p-2 rounded-lg', getIconColor(activity.type))}>
                  <Icon size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  {activity.platform && (
                    <Badge variant="gray" className="mb-2">
                      {activity.platform}
                    </Badge>
                  )}
                  <p className="text-sm text-gray-900 dark:text-white">
                    {activity.message}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-1">
                    <Clock size={12} />
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
