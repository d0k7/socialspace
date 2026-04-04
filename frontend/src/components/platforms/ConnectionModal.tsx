/**
 * Connection Modal Component
 * 
 * Modal for connecting a platform with API keys
 */

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { X, Eye, EyeOff, ExternalLink, CheckCircle2 } from 'lucide-react'
import { PLATFORM_NAMES, PLATFORM_COLORS, type Platform } from '@/utils/constants'
import toast from 'react-hot-toast'

interface ConnectionModalProps {
  platform: Platform
  isOpen: boolean
  onClose: () => void
  onConnect: (config: Record<string, string>) => void
  connecting?: boolean
}

export default function ConnectionModal({
  platform,
  isOpen,
  onClose,
  onConnect,
  connecting,
}: ConnectionModalProps) {
  const [showToken, setShowToken] = useState(false)
  const [formData, setFormData] = useState<Record<string, string>>({})

  if (!isOpen) return null

  const platformColor = PLATFORM_COLORS[platform]

  // Platform-specific configuration fields
  const getConfigFields = (): Array<{
    key: string
    label: string
    placeholder: string
    type: 'text' | 'password'
    required: boolean
    helpText?: string
  }> => {
    switch (platform) {
      case 'telegram':
        return [
          {
            key: 'bot_token',
            label: 'Bot Token',
            placeholder: '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz',
            type: 'password',
            required: true,
            helpText: 'Get your bot token from @BotFather',
          },
        ]
      
      case 'discord':
        return [
          {
            key: 'bot_token',
            label: 'Bot Token',
            placeholder: 'Your Discord bot token',
            type: 'password',
            required: true,
            helpText: 'Create a bot at discord.com/developers',
          },
        ]
      
      case 'twitter':
        return [
          {
            key: 'api_key',
            label: 'API Key',
            placeholder: 'Your Twitter API key',
            type: 'password',
            required: true,
          },
          {
            key: 'api_secret',
            label: 'API Secret',
            placeholder: 'Your Twitter API secret',
            type: 'password',
            required: true,
          },
          {
            key: 'access_token',
            label: 'Access Token',
            placeholder: 'Your access token',
            type: 'password',
            required: true,
          },
          {
            key: 'access_token_secret',
            label: 'Access Token Secret',
            placeholder: 'Your access token secret',
            type: 'password',
            required: true,
          },
        ]
      
      case 'reddit':
        return [
          {
            key: 'client_id',
            label: 'Client ID',
            placeholder: 'Your Reddit client ID',
            type: 'text',
            required: true,
          },
          {
            key: 'client_secret',
            label: 'Client Secret',
            placeholder: 'Your Reddit client secret',
            type: 'password',
            required: true,
          },
          {
            key: 'username',
            label: 'Username',
            placeholder: 'Your Reddit username',
            type: 'text',
            required: true,
          },
          {
            key: 'password',
            label: 'Password',
            placeholder: 'Your Reddit password',
            type: 'password',
            required: true,
          },
        ]
      
      case 'youtube':
        return [
          {
            key: 'api_key',
            label: 'API Key',
            placeholder: 'Your YouTube Data API key',
            type: 'password',
            required: true,
            helpText: 'Get API key from Google Cloud Console',
          },
        ]
      
      default:
        return [
          {
            key: 'api_key',
            label: 'API Key',
            placeholder: `Your ${PLATFORM_NAMES[platform]} API key`,
            type: 'password',
            required: true,
          },
          {
            key: 'access_token',
            label: 'Access Token',
            placeholder: `Your access token`,
            type: 'password',
            required: false,
          },
        ]
    }
  }

  const configFields = getConfigFields()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validate required fields
    const missingFields = configFields
      .filter(field => field.required && !formData[field.key])
      .map(field => field.label)

    if (missingFields.length > 0) {
      toast.error(`Please fill in: ${missingFields.join(', ')}`)
      return
    }

    onConnect(formData)
  }

  const handleInputChange = (key: string, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div
                  className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-lg"
                  style={{ backgroundColor: platformColor }}
                >
                  {PLATFORM_NAMES[platform]?.[0]}
                </div>
                <div>
                  <CardTitle className="text-xl">
                    Connect {PLATFORM_NAMES[platform]}
                  </CardTitle>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Enter your API credentials to connect
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <X size={20} />
              </button>
            </div>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Instructions */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" size={20} />
                  <div className="flex-1">
                    <p className="text-sm text-blue-800 dark:text-blue-300 font-medium mb-2">
                      How to get your credentials:
                    </p>
                    <ol className="text-sm text-blue-700 dark:text-blue-300 space-y-1 list-decimal list-inside">
                      {getPlatformInstructions(platform).map((instruction, index) => (
                        <li key={index}>{instruction}</li>
                      ))}
                    </ol>
                    {getPlatformDocLink(platform) && (
                      <a
                        href={getPlatformDocLink(platform)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline mt-2"
                      >
                        Read documentation
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                </div>
              </div>

              {/* Config Fields */}
              {configFields.map((field) => (
                <div key={field.key}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {field.label}
                    {field.required && <span className="text-red-600">*</span>}
                  </label>
                  <div className="relative">
                    <input
                      type={field.type === 'password' && !showToken ? 'password' : 'text'}
                      value={formData[field.key] || ''}
                      onChange={(e) => handleInputChange(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white pr-12"
                      required={field.required}
                    />
                    {field.type === 'password' && (
                      <button
                        type="button"
                        onClick={() => setShowToken(!showToken)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        {showToken ? <EyeOff size={20} /> : <Eye size={20} />}
                      </button>
                    )}
                  </div>
                  {field.helpText && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {field.helpText}
                    </p>
                  )}
                </div>
              ))}

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  className="flex-1"
                  disabled={connecting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  loading={connecting}
                  style={{ backgroundColor: platformColor }}
                >
                  Connect
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Helper functions
function getPlatformInstructions(platform: Platform): string[] {
  switch (platform) {
    case 'telegram':
      return [
        'Open Telegram and search for @BotFather',
        'Send /newbot and follow instructions',
        'Copy the bot token provided',
      ]
    
    case 'discord':
      return [
        'Go to discord.com/developers/applications',
        'Create a new application',
        'Go to Bot section and create a bot',
        'Copy the bot token',
      ]
    
    case 'twitter':
      return [
        'Go to developer.twitter.com',
        'Create a new app',
        'Generate API keys and tokens',
        'Copy all credentials',
      ]
    
    case 'reddit':
      return [
        'Go to reddit.com/prefs/apps',
        'Create a new app (script type)',
        'Copy client ID and secret',
        'Use your Reddit username and password',
      ]
    
    case 'youtube':
      return [
        'Go to Google Cloud Console',
        'Enable YouTube Data API v3',
        'Create credentials (API key)',
        'Copy the API key',
      ]
    
    default:
      return [
        `Go to ${PLATFORM_NAMES[platform]} developer portal`,
        'Create or access your app',
        'Generate API credentials',
        'Copy the required tokens',
      ]
  }
}

function getPlatformDocLink(platform: Platform): string {
  const links: Record<Platform, string> = {
    telegram: 'https://core.telegram.org/bots',
    discord: 'https://discord.com/developers/docs',
    twitter: 'https://developer.twitter.com/en/docs',
    reddit: 'https://www.reddit.com/dev/api',
    youtube: 'https://developers.google.com/youtube/v3',
    whatsapp: 'https://developers.facebook.com/docs/whatsapp',
    instagram: 'https://developers.facebook.com/docs/instagram',
    facebook: 'https://developers.facebook.com/docs',
    linkedin: 'https://docs.microsoft.com/en-us/linkedin',
    tiktok: 'https://developers.tiktok.com',
    snapchat: 'https://developers.snap.com',
    pinterest: 'https://developers.pinterest.com',
  }
  
  return links[platform] || ''
}
