/**
 * Dashboard Hook
 * 
 * Fetches dashboard data with React Query
 */

import { useQuery } from '@tanstack/react-query'
import { getDashboardStats } from '@/api/endpoints/analytics'
import { QUERY_KEYS } from '@/utils/constants'

export function useDashboardStats() {
  return useQuery({
    queryKey: [QUERY_KEYS.ANALYTICS, 'dashboard'],
    queryFn: getDashboardStats,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  })
}