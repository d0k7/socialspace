/**
 * Authentication API Endpoints
 */

import apiClient from '@/api/client'
import type { 
  AuthResponse, 
  LoginCredentials, 
  RegisterCredentials, 
  User 
} from '@/types/auth.types'

/**
 * Login user
 */
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', credentials)
  return response.data
}

/**
 * Register new user
 */
export async function register(credentials: RegisterCredentials): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/register', credentials)
  return response.data
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

/**
 * Get current user
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}

/**
 * Refresh auth token
 */
export async function refreshToken(): Promise<{ token: string }> {
  const response = await apiClient.post<{ token: string }>('/auth/refresh')
  return response.data
}