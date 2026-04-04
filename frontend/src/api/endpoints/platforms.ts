/**
 * Platform Management API Endpoints
 */

import apiClient from '@/api/client'
import type { PlatformConfig, PlatformStats } from '@/types/platform.types'
import type { Platform } from '@/utils/constants'

/**
 * Get all connected platforms
 */
export async function getPlatforms(): Promise<PlatformConfig[]> {
  const response = await apiClient.get<PlatformConfig[]>('/platforms')
  return response.data
}

/**
 * Get specific platform config
 */
export async function getPlatform(platform: Platform): Promise<PlatformConfig> {
  const response = await apiClient.get<PlatformConfig>(`/platforms/${platform}`)
  return response.data
}

/**
 * Connect a platform
 */
export async function connectPlatform(
  platform: Platform,
  config: Partial<PlatformConfig>
): Promise<PlatformConfig> {
  const response = await apiClient.post<PlatformConfig>(`/platforms/${platform}/connect`, config)
  return response.data
}

/**
 * Disconnect a platform
 */
export async function disconnectPlatform(platform: Platform): Promise<void> {
  await apiClient.post(`/platforms/${platform}/disconnect`)
}

/**
 * Test platform connection
 */
export async function testPlatformConnection(platform: Platform): Promise<{ success: boolean }> {
  const response = await apiClient.post<{ success: boolean }>(`/platforms/${platform}/test`)
  return response.data
}

/**
 * Get platform statistics
 */
export async function getPlatformStats(platform: Platform): Promise<PlatformStats> {
  const response = await apiClient.get<PlatformStats>(`/platforms/${platform}/stats`)
  return response.data
}

/**
 * Get all platform statistics
 */
export async function getAllPlatformStats(): Promise<PlatformStats[]> {
  const response = await apiClient.get<PlatformStats[]>('/platforms/stats')
  return response.data
}