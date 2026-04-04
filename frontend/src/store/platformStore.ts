/**
 * Platform Store (Zustand)
 */

import { create } from 'zustand'
import type { PlatformConfig } from '@/types/platform.types'
import type { Platform } from '@/utils/constants'

interface PlatformState {
  platforms: PlatformConfig[]
  selectedPlatform: Platform | null
  isLoading: boolean
}

interface PlatformActions {
  setPlatforms: (platforms: PlatformConfig[]) => void
  updatePlatform: (platform: Platform, config: Partial<PlatformConfig>) => void
  setSelectedPlatform: (platform: Platform | null) => void
  setLoading: (loading: boolean) => void
  getConnectedPlatforms: () => PlatformConfig[]
}

type PlatformStore = PlatformState & PlatformActions

/**
 * Platform Store
 */
export const usePlatformStore = create<PlatformStore>((set, get) => ({
  // Initial State
  platforms: [],
  selectedPlatform: null,
  isLoading: false,

  // Actions
  setPlatforms: (platforms) => set({ platforms }),
  
  updatePlatform: (platform, config) =>
    set((state) => ({
      platforms: state.platforms.map((p) =>
        p.platform === platform ? { ...p, ...config } : p
      ),
    })),
  
  setSelectedPlatform: (platform) => set({ selectedPlatform: platform }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  getConnectedPlatforms: () => {
    const { platforms } = get()
    return platforms.filter((p) => p.isConnected)
  },
}))