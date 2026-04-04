/**
 * Analytics Hook
 * 
 * React Query hooks for analytics data
 */

import { useQuery } from '@tanstack/react-query'
import { QUERY_KEYS } from '@/utils/constants'
import * as analyticsApi from '@/api/endpoints/analytics'
import type { Platform } from '@/utils/constants'

/**
 * Get dashboard stats
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: [QUERY_KEYS.ANALYTICS, 'dashboard'],
    queryFn: analyticsApi.getDashboardStats,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}

/**
 * Get platform analytics
 */
export function usePlatformAnalytics(
  platform: Platform,
  startDate?: string,
  endDate?: string
) {
  return useQuery({
    queryKey: [QUERY_KEYS.ANALYTICS, platform, startDate, endDate],
    queryFn: () => analyticsApi.getPlatformAnalytics(platform, startDate, endDate),
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get all analytics
 */
export function useAllAnalytics(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: [QUERY_KEYS.ANALYTICS, 'all', startDate, endDate],
    queryFn: () => analyticsApi.getAllAnalytics(startDate, endDate),
    staleTime: 5 * 60 * 1000,
  })
}