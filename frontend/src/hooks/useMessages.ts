/**
 * Messages Hook
 * 
 * Fetches messages data with React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getMessages, 
  markMessageAsRead,
  markAllMessagesAsRead 
} from '@/api/endpoints/messages'
import { QUERY_KEYS } from '@/utils/constants'
import type { MessageFilter } from '@/types/message.types'
import toast from 'react-hot-toast'

export function useMessages(filters?: MessageFilter) {
  return useQuery({
    queryKey: [QUERY_KEYS.MESSAGES, filters],
    queryFn: () => getMessages(filters),
    staleTime: 30000, // 30 seconds
  })
}

export function useMarkAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (messageId: string) => markMessageAsRead(messageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.MESSAGES] })
    },
  })
}

export function useMarkAllAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (platform?: string) => markAllMessagesAsRead(platform),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.MESSAGES] })
      toast.success('All messages marked as read')
    },
  })
}