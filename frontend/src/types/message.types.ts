/**
 * Message Types - Enhanced
 */

import { Platform } from '@/utils/constants'

export interface Message {
  id: string
  platform: Platform
  platformMessageId: string
  sender: {
    id: string
    username: string
    displayName: string
    avatarUrl?: string
  }
  content: string
  media?: Array<{
    url: string
    type: 'image' | 'video' | 'audio' | 'document'
  }>
  timestamp: string
  isRead: boolean
  isArchived?: boolean
  isDeleted?: boolean
  deletedAt?: string
  metadata?: Record<string, any>
}

export interface MessageFilter {
  platform?: Platform
  isRead?: boolean
  isArchived?: boolean
  isDeleted?: boolean
  searchQuery?: string
  startDate?: string
  endDate?: string
}
