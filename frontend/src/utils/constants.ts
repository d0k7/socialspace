/**
 * Application Constants
 */

export const APP_NAME = 'SocialSpace'
export const APP_VERSION = '1.0.0'

/**
 * API Configuration
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const API_TIMEOUT = 30000 // 30 seconds

/**
 * Supported Platforms
 */
export const PLATFORMS = {
  WHATSAPP: 'whatsapp',
  TELEGRAM: 'telegram',
  INSTAGRAM: 'instagram',
  DISCORD: 'discord',
  REDDIT: 'reddit',
  TWITTER: 'twitter',
  YOUTUBE: 'youtube',
  FACEBOOK: 'facebook',
  LINKEDIN: 'linkedin',
  TIKTOK: 'tiktok',
  SNAPCHAT: 'snapchat',
  PINTEREST: 'pinterest',
} as const

export type Platform = (typeof PLATFORMS)[keyof typeof PLATFORMS]

/**
 * Platform Display Names
 */
export const PLATFORM_NAMES: Record<Platform, string> = {
  whatsapp: 'WhatsApp',
  telegram: 'Telegram',
  instagram: 'Instagram',
  discord: 'Discord',
  reddit: 'Reddit',
  twitter: 'Twitter',
  youtube: 'YouTube',
  facebook: 'Facebook',
  linkedin: 'LinkedIn',
  tiktok: 'TikTok',
  snapchat: 'Snapchat',
  pinterest: 'Pinterest',
}

/**
 * Platform Colors (for UI)
 */
export const PLATFORM_COLORS: Record<Platform, string> = {
  whatsapp: '#25D366',
  telegram: '#0088cc',
  instagram: '#E4405F',
  discord: '#5865F2',
  reddit: '#FF4500',
  twitter: '#1DA1F2',
  youtube: '#FF0000',
  facebook: '#1877F2',
  linkedin: '#0A66C2',
  tiktok: '#000000',
  snapchat: '#FFFC00',
  pinterest: '#E60023',
}

/**
 * Routes
 */
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  MESSAGES: '/messages',
  PLATFORMS: '/platforms',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
  PROFILE: '/profile',
} as const

/**
 * Local Storage Keys
 */
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'access_token',
  // WHY: 'refresh_token' matches the key written by AuthContext.tsx KEYS.REFRESH_TOKEN.
  // Centralizing here so api/client.ts and AuthContext.tsx both read from one source of truth
  // instead of each hardcoding the string independently.
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  THEME: 'theme',
  PLATFORMS: 'platforms',
} as const

/**
 * Query Keys (React Query)
 */
export const QUERY_KEYS = {
  USER: 'user',
  PLATFORMS: 'platforms',
  MESSAGES: 'messages',
  ANALYTICS: 'analytics',
  DASHBOARD: 'dashboard',
} as const
