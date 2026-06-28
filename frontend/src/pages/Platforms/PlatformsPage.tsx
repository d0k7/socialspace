/**
 * Platforms Page -- Real Connection Status
 * =========================================
 * Rewritten: Phase 4, Session 4.2
 * Updated:   Phase 4, Session 4.4 -- Reddit OAuth 2.0 added
 *
 * WHY this was rewritten (Session 4.2):
 * Previous version used a local platformStates useState array initialised with
 * isConnected: false for all 12 platforms. Clicking Connect/Disconnect ran
 * fake setTimeout calls -- nothing was written to or read from the database.
 * A real user (or interviewer) could not connect any platform from this page.
 *
 * Session 4.4 additions:
 * - Reddit added to LIVE_PLATFORMS (OAuth 2.0 Authorization Code flow)
 * - getRedditStatus useQuery added (reads real PlatformConnection rows)
 * - Reddit OAuth callback params (reddit_connected, reddit_error) handled
 *   in the existing mount effect alongside Twitter params
 * - handleConnect Reddit case: browser redirect to /api/reddit/authorize
 * - disconnectMutation Reddit case: calls disconnectReddit()
 * - isPlatformConnected, connectedCount, handleTest, handleTestAll,
 *   handleRefresh all updated to include reddit
 */

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import PlatformCard from '@/components/platforms/PlatformCard'
import ConnectionModal from '@/components/platforms/ConnectionModal'
import {
  getTelegramStatus,
  getDiscordStatus,
  getTwitterStatus,
  getRedditStatus,
  connectTelegram,
  connectDiscord,
  disconnectTelegram,
  disconnectDiscord,
  disconnectTwitter,
  disconnectReddit,
} from '@/api/endpoints/platformStatus'
import apiClient from '@/api/client'
import { PLATFORMS, PLATFORM_NAMES, type Platform } from '@/utils/constants'
import {
  RefreshCw,
  Zap,
  CheckCircle2,
  XCircle,
  TrendingUp,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'

// ============================================================================
// CONSTANTS
// ============================================================================

/**
 * Stable React Query cache keys for each platform's status query.
 * WHY array format: Allows React Query's partial-match invalidation.
 * queryClient.invalidateQueries({ queryKey: ['platform-status'] }) would
 * invalidate all at once if needed. Individual invalidation uses the full key.
 */
const STATUS_KEYS = {
  telegram: ['platform-status', 'telegram'] as const,
  discord: ['platform-status', 'discord'] as const,
  twitter: ['platform-status', 'twitter'] as const,
  reddit: ['platform-status', 'reddit'] as const,
}

/**
 * The set of platforms that have real backend integration today.
 * WHY a Set: O(1) lookup in isPlatformConnected and handleConnect guards.
 * Anything not in this set shows "coming soon" when the user tries to connect.
 *
 * Reddit added Session 4.4: reddit.py OAuth 2.0 router is live.
 * Credentials pending Reddit API approval -- connect will show a 503 until
 * REDDIT_CLIENT_ID is in .env. The flow is wired end-to-end on our side.
 */
const LIVE_PLATFORMS = new Set<Platform>(['telegram', 'discord', 'twitter', 'reddit'])

// ============================================================================
// COMPONENT
// ============================================================================

export default function PlatformsPage() {
  const queryClient = useQueryClient()

  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null)
  const [showConnectionModal, setShowConnectionModal] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [testingPlatform, setTestingPlatform] = useState<Platform | null>(null)

  // ==========================================================================
  // OAUTH CALLBACK HANDLER
  //
  // WHY on mount with empty deps (not useSearchParams):
  // Twitter and Reddit OAuth flows complete on the backend, which redirects the
  // browser to /platforms?{platform}_connected=true or ?{platform}_error=...
  // We read these params exactly once on mount then remove them from the URL.
  //
  // WHY window.location.search not useSearchParams:
  // If we used useSearchParams as a dep, calling setSearchParams({}) inside the
  // effect would trigger a re-run, requiring an additional guard variable.
  // Reading window.location.search directly + window.history.replaceState
  // is atomic and avoids the loop entirely.
  //
  // WHY one effect for both Twitter and Reddit (not two):
  // Both platforms land on the same page (/platforms) and both need URL cleanup
  // via replaceState. Two separate effects would each call replaceState, but
  // both must run before the first replaceState wipes the params the other
  // effect needs. One effect reads all OAuth params atomically.
  // ==========================================================================
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const twitterConnected = params.get('twitter_connected')
    const twitterError = params.get('twitter_error')
    const redditConnected = params.get('reddit_connected')
    const redditError = params.get('reddit_error')

    // Nothing OAuth-related in URL -- bail out immediately
    const hasOAuthParams = twitterConnected || twitterError || redditConnected || redditError
    if (!hasOAuthParams) return

    // -- Twitter --
    if (twitterConnected === 'true') {
      const username = params.get('username')
      toast.success(
        username
          ? `Twitter connected as @${username}!`
          : 'Twitter connected successfully!'
      )
      // Invalidate Twitter status so the card refreshes without a manual refresh
      queryClient.invalidateQueries({ queryKey: STATUS_KEYS.twitter })
    } else if (twitterError) {
      // Map backend error codes to user-readable messages
      const twitterErrorMessages: Record<string, string> = {
        missing_params: 'Twitter auth failed: missing OAuth parameters. Please try again.',
        invalid_state:
          'Twitter auth failed: state mismatch. This may be a CSRF attempt or the session expired.',
        token_exchange_failed:
          'Twitter auth failed: could not exchange the authorization code for a token.',
        user_fetch_failed: 'Twitter auth failed: could not fetch your Twitter profile.',
        timeout: 'Twitter auth timed out. Please try again.',
        network_error:
          'Network error during Twitter auth. Check your connection and try again.',
        db_error: 'Database error during Twitter auth. Please try again.',
      }
      toast.error(
        twitterErrorMessages[twitterError] || `Twitter auth failed: ${twitterError}`
      )
    }

    // -- Reddit --
    if (redditConnected === 'true') {
      toast.success('Reddit connected! You can now post to subreddits.')
      // Invalidate Reddit status so the card immediately shows Connected
      queryClient.invalidateQueries({ queryKey: STATUS_KEYS.reddit })
    } else if (redditError) {
      const redditErrorMessages: Record<string, string> = {
        access_denied:
          'Reddit connection cancelled. You declined the authorization request.',
        invalid_state:
          'Reddit auth failed: state mismatch. This may be a CSRF attempt or the session expired.',
        token_exchange_failed:
          'Reddit auth failed: could not exchange the authorization code. Please try again.',
        identity_fetch_failed:
          'Reddit auth failed: could not fetch your Reddit profile. Please try again.',
        no_code: 'Reddit auth failed: no authorization code received. Please try again.',
        network_error:
          'Network error during Reddit auth. Check your connection and try again.',
      }
      toast.error(
        redditErrorMessages[redditError] || `Reddit auth failed: ${redditError}`
      )
    }

    // Remove all OAuth params from URL without triggering a page reload.
    // WHY replaceState not pushState: We do not want a "blank" history entry
    // that the user can navigate back to, which would re-trigger the effect.
    window.history.replaceState({}, '', window.location.pathname)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  // WHY empty deps: intentional -- this effect must run exactly once on mount
  // to consume the OAuth redirect parameters from Twitter and Reddit.

  // ==========================================================================
  // STATUS QUERIES
  //
  // WHY staleTime 30_000 (30 seconds):
  // Platform connection status rarely changes mid-session. 30s reduces backend
  // load for users who quickly navigate away and back while keeping the UI
  // fresh enough for interactive use. After any connect/disconnect mutation,
  // we explicitly invalidate the relevant key so the next render always gets
  // fresh data regardless of staleTime.
  //
  // WHY retry: false:
  // A 401 from the status endpoint means the user's session is invalid.
  // The axios interceptor handles token refresh transparently before React Query
  // sees the error. If the interceptor fails to refresh, it redirects to login --
  // retrying the status query at that point is wasteful and confusing.
  // ==========================================================================
  const {
    data: telegramStatus,
    isLoading: telegramLoading,
    refetch: refetchTelegram,
  } = useQuery({
    queryKey: STATUS_KEYS.telegram,
    queryFn: getTelegramStatus,
    staleTime: 30_000,
    retry: false,
  })

  const {
    data: discordStatus,
    isLoading: discordLoading,
    refetch: refetchDiscord,
  } = useQuery({
    queryKey: STATUS_KEYS.discord,
    queryFn: getDiscordStatus,
    staleTime: 30_000,
    retry: false,
  })

  const {
    data: twitterStatus,
    isLoading: twitterLoading,
    refetch: refetchTwitter,
  } = useQuery({
    queryKey: STATUS_KEYS.twitter,
    queryFn: getTwitterStatus,
    staleTime: 30_000,
    retry: false,
  })

  const {
    data: redditStatus,
    isLoading: redditLoading,
    refetch: refetchReddit,
  } = useQuery({
    queryKey: STATUS_KEYS.reddit,
    queryFn: getRedditStatus,
    staleTime: 30_000,
    retry: false,
  })

  /** True while any of the 4 initial status fetches are in-flight */
  const isLoadingAny = telegramLoading || discordLoading || twitterLoading || redditLoading

  // ==========================================================================
  // CONNECT MUTATIONS
  //
  // WHY separate mutations for Telegram and Discord (not one generic mutation):
  // Each platform has a different request body shape, a different success
  // message, and invalidates a different cache key. A single generic mutation
  // would require branching inside mutationFn and make onSuccess/onError
  // handlers ambiguous about which platform just connected.
  //
  // WHY Twitter and Reddit connect are NOT mutations:
  // Both use OAuth browser redirect flows -- window.location.href navigation
  // to the backend authorize endpoint. Fetch-based mutations cannot initiate
  // a proper OAuth browser redirect chain.
  // ==========================================================================
  const connectTelegramMutation = useMutation({
    mutationFn: ({ chatId, chatName }: { chatId: string; chatName?: string }) =>
      connectTelegram(chatId, chatName),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: STATUS_KEYS.telegram })
      toast.success(`Telegram connected to ${data.chat_name}!`)
      setShowConnectionModal(false)
      setSelectedPlatform(null)
    },
    onError: (error: Error) => {
      // WHY extract response.data.detail:
      // FastAPI returns error detail in error.response.data.detail.
      // The generic error.message is axios's "Request failed with status code 400"
      // which gives the user no actionable information.
      const detail = (
        error as unknown as { response?: { data?: { detail?: string } } }
      )?.response?.data?.detail
      toast.error(
        detail ||
          'Failed to connect Telegram. Make sure you have messaged @socialspace_agent_bot first.'
      )
    },
  })

  const connectDiscordMutation = useMutation({
    mutationFn: ({
      channelId,
      channelName,
    }: {
      channelId: string
      channelName?: string
    }) => connectDiscord(channelId, channelName),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: STATUS_KEYS.discord })
      toast.success(`Discord connected to #${data.channel_name}!`)
      setShowConnectionModal(false)
      setSelectedPlatform(null)
    },
    onError: (error: Error) => {
      const detail = (
        error as unknown as { response?: { data?: { detail?: string } } }
      )?.response?.data?.detail
      toast.error(
        detail ||
          'Failed to connect Discord. Make sure the SocialSpace bot is in your server.'
      )
    },
  })

  // ==========================================================================
  // DISCONNECT MUTATION
  //
  // WHY a single mutation routes by platform (instead of 4 separate mutations):
  // Disconnect is structurally identical for all live platforms -- soft delete,
  // clear tokens. The callsite becomes: disconnectMutation.mutate(platform).
  // The branching lives in mutationFn, keeping the handlers clean.
  // ==========================================================================
  const disconnectMutation = useMutation({
    mutationFn: (platform: Platform) => {
      switch (platform) {
        case 'telegram':
          return disconnectTelegram()
        case 'discord':
          return disconnectDiscord()
        case 'twitter':
          return disconnectTwitter()
        case 'reddit':
          return disconnectReddit()
        default:
          // Defensive: business platforms cannot be disconnected until integrated
          return Promise.reject(
            new Error(`Disconnect not yet implemented for ${platform}`)
          )
      }
    },
    onSuccess: (_, platform) => {
      // Invalidate only the disconnected platform's cache key.
      // The others stay cached -- their status did not change.
      const key = STATUS_KEYS[platform as keyof typeof STATUS_KEYS]
      if (key) {
        queryClient.invalidateQueries({ queryKey: key })
      }
      toast.success(`${PLATFORM_NAMES[platform]} disconnected`)
    },
    onError: (error: Error, platform) => {
      const detail = (
        error as unknown as { response?: { data?: { detail?: string } } }
      )?.response?.data?.detail
      toast.error(detail || `Failed to disconnect ${PLATFORM_NAMES[platform]}`)
    },
  })

  // ==========================================================================
  // DERIVED STATE HELPERS
  // ==========================================================================

  /**
   * Returns true if the given platform has an active DB connection.
   * For business platforms (not yet integrated), always returns false.
   * For Reddit: returns true once reddit.py OAuth flow completes and
   * REDDIT_CLIENT_ID credentials are approved and in .env.
   */
  const isPlatformConnected = (platform: Platform): boolean => {
    switch (platform) {
      case 'telegram':
        return telegramStatus?.connected ?? false
      case 'discord':
        return discordStatus?.connected ?? false
      case 'twitter':
        return twitterStatus?.connected ?? false
      case 'reddit':
        return redditStatus?.connected ?? false
      default:
        return false
    }
  }

  // Real connected count -- only counts platforms with live backend integration
  const connectedCount = (
    ['telegram', 'discord', 'twitter', 'reddit'] as Platform[]
  ).filter(isPlatformConnected).length

  // Total number of platforms the product supports (all 12, including future ones)
  const totalCount = Object.values(PLATFORMS).length

  // Whether any connect mutation is currently in-flight (for modal loading state)
  const isConnecting =
    connectTelegramMutation.isPending || connectDiscordMutation.isPending

  // ==========================================================================
  // HANDLERS
  // ==========================================================================

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      // Parallel refetch -- all 4 fire simultaneously
      await Promise.all([
        refetchTelegram(),
        refetchDiscord(),
        refetchTwitter(),
        refetchReddit(),
      ])
      toast.success('Platform status refreshed')
    } catch {
      toast.error('Failed to refresh platform status')
    } finally {
      // Brief delay so the spinner is visible even on fast connections
      setTimeout(() => setIsRefreshing(false), 500)
    }
  }

  const handleConnect = (platform: Platform) => {
    if (platform === 'twitter') {
      // WHY window.location.href not a mutation:
      // Twitter PKCE flow = backend generates state+verifier, stores server-side,
      // returns 302 redirect to Twitter's auth URL. This is browser navigation,
      // not a fetch. The redirect chain only works as a real navigation, not via
      // fetch (which would follow the 302 internally and receive Twitter's HTML).
      const apiBase = (
        apiClient.defaults.baseURL || 'http://localhost:8000'
      ).replace(/\/$/, '')
      window.location.href = `${apiBase}/api/auth/twitter/authorize`
      return
    }

    if (platform === 'reddit') {
      // WHY window.location.href not a mutation:
      // Reddit Authorization Code flow = backend generates CSRF state, stores
      // server-side, returns 302 redirect to Reddit's consent page. Same pattern
      // as Twitter -- must be real browser navigation, not a fetch call.
      // If REDDIT_CLIENT_ID is not yet in .env, the backend returns HTTP 503
      // before the redirect -- the browser shows an error page. This is correct
      // behaviour until the Reddit API application is approved.
      const apiBase = (
        apiClient.defaults.baseURL || 'http://localhost:8000'
      ).replace(/\/$/, '')
      window.location.href = `${apiBase}/api/reddit/authorize`
      return
    }

    if (!LIVE_PLATFORMS.has(platform)) {
      // Business platforms and non-integrated free platforms
      toast.error(`${PLATFORM_NAMES[platform]} integration coming soon!`)
      return
    }

    setSelectedPlatform(platform)
    setShowConnectionModal(true)
  }

  const handleConnectionSubmit = (config: Record<string, string>) => {
    if (!selectedPlatform) return

    if (selectedPlatform === 'telegram') {
      const chatId = config.chat_id?.trim()
      if (!chatId) {
        toast.error('Chat ID is required')
        return
      }
      // Pass chat_name if the user filled it in -- optional field
      connectTelegramMutation.mutate({
        chatId,
        chatName: config.chat_name?.trim() || undefined,
      })
    } else if (selectedPlatform === 'discord') {
      const channelId = config.channel_id?.trim()
      if (!channelId) {
        toast.error('Channel ID is required')
        return
      }
      connectDiscordMutation.mutate({
        channelId,
        channelName: config.channel_name?.trim() || undefined,
      })
    }
  }

  const handleDisconnect = async (platform: Platform) => {
    if (!isPlatformConnected(platform)) {
      toast.error(`${PLATFORM_NAMES[platform]} is not connected`)
      return
    }
    if (
      !window.confirm(
        `Disconnect ${PLATFORM_NAMES[platform]}? Posts to this platform will stop.`
      )
    ) {
      return
    }
    disconnectMutation.mutate(platform)
  }

  const handleTest = async (platform: Platform) => {
    if (!LIVE_PLATFORMS.has(platform)) {
      toast.error(`${PLATFORM_NAMES[platform]} integration not yet available`)
      return
    }

    setTestingPlatform(platform)
    try {
      let connected = false
      // WHY fresh API call not cached status:
      // handleTest is the user explicitly asking "is this working RIGHT NOW?"
      // The React Query cache may be up to 30s stale. A fresh call gives a
      // definitive answer at the exact moment of testing.
      switch (platform) {
        case 'telegram': {
          const result = await getTelegramStatus()
          connected = result.connected
          break
        }
        case 'discord': {
          const result = await getDiscordStatus()
          connected = result.connected
          break
        }
        case 'twitter': {
          const result = await getTwitterStatus()
          connected = result.connected
          break
        }
        case 'reddit': {
          const result = await getRedditStatus()
          connected = result.connected
          break
        }
      }

      if (connected) {
        toast.success(`${PLATFORM_NAMES[platform]} is connected and responding`)
      } else {
        toast.error(`${PLATFORM_NAMES[platform]} is not connected`)
      }
    } catch {
      toast.error(`${PLATFORM_NAMES[platform]} connection test failed`)
    } finally {
      setTestingPlatform(null)
    }
  }

  const handleTestAll = async () => {
    const connectedPlatforms = (
      ['telegram', 'discord', 'twitter', 'reddit'] as Platform[]
    ).filter(isPlatformConnected)

    if (connectedPlatforms.length === 0) {
      toast.error('No platforms connected to test')
      return
    }

    toast.success(
      `Testing ${connectedPlatforms.length} platform${connectedPlatforms.length > 1 ? 's' : ''}...`
    )
    // Sequential -- wait for each test before starting the next so toasts are readable
    for (const platform of connectedPlatforms) {
      await handleTest(platform)
    }
  }

  const handleSettings = (platform: Platform) => {
    toast.success(`Settings for ${PLATFORM_NAMES[platform]} coming soon`)
  }

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ------------------------------------------------------------------ */}
      {/* Header */}
      {/* ------------------------------------------------------------------ */}
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
              disabled={testingPlatform !== null || isLoadingAny}
              className="gap-2"
            >
              <Zap size={16} />
              Test All
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoadingAny}
            className="gap-2"
          >
            <RefreshCw
              size={16}
              className={isRefreshing || isLoadingAny ? 'animate-spin' : ''}
            />
            Refresh
          </Button>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Stats Overview */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Supported Platforms -- static count of all 12 product platforms */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Supported Platforms
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

        {/* Connected -- real count from DB */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Connected
                </p>
                {isLoadingAny ? (
                  <Loader2
                    className="animate-spin text-green-600 mt-3"
                    size={28}
                  />
                ) : (
                  <p className="text-3xl font-bold text-green-600 mt-2">
                    {connectedCount}
                  </p>
                )}
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <CheckCircle2 className="text-green-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Disconnected -- total minus real connected count */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Disconnected
                </p>
                {isLoadingAny ? (
                  <Loader2
                    className="animate-spin text-gray-500 mt-3"
                    size={28}
                  />
                ) : (
                  <p className="text-3xl font-bold text-gray-600 mt-2">
                    {totalCount - connectedCount}
                  </p>
                )}
              </div>
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <XCircle className="text-gray-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Live Integrations -- static count of platforms with real backend code */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Live Integrations
                </p>
                <p className="text-3xl font-bold text-purple-600 mt-2">
                  {LIVE_PLATFORMS.size}
                </p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <TrendingUp className="text-purple-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Quick Start Banner -- shown only when nothing is connected */}
      {/* ------------------------------------------------------------------ */}
      {!isLoadingAny && connectedCount === 0 && (
        <Card className="border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="text-5xl">🚀</div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-blue-900 dark:text-blue-100 mb-2">
                  Get Started
                </h3>
                <p className="text-blue-700 dark:text-blue-300 mb-4">
                  Connect Telegram or Discord to start posting from SocialSpace.
                  Both are free with no paid API tier required.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="primary"
                    onClick={() => handleConnect('telegram')}
                    className="gap-2"
                  >
                    <CheckCircle2 size={16} />
                    Connect Telegram
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleConnect('discord')}
                    className="gap-2"
                  >
                    <CheckCircle2 size={16} />
                    Connect Discord
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Platform Categories */}
      {/* ------------------------------------------------------------------ */}
      <div className="space-y-6">
        {/* FREE Platforms -- Telegram/Discord/Twitter/Reddit have live integration */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Free Platforms
            </h2>
            <Badge variant="success">Production Ready</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(
              ['telegram', 'discord', 'reddit', 'twitter', 'youtube'] as Platform[]
            ).map((platform) => (
              <PlatformCard
                key={platform}
                platform={platform}
                isConnected={isPlatformConnected(platform)}
                messageCount={0}
                onConnect={() => handleConnect(platform)}
                onDisconnect={() => handleDisconnect(platform)}
                onSettings={() => handleSettings(platform)}
                onTest={() => handleTest(platform)}
              />
            ))}
          </div>
        </div>

        {/* BUSINESS Platforms -- require Company accounts or paid API tiers */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Business Platforms
            </h2>
            <Badge variant="warning">API Keys Required</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(
              [
                'whatsapp',
                'instagram',
                'facebook',
                'linkedin',
                'tiktok',
                'snapchat',
                'pinterest',
              ] as Platform[]
            ).map((platform) => (
              <PlatformCard
                key={platform}
                platform={platform}
                isConnected={false}
                messageCount={0}
                onConnect={() => handleConnect(platform)}
                onDisconnect={() => handleDisconnect(platform)}
                onSettings={() => handleSettings(platform)}
                onTest={() => handleTest(platform)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Connection Guide */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle size={20} className="text-blue-600" />
            Connection Guide
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Telegram
              </h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li>1. Open Telegram and message @socialspace_agent_bot</li>
                <li>2. Then message @userinfobot to get your numeric chat ID</li>
                <li>3. Click Connect Telegram and paste your chat ID</li>
                <li>4. The bot sends a confirmation message to confirm</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Discord
              </h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li>1. Enable Developer Mode in Discord (Settings &gt; Advanced)</li>
                <li>2. Make sure the SocialSpace bot is in your server</li>
                <li>3. Right-click your target channel and select Copy Channel ID</li>
                <li>4. Click Connect Discord and paste the channel ID</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* Connection Modal -- shown only for Telegram and Discord */}
      {/* Twitter and Reddit connect are browser redirects, not modals */}
      {/* ------------------------------------------------------------------ */}
      {selectedPlatform && showConnectionModal && (
        <ConnectionModal
          platform={selectedPlatform}
          isOpen={showConnectionModal}
          onClose={() => {
            setShowConnectionModal(false)
            setSelectedPlatform(null)
          }}
          onConnect={handleConnectionSubmit}
          connecting={isConnecting}
        />
      )}
    </div>
  )
}