/**
 * Axios API Client
 * 
 * Centralized HTTP client with interceptors for:
 * - Authentication
 * - Error handling
 * - Request/Response logging
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { API_BASE_URL, API_TIMEOUT, STORAGE_KEYS } from '@/utils/constants'

/**
 * Create Axios instance
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request Interceptor
 * Add auth token to all requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Log request in development
    if (import.meta.env.DEV) {
      console.log('🔵 API Request:', config.method?.toUpperCase(), config.url)
    }
    
    return config
  },
  (error) => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

/**
 * Response Interceptor
 * Handle errors globally
 */
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log('🟢 API Response:', response.config.url, response.status)
    }
    
    return response
  },
  (error: AxiosError) => {
    // Log error
    console.error('❌ API Error:', error.response?.status, error.message)
    
    // Handle specific error codes
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - clear auth and redirect to login
          localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
          localStorage.removeItem(STORAGE_KEYS.USER)
          window.location.href = '/login'
          break
        
        case 403:
          // Forbidden
          console.error('Access forbidden')
          break
        
        case 404:
          // Not found
          console.error('Resource not found')
          break
        
        case 500:
          // Server error
          console.error('Server error')
          break
        
        default:
          console.error('Unknown error occurred')
      }
    }
    
    return Promise.reject(error)
  }
)

/**
 * API Error Type
 */
export interface ApiError {
  message: string
  status?: number
  data?: any
}

/**
 * Extract error message from API error
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message || error.message || 'An error occurred'
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  return 'An unknown error occurred'
}

export default apiClient