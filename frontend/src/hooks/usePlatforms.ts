/**
 * Platforms Hook
 * 
 * Fetches platform data with React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getPlatforms, 
  connectPlatform, 
  disconnectPlatform,
  getAllPlatformStats 
} from '@/api/endpoints/platforms'
import { QUERY_KEYS } from '@/utils/constants'
import type { Platform } from '@/utils/constants'
import type { PlatformConfig } from '@/types/platform.types'
import toast from 'react-hot-toast'

export function usePlatforms() {
  return useQuery({
    queryKey: [QUERY_KEYS.PLATFORMS],
    queryFn: getPlatforms,
    staleTime: 60000, // 1 minute
  })
}

export function usePlatformStats() {
  return useQuery({
    queryKey: [QUERY_KEYS.PLATFORMS, 'stats'],
    queryFn: getAllPlatformStats,
    refetchInterval: 60000, // Refetch every minute
  })
}

export function useConnectPlatform() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ platform, config }: { platform: Platform; config: Partial<PlatformConfig> }) =>
      connectPlatform(platform, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.PLATFORMS] })
      toast.success('Platform connected successfully!')
    },
    onError: () => {
      toast.error('Failed to connect platform')
    },
  })
}

export function useDisconnectPlatform() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (platform: Platform) => disconnectPlatform(platform),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.PLATFORMS] })
      toast.success('Platform disconnected')
    },
    onError: () => {
      toast.error('Failed to disconnect platform')
    },
  })
}