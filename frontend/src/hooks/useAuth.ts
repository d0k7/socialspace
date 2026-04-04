/**
 * Auth Hook
 * 
 * React Query hook for authentication
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { QUERY_KEYS, ROUTES } from '@/utils/constants'
import * as authApi from '@/api/endpoints/auth'
import type { LoginCredentials, RegisterCredentials } from '@/types/auth.types'
import toast from 'react-hot-toast'

/**
 * Get current user
 */
export function useCurrentUser() {
  const { user, isAuthenticated } = useAuthStore()
  
  return useQuery({
    queryKey: [QUERY_KEYS.USER, 'current'],
    queryFn: authApi.getCurrentUser,
    enabled: isAuthenticated && !user,
    retry: 1,
  })
}

/**
 * Login mutation
 */
export function useLogin() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  
  return useMutation({
    mutationFn: (credentials: LoginCredentials) => authApi.login(credentials),
    onSuccess: (data) => {
      login(data.user, data.token)
      toast.success('Welcome back! 🎉')
      navigate(ROUTES.DASHBOARD)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Login failed')
    },
  })
}

/**
 * Register mutation
 */
export function useRegister() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  
  return useMutation({
    mutationFn: (credentials: RegisterCredentials) => authApi.register(credentials),
    onSuccess: (data) => {
      login(data.user, data.token)
      toast.success('Account created successfully! 🎉')
      navigate(ROUTES.DASHBOARD)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Registration failed')
    },
  })
}

/**
 * Logout mutation
 */
export function useLogout() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      logout()
      queryClient.clear()
      toast.success('Logged out successfully')
      navigate(ROUTES.LOGIN)
    },
    onError: () => {
      // Logout locally even if API fails
      logout()
      queryClient.clear()
      navigate(ROUTES.LOGIN)
    },
  })
}