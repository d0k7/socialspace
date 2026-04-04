/**
 * Platforms Page - Complete
 * 
 * Manage all 12 social media platform connections
 */

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import PlatformCard from '@/components/platforms/PlatformCard'
import ConnectionModal from '@/components/platforms/ConnectionModal'
import { usePlatforms, useConnectPlatform, useDisconnectPlatform } from '@/hooks/usePlatforms'
import { PLATFORMS, PLATFORM_NAMES, type Platform } from '@/utils/constants'
import { RefreshCw, Zap, CheckCircle2, XCircle, TrendingUp, AlertCircle } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

interface PlatformState {
  platform: Platform
  isConnected: boolean
  lastSync?: string
  messageCount: number
}

export default function PlatformsPage() {
  const queryClient = useQueryClient()
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null)
  const [showConnectionModal, setShowConnectionModal] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [testingPlatform, setTestingPlatform] = useState<Platform | null>(null)

  // Fetch platforms
  const { data: platforms = [], isLoading } = usePlatforms()
  
  // Mutations
  const connectMutation = useConnectPlatform()
  const disconnectMutation = useDisconnectPlatform()

  // Mock platform states (will be replaced with real API data)
  const [platformStates, setPlatformStates] = useState<PlatformState[]>(
    Object.values(PLATFORMS).map(platform => ({
      platform,
      isConnected: false,
      messageCount: 0,
    }))
  )

  // Calculate stats
  const connectedCount = platformStates.filter(p => p.isConnected).length
  const totalCount = platformStates.length
  const totalMessages = platformStates.reduce((sum, p) => sum + p.messageCount, 0)

  // Handlers
  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await queryClient.invalidateQueries({ queryKey: ['platforms'] })
      toast.success('Platforms refreshed!')
    } catch (error) {
      toast.error('Failed to refresh')
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000)
    }
  }

  const handleConnect = (platform: Platform) => {
    setSelectedPlatform(platform)
    setShowConnectionModal(true)
  }

  const handleConnectionSubmit = async (config: Record<string, string>) => {
    if (!selectedPlatform) return

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Update state
      setPlatformStates(prev =>
        prev.map(p =>
          p.platform === selectedPlatform
            ? { ...p, isConnected: true, lastSync: new Date().toISOString() }
            : p
        )
      )

      toast.success(`${PLATFORM_NAMES[selectedPlatform]} connected successfully!`)
      setShowConnectionModal(false)
      setSelectedPlatform(null)
    } catch (error) {
      toast.error('Failed to connect platform')
    }
  }

  const handleDisconnect = async (platform: Platform) => {
    if (!window.confirm(`Disconnect ${PLATFORM_NAMES[platform]}?`)) return

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Update state
      setPlatformStates(prev =>
        prev.map(p =>
          p.platform === platform
            ? { ...p, isConnected: false, lastSync: undefined, messageCount: 0 }
            : p
        )
      )

      toast.success(`${PLATFORM_NAMES[platform]} disconnected`)
    } catch (error) {
      toast.error('Failed to disconnect')
    }
  }

  const handleTest = async (platform: Platform) => {
    setTestingPlatform(platform)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))

      const platformState = platformStates.find(p => p.platform === platform)
      if (platformState?.isConnected) {
        toast.success(`${PLATFORM_NAMES[platform]} connection is working!`)
      } else {
        toast.error(`${PLATFORM_NAMES[platform]} is not connected`)
      }
    } catch (error) {
      toast.error('Connection test failed')
    } finally {
      setTestingPlatform(null)
    }
  }

  const handleSettings = (platform: Platform) => {
    toast.success(`Opening settings for ${PLATFORM_NAMES[platform]}`)
    // Settings modal will be implemented later
  }

  const handleConnectAll = () => {
    toast.success('Connect all platforms feature coming soon!')
  }

  const handleTestAll = async () => {
    const connectedPlatforms = platformStates.filter(p => p.isConnected)
    
    if (connectedPlatforms.length === 0) {
      toast.error('No platforms connected')
      return
    }

    toast.success(`Testing ${connectedPlatforms.length} platforms...`)
    
    for (const platform of connectedPlatforms) {
      await handleTest(platform.platform)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Platform Connections
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your social media platform integrations
          </p>
        </div>
        <div className="flex items-center gap-3">
          {connectedCount > 0 && (
            <Button
              variant="outline"
              onClick={handleTestAll}
              disabled={testingPlatform !== null}
              className="gap-2"
            >
              <Zap size={16} />
              Test All
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Platforms
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {totalCount}
                </p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <TrendingUp className="text-blue-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Connected
                </p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  {connectedCount}
                </p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <CheckCircle2 className="text-green-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Disconnected
                </p>
                <p className="text-3xl font-bold text-gray-600 mt-2">
                  {totalCount - connectedCount}
                </p>
              </div>
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <XCircle className="text-gray-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Messages
                </p>
                <p className="text-3xl font-bold text-purple-600 mt-2">
                  {totalMessages}
                </p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <TrendingUp className="text-purple-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      {connectedCount === 0 && (
        <Card className="border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="text-5xl">🚀</div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-blue-900 dark:text-blue-100 mb-2">
                  Get Started!
                </h3>
                <p className="text-blue-700 dark:text-blue-300 mb-4">
                  Connect your first platform to start managing your social media from one place.
                </p>
                <Button 
                  variant="primary"
                  onClick={handleConnectAll}
                  className="gap-2"
                >
                  <CheckCircle2 size={16} />
                  Connect Platforms
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Platform Categories */}
      <div className="space-y-6">
        {/* FREE Platforms */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Free Platforms
            </h2>
            <Badge variant="success">Production Ready</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {['telegram', 'discord', 'reddit', 'twitter', 'youtube'].map((platform) => {
              const state = platformStates.find(p => p.platform === platform)
              return (
                <PlatformCard
                  key={platform}
                  platform={platform as Platform}
                  isConnected={state?.isConnected || false}
                  lastSync={state?.lastSync}
                  messageCount={state?.messageCount}
                  onConnect={() => handleConnect(platform as Platform)}
                  onDisconnect={() => handleDisconnect(platform as Platform)}
                  onSettings={() => handleSettings(platform as Platform)}
                  onTest={() => handleTest(platform as Platform)}
                />
              )
            })}
          </div>
        </div>

        {/* Business/Premium Platforms */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Business Platforms
            </h2>
            <Badge variant="warning">API Keys Required</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {['whatsapp', 'instagram', 'facebook', 'linkedin', 'tiktok', 'snapchat', 'pinterest'].map((platform) => {
              const state = platformStates.find(p => p.platform === platform)
              return (
                <PlatformCard
                  key={platform}
                  platform={platform as Platform}
                  isConnected={state?.isConnected || false}
                  lastSync={state?.lastSync}
                  messageCount={state?.messageCount}
                  onConnect={() => handleConnect(platform as Platform)}
                  onDisconnect={() => handleDisconnect(platform as Platform)}
                  onSettings={() => handleSettings(platform as Platform)}
                  onTest={() => handleTest(platform as Platform)}
                />
              )
            })}
          </div>
        </div>
      </div>

      {/* Help Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle size={20} className="text-blue-600" />
            Need Help?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Connection Issues?
              </h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li>• Check your API credentials are correct</li>
                <li>• Ensure your API keys have proper permissions</li>
                <li>• Try disconnecting and reconnecting</li>
                <li>• Use the "Test Connection" feature</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Getting API Keys
              </h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li>• Each platform has a developer portal</li>
                <li>• Create an app/bot on the platform</li>
                <li>• Generate API credentials</li>
                <li>• Copy and paste them here securely</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Connection Modal */}
      {selectedPlatform && (
        <ConnectionModal
          platform={selectedPlatform}
          isOpen={showConnectionModal}
          onClose={() => {
            setShowConnectionModal(false)
            setSelectedPlatform(null)
          }}
          onConnect={handleConnectionSubmit}
          connecting={connectMutation.isPending}
        />
      )}
    </div>
  )
}