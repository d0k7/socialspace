/**
 * Platform Statistics Component
 * 
 * Shows detailed stats for a platform
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { 
  TrendingUp, 
  MessageSquare, 
  Users, 
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import { PLATFORM_NAMES, PLATFORM_COLORS, type Platform } from '@/utils/constants'

interface PlatformStatsProps {
  platform: Platform
  stats: {
    totalMessages: number
    unreadMessages: number
    sentMessages: number
    receivedMessages: number
    responseRate: number
    avgResponseTime: string
    trend: 'up' | 'down' | 'neutral'
    trendPercentage: number
  }
}

export default function PlatformStats({ platform, stats }: PlatformStatsProps) {
  const platformColor = PLATFORM_COLORS[platform]

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold shadow-sm"
              style={{ backgroundColor: platformColor }}
            >
              {PLATFORM_NAMES[platform]?.[0]}
            </div>
            <CardTitle>{PLATFORM_NAMES[platform]} Statistics</CardTitle>
          </div>
          <Badge variant={stats.trend === 'up' ? 'success' : stats.trend === 'down' ? 'danger' : 'gray'}>
            {stats.trend === 'up' ? (
              <ArrowUpRight size={14} />
            ) : stats.trend === 'down' ? (
              <ArrowDownRight size={14} />
            ) : null}
            {stats.trendPercentage}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <MessageSquare className="w-6 h-6 text-blue-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.totalMessages}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Total Messages
            </p>
          </div>

          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <Activity className="w-6 h-6 text-orange-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.unreadMessages}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Unread
            </p>
          </div>

          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <TrendingUp className="w-6 h-6 text-green-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.responseRate}%
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Response Rate
            </p>
          </div>

          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <Users className="w-6 h-6 text-purple-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.avgResponseTime}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Avg Response
            </p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Sent:</span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {stats.sentMessages}
            </span>
          </div>
          <div className="flex justify-between text-sm mt-2">
            <span className="text-gray-600 dark:text-gray-400">Received:</span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {stats.receivedMessages}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
