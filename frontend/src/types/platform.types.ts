/**
 * Platform Types
 */

import { Platform } from '@/utils/constants'

export interface PlatformConfig {
  platform: Platform
  displayName: string
  isConnected: boolean
  apiKey?: string
  accessToken?: string
  lastSync?: string
  messageCount?: number
  status: 'connected' | 'disconnected' | 'error'
}

export interface PlatformStats {
  platform: Platform
  totalMessages: number
  unreadMessages: number
  sentMessages: number
  receivedMessages: number
  lastActivity?: string
}