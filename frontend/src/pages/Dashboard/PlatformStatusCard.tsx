/**
 * Platform Status Card Component
 * 
 * Shows platform connection status
 */

import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { PLATFORM_NAMES, PLATFORM_COLORS } from '@/utils/constants'
import type { PlatformConfig } from '@/types/platform.types'
import { Link, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface PlatformStatusCardProps {
  platform: PlatformConfig
  onConnect?: () => void
  onDisconnect?: () => void
}

export default function PlatformStatusCard({
  platform,
  onConnect,
  onDisconnect,
}: PlatformStatusCardProps) {
  const getStatusIcon = () => {
    switch (platform.status) {
      case 'connected':
        return <CheckCircle size={16} className="text-green-600" />
      case 'error':
        return <AlertCircle size={16} className="text-red-600" />
      default:
        return <XCircle size={16} className="text-gray-400" />
    }
  }

  const getStatusBadge = () => {
    switch (platform.status) {
      case 'connected':
        return <Badge variant="success">Connected</Badge>
      case 'error':
        return <Badge variant="danger">Error</Badge>
      default:
        return <Badge variant="gray">Disconnected</Badge>
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border-2 border-gray-200 dark:border-gray-700 p-4 hover:border-blue-500 dark:hover:border-blue-500 transition-colors group">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold"
            style={{ backgroundColor: PLATFORM_COLORS[platform.platform] || '#6B7280' }}
          >
            {PLATFORM_NAMES[platform.platform]?.[0] || '?'}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {platform.displayName || PLATFORM_NAMES[platform.platform]}
            </h3>
            <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 mt-1">
              {getStatusIcon()}
              <span>{platform.status}</span>
            </div>
          </div>
        </div>
        {getStatusBadge()}
      </div>

      {platform.isConnected && (
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Messages</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {platform.messageCount || 0}
            </span>
          </div>
          {platform.lastSync && (
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Last sync: {new Date(platform.lastSync).toLocaleDateString()}
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2">
        {platform.isConnected ? (
          <>
            <Button variant="outline" size="sm" className="flex-1">
              <Link size={14} />
              Settings
            </Button>
            <Button
              variant="danger"
              size="sm"
              className="flex-1"
              onClick={onDisconnect}
            >
              Disconnect
            </Button>
          </>
        ) : (
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            onClick={onConnect}
          >
            Connect
          </Button>
        )}
      </div>
    </div>
  )
}
