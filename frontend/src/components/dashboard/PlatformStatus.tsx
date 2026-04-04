/**
 * Platform Status Component
 * 
 * Shows status of all platforms
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PLATFORMS, PLATFORM_NAMES, PLATFORM_COLORS } from '@/utils/constants'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Platform {
  name: string
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
  messageCount?: number
}

interface PlatformStatusProps {
  platforms?: Platform[]
  loading?: boolean
}

export default function PlatformStatus({ platforms, loading }: PlatformStatusProps) {
  // Mock data if none provided
  const mockPlatforms: Platform[] = Object.values(PLATFORMS).map((platform) => ({
    name: platform,
    status: 'disconnected' as const,
    messageCount: 0,
  }))

  const displayPlatforms = platforms || mockPlatforms

  const getStatusIcon = (status: Platform['status']) => {
    switch (status) {
      case 'connected':
        return <CheckCircle2 size={16} className="text-green-600" />
      case 'error':
        return <XCircle size={16} className="text-red-600" />
      default:
        return <XCircle size={16} className="text-gray-400" />
    }
  }

  const getStatusBadge = (status: Platform['status']) => {
    switch (status) {
      case 'connected':
        return <Badge variant="success">Connected</Badge>
      case 'error':
        return <Badge variant="danger">Error</Badge>
      default:
        return <Badge variant="gray">Disconnected</Badge>
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Platform Status</span>
          {loading && <Loader2 size={20} className="animate-spin text-gray-400" />}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {displayPlatforms.map((platform) => (
            <div
              key={platform.name}
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-sm"
                  style={{ backgroundColor: PLATFORM_COLORS[platform.name] || '#6B7280' }}
                >
                  {PLATFORM_NAMES[platform.name]?.[0] || '?'}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(platform.status)}
                    <span className="font-medium text-gray-900 dark:text-white">
                      {PLATFORM_NAMES[platform.name] || platform.name}
                    </span>
                  </div>
                  {platform.messageCount !== undefined && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {platform.messageCount} messages
                    </p>
                  )}
                </div>
              </div>
              {getStatusBadge(platform.status)}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}