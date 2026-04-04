/**
 * Message Management API Endpoints
 */

import apiClient from '@/api/client'
import type { Message, MessageFilter } from '@/types/message.types'
import type { Platform } from '@/utils/constants'

/**
 * Get messages from all platforms
 */
export async function getMessages(filters?: MessageFilter): Promise<Message[]> {
  const response = await apiClient.get<Message[]>('/messages', { params: filters })
  return response.data
}

/**
 * Get messages from specific platform
 */
export async function getPlatformMessages(
  platform: Platform,
  filters?: Omit<MessageFilter, 'platform'>
): Promise<Message[]> {
  const response = await apiClient.get<Message[]>(`/messages/${platform}`, { params: filters })
  return response.data
}

/**
 * Get single message
 */
export async function getMessage(messageId: string): Promise<Message> {
  const response = await apiClient.get<Message>(`/messages/${messageId}`)
  return response.data
}

/**
 * Send message to platform
 */
export async function sendMessage(
  platform: Platform,
  content: string,
  recipientId?: string
): Promise<Message> {
  const response = await apiClient.post<Message>(`/messages/${platform}/send`, {
    content,
    recipientId,
  })
  return response.data
}

/**
 * Mark message as read
 */
export async function markMessageAsRead(messageId: string): Promise<void> {
  await apiClient.patch(`/messages/${messageId}/read`)
}

/**
 * Mark all messages as read
 */
export async function markAllMessagesAsRead(platform?: Platform): Promise<void> {
  const url = platform ? `/messages/${platform}/read-all` : '/messages/read-all'
  await apiClient.post(url)
}

/**
 * Delete message
 */
export async function deleteMessage(messageId: string): Promise<void> {
  await apiClient.delete(`/messages/${messageId}`)
}