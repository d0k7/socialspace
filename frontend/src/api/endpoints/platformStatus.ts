/**
 * Platform Status API — Real Endpoints for Live Platforms
 * =========================================================
 * Created: Phase 4, Session 4.2
 *
 * WHY this file exists (separate from platforms.ts):
 * The existing platforms.ts targets /platforms/* — a unified API route that
 * does not exist yet on the backend. These 3 platforms (Telegram, Discord,
 * Twitter) have dedicated routers already live. This file calls those real
 * endpoints directly.
 *
 * WHY not modify platforms.ts:
 * platforms.ts is the future unified API scaffold. It stays untouched for
 * the phase when a single /api/platforms endpoint is built. This file is
 * the production implementation for the 3 live platforms today.
 *
 * Endpoints covered:
 *   Telegram : GET/POST/DELETE /api/telegram/status|connect|disconnect
 *   Discord  : GET/POST/DELETE /api/discord/status|connect|disconnect
 *   Twitter  : GET/DELETE      /api/auth/twitter/status|disconnect
 *              Twitter connect = browser redirect to /api/auth/twitter/authorize
 */

import apiClient from '@/api/client'

// ============================================================================
// RESPONSE TYPE DEFINITIONS
// WHY explicit interfaces instead of inferred: These shapes must match the
// backend routers exactly. An interface documents the contract and fails at
// compile time if the caller uses a field that does not exist.
//
// telegram.py /status returns: { connected, chat_id, chat_name }
// discord.py  /status returns: { connected, channel_id, channel_name }
// twitter.py  /status returns: { connected, username, display_name, expires_at }
// ============================================================================

export interface TelegramStatus {
  /** Whether a PlatformConnection row exists with is_active=true for telegram */
  connected: boolean
  /** Numeric Telegram chat ID stored in PlatformConnection.platform_user_id */
  chat_id: string | null
  /** Human-readable name stored in PlatformConnection.platform_display_name */
  chat_name: string | null
}

export interface DiscordStatus {
  /** Whether a PlatformConnection row exists with is_active=true for discord */
  connected: boolean
  /** Numeric Discord channel ID stored in PlatformConnection.platform_user_id */
  channel_id: string | null
  /**
   * Channel name fetched from Discord API at connect time and cached in
   * PlatformConnection.platform_display_name. Authoritative — comes from
   * Discord, not from the user.
   */
  channel_name: string | null
}

export interface TwitterStatus {
  /** Whether a PlatformConnection row exists with is_active=true for twitter */
  connected: boolean
  /** Twitter @username stored in PlatformConnection.platform_username */
  username: string | null
  /** Twitter display name stored in PlatformConnection.platform_display_name */
  display_name: string | null
  /**
   * ISO 8601 UTC datetime when the OAuth 2.0 access token expires.
   * Twitter tokens expire after 2 hours. Auto-refresh is not yet implemented —
   * manual reconnect via OAuth flow required after expiry.
   */
  expires_at: string | null
}

// ============================================================================
// STATUS ENDPOINTS
// WHY read from our DB not from the platform API:
// Status checks happen on every PlatformsPage load. Calling Twitter/Telegram/
// Discord APIs on every load wastes quota, adds latency, and can fail when
// the platform is temporarily down. Reading our own DB is fast and reliable.
// ============================================================================

/**
 * Check Telegram connection status for the current authenticated user.
 * Reads PlatformConnection table — no live Telegram API call.
 */
export async function getTelegramStatus(): Promise<TelegramStatus> {
  const response = await apiClient.get<TelegramStatus>('/api/telegram/status')
  return response.data
}

/**
 * Check Discord connection status for the current authenticated user.
 * Reads PlatformConnection table — no live Discord API call.
 */
export async function getDiscordStatus(): Promise<DiscordStatus> {
  const response = await apiClient.get<DiscordStatus>('/api/discord/status')
  return response.data
}

/**
 * Check Twitter connection status for the current authenticated user.
 * Reads PlatformConnection table — no live Twitter API call.
 */
export async function getTwitterStatus(): Promise<TwitterStatus> {
  const response = await apiClient.get<TwitterStatus>('/api/auth/twitter/status')
  return response.data
}

// ============================================================================
// CONNECT ENDPOINTS
//
// WHY Telegram and Discord connect via POST (not OAuth redirect):
// Both platforms authenticate SocialSpace via a static bot token already in
// backend .env. The user only needs to supply their destination — a chat_id
// (Telegram) or channel_id (Discord). The backend validates the destination
// (Telegram: sends a test message; Discord: fetches channel info via bot),
// then upserts a PlatformConnection row.
//
// WHY Twitter connect is NOT in this file:
// Twitter uses OAuth 2.0 PKCE. There is no form — the backend generates a
// code_verifier + state, stores them server-side, then returns a 302 redirect
// to Twitter's authorization URL. The connect flow is a browser navigation to
// GET /api/auth/twitter/authorize. No API call to make from the frontend.
// ============================================================================

/**
 * Connect a Telegram chat to the current user's SocialSpace account.
 * The backend validates the chat_id by sending a confirmation message via Bot API.
 * User must have messaged @socialspace_agent_bot before calling this.
 *
 * @param chatId   - Numeric Telegram chat ID (get it from @userinfobot)
 * @param chatName - Optional display label for this chat in the UI
 */
export async function connectTelegram(
  chatId: string,
  chatName?: string
): Promise<{ connected: boolean; chat_id: string; chat_name: string }> {
  const response = await apiClient.post('/api/telegram/connect', {
    chat_id: chatId.trim(),
    // WHY conditional spread: backend chat_name field is Optional[str].
    // Omitting it lets the backend derive the name as "Telegram Chat {chat_id}".
    ...(chatName?.trim() && { chat_name: chatName.trim() }),
  })
  return response.data
}

/**
 * Connect a Discord channel to the current user's SocialSpace account.
 * The backend validates access by calling GET /channels/{channel_id} via bot token.
 * The SocialSpace bot must already be in the target server with Send Messages permission.
 *
 * @param channelId   - Numeric Discord channel ID (right-click channel → Copy Channel ID)
 * @param channelName - Optional hint; backend overrides with authoritative name from Discord API
 */
export async function connectDiscord(
  channelId: string,
  channelName?: string
): Promise<{ connected: boolean; channel_id: string; channel_name: string }> {
  const response = await apiClient.post('/api/discord/connect', {
    channel_id: channelId.trim(),
    ...(channelName?.trim() && { channel_name: channelName.trim() }),
  })
  return response.data
}

// ============================================================================
// DISCONNECT ENDPOINTS
// All three are soft deletes on the backend — is_active set to false,
// tokens JSON cleared. PlatformConnection row is preserved for audit history.
// ============================================================================

/** Disconnect Telegram from the current user's account (soft delete). */
export async function disconnectTelegram(): Promise<{ disconnected: boolean }> {
  const response = await apiClient.delete('/api/telegram/disconnect')
  return response.data
}

/** Disconnect Discord from the current user's account (soft delete). */
export async function disconnectDiscord(): Promise<{ disconnected: boolean }> {
  const response = await apiClient.delete('/api/discord/disconnect')
  return response.data
}

/** Disconnect Twitter from the current user's account (soft delete). */
export async function disconnectTwitter(): Promise<{ disconnected: boolean }> {
  const response = await apiClient.delete('/api/auth/twitter/disconnect')
  return response.data
}