/**
 * Platform Card Component
 * 
 * Individual platform connection card
 */

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { 
  CheckCircle2, 
  XCircle, 
  Settings, 
  MoreVertical,
  Zap,
  TrendingUp,
} from 'lucide-react'
import { PLATFORM_NAMES, PLATFORM_COLORS, type Platform } from '@/utils/constants'
import { cn } from '@/lib/utils'

interface PlatformCardProps {
  platform: Platform
  isConnected: boolean
  lastSync?: string
  messageCount?: number
  onConnect?: () => void
  onDisconnect?: () => void
  onSettings?: () => void
  onTest?: () => void
}

export default function PlatformCard({
  platform,
  isConnected,
  lastSync,
  messageCount = 0,
  onConnect,
  onDisconnect,
  onSettings,
  onTest,
}: PlatformCardProps) {
  const [showMenu, setShowMenu] = useState(false)

  const platformColor = PLATFORM_COLORS[platform] || '#6B7280'

  return (
    <Card 
      className={cn(
        'hover:shadow-lg transition-all duration-300 hover:scale-[1.02]',
        isConnected && 'border-2 border-green-200 dark:border-green-800'
      )}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            {/* Platform Icon */}
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center text-white font-bold text-2xl shadow-lg"
              style={{ backgroundColor: platformColor }}
            >
              {PLATFORM_NAMES[platform]?.[0] || '?'}
            </div>

            {/* Platform Info */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <CardTitle className="text-xl">
                  {PLATFORM_NAMES[platform]}
                </CardTitle>
                {isConnected ? (
                  <Badge variant="success" className="gap-1">
                    <CheckCircle2 size={12} />
                    Connected
                  </Badge>
                ) : (
                  <Badge variant="gray" className="gap-1">
                    <XCircle size={12} />
                    Disconnected
                  </Badge>
                )}
              </div>
              
              {isConnected && (
                <div className="space-y-1">
                  {lastSync && (
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Last sync: {new Date(lastSync).toLocaleString()}
                    </p>
                  )}
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {messageCount} messages
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Menu */}
          {isConnected && (
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <MoreVertical size={20} className="text-gray-400" />
              </button>

              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-20">
                    <button
                      onClick={() => {
                        onTest?.()
                        setShowMenu(false)
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <Zap size={16} />
                      Test Connection
                    </button>
                    <button
                      onClick={() => {
                        onSettings?.()
                        setShowMenu(false)
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <Settings size={16} />
                      Settings
                    </button>
                    <hr className="my-1 border-gray-200 dark:border-gray-700" />
                    <button
                      onClick={() => {
                        onDisconnect?.()
                        setShowMenu(false)
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <XCircle size={16} />
                      Disconnect
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {isConnected ? (
          <div className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {messageCount}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Messages
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  <TrendingUp size={24} className="inline" />
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Active
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onSettings}
                className="flex-1 gap-2"
              >
                <Settings size={16} />
                Settings
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onTest}
                className="flex-1 gap-2"
              >
                <Zap size={16} />
                Test
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Connect your {PLATFORM_NAMES[platform]} account to start managing messages
            </p>
            <Button
              variant="primary"
              onClick={onConnect}
              className="w-full"
              style={{ backgroundColor: platformColor }}
            >
              Connect {PLATFORM_NAMES[platform]}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}