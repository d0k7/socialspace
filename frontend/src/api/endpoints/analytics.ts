/**
 * Analytics API Endpoints
 */

import apiClient from '@/api/client'
import type { Platform } from '@/utils/constants'

export interface AnalyticsData {
  platform: Platform
  totalMessages: number
  messagesByDay: Array<{ date: string; count: number }>
  topSenders: Array<{ name: string; count: number }>
  engagementRate: number
  responseTime: number
}

export interface DashboardStats {
  totalMessages: number
  unreadMessages: number
  connectedPlatforms: number
  totalPlatforms: number
  recentActivity: Array<{
    platform: Platform
    message: string
    timestamp: string
  }>
}

/**
 * Get dashboard statistics
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>('/analytics/dashboard')
  return response.data
}

/**
 * Get analytics for specific platform
 */
export async function getPlatformAnalytics(
  platform: Platform,
  startDate?: string,
  endDate?: string
): Promise<AnalyticsData> {
  const response = await apiClient.get<AnalyticsData>(`/analytics/${platform}`, {
    params: { startDate, endDate },
  })
  return response.data
}

/**
 * Get analytics for all platforms
 */
export async function getAllAnalytics(
  startDate?: string,
  endDate?: string
): Promise<AnalyticsData[]> {
  const response = await apiClient.get<AnalyticsData[]>('/analytics', {
    params: { startDate, endDate },
  })
  return response.data
}