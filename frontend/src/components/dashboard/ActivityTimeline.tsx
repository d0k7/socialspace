/**
 * Activity Timeline Component
 * 
 * Shows recent activity
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Clock, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils'

interface Activity {
  id: string
  type: 'success' | 'error' | 'info'
  platform: string
  message: string
  timestamp: string
}

interface ActivityTimelineProps {
  activities?: Activity[]
  loading?: boolean
}

export default function ActivityTimeline({ activities, loading }: ActivityTimelineProps) {
  // Mock data if none provided
  const mockActivities: Activity[] = [
    {
      id: '1',
      type: 'success',
      platform: 'Setup',
      message: 'Frontend core architecture completed',
      timestamp: new Date().toISOString(),
    },
    {
      id: '2',
      type: 'success',
      platform: 'Backend',
      message: '12 platform integrations ready',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: '3',
      type: 'success',
      platform: 'Testing',
      message: '325 tests passing',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: '4',
      type: 'info',
      platform: 'Development',
      message: 'Session 17 in progress',
      timestamp: new Date().toISOString(),
    },
  ]

  const displayActivities = activities || mockActivities

  const getIcon = (type: Activity['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 size={20} className="text-green-600" />
      case 'error':
        return <AlertCircle size={20} className="text-red-600" />
      default:
        return <Info size={20} className="text-blue-600" />
    }
  }

  const getBgColor = (type: Activity['type']) => {
    switch (type) {
      case 'success':
        return 'bg-green-100 dark:bg-green-900/30'
      case 'error':
        return 'bg-red-100 dark:bg-red-900/30'
      default:
        return 'bg-blue-100 dark:bg-blue-900/30'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-4">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {displayActivities.map((activity, index) => (
              <div key={activity.id} className="flex gap-4 relative">
                {/* Timeline Line */}
                {index < displayActivities.length - 1 && (
                  <div className="absolute left-5 top-12 w-0.5 h-8 bg-gray-200 dark:bg-gray-700" />
                )}
                
                {/* Icon */}
                <div className={cn('p-2 rounded-lg', getBgColor(activity.type))}>
                  {getIcon(activity.type)}
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {activity.platform}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {activity.message}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-2 flex items-center gap-1">
                    <Clock size={12} />
                    {formatDate(new Date(activity.timestamp))}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
