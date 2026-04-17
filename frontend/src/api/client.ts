/**
 * Axios API Client
 * Created: Phase 0, Session 0.2
 * Updated: Phase 1, Session 1.4 — automatic token refresh interceptor
 *
 * WHY this file exists:
 * Centralizes all HTTP configuration in one place. Every component imports
 * from here, so auth headers, base URL, timeout, and error handling are
 * applied uniformly across the entire frontend. No component should ever
 * call axios directly.
 *
 * Interceptor architecture:
 * - Request interceptor: attaches Bearer token from localStorage to every outgoing request
 * - Response interceptor: on 401, silently attempts token refresh before failing.
 *   On refresh success: retries the original request transparently.
 *   On refresh failure: clears auth state and redirects to login.
 *   All requests that arrive during an in-flight refresh are queued and
 *   replayed once the new token is available — no request is silently dropped.
 */

import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from 'axios'
import { API_BASE_URL, API_TIMEOUT, STORAGE_KEYS } from '@/utils/constants'

// =============================================================================
// REFRESH QUEUE TYPES
// WHY: When a token refresh is already in flight, subsequent 401 responses
// must wait for that refresh to complete rather than each triggering their own
// refresh call. This queue holds their resolve/reject callbacks so they can be
// replayed or failed atomically once the refresh settles.
// =============================================================================

interface QueuedRequest {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

// =============================================================================
// MODULE-LEVEL REFRESH STATE
// WHY: Must be module-level (not inside the interceptor closure) so that all
// interceptor invocations share the same isRefreshing flag and failedQueue.
// If these were inside the interceptor function they would reset on every call.
// =============================================================================

let isRefreshing = false
let failedQueue: QueuedRequest[] = []

/**
 * processQueue
 *
 * WHY: After a refresh attempt settles (success or failure), every queued
 * request must be unblocked. On success, resolve with the new token so each
 * queued request can attach it to its retry. On failure, reject with the
 * original error so callers receive a meaningful rejection instead of hanging.
 *
 * @param error - The refresh error if the refresh failed, null on success
 * @param token - The new access token if the refresh succeeded, null on failure
 */
function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      // token is guaranteed non-null here because error is null — safe cast
      resolve(token as string)
    }
  })
  // WHY: Clear the queue after processing so stale callbacks cannot be
  // accidentally replayed if a second refresh cycle begins later.
  failedQueue = []
}

// =============================================================================
// AXIOS INSTANCE
// WHY: A dedicated instance (not the global axios) isolates SocialSpace's
// interceptors from any third-party library that might also use axios.
// baseURL set here means every call uses a path like /api/auth/login — no
// component ever hardcodes the host.
// =============================================================================

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// =============================================================================
// REQUEST INTERCEPTOR — attach access token
// WHY: Attaching the token here means every request is automatically
// authenticated. Components never touch headers directly.
// =============================================================================

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    if (import.meta.env.DEV) {
      console.log('🔵 API Request:', config.method?.toUpperCase(), config.url)
    }

    return config
  },
  (error: unknown) => {
    console.error('❌ Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// =============================================================================
// RESPONSE INTERCEPTOR — silent token refresh on 401
//
// WHY this logic exists:
// Access tokens expire after 30 minutes. Without this interceptor, every
// expiry results in a hard logout that breaks any in-progress work, including
// Phase 2 OAuth flows. With this interceptor, expiry is invisible to the user:
// the refresh happens in the background, the original request is retried with
// the new token, and the component receives its data as if nothing happened.
//
// Race condition protection:
// If 5 API calls fire simultaneously and the token is expired, all 5 get 401.
// Without the queue, all 5 would each attempt a refresh, causing 5 concurrent
// /api/auth/refresh calls with the same refresh token — most would fail because
// refresh tokens are typically single-use or rate-limited.
// The isRefreshing flag + failedQueue ensures only ONE refresh call is made.
// The other 4 requests queue up and are replayed once the single refresh settles.
//
// _retry flag:
// The retried request will have a fresh access token, but if the server still
// returns 401 (e.g. token was revoked server-side), we must NOT loop infinitely.
// The _retry flag on the config marks that this request has already been through
// one refresh cycle. A second 401 on a retried request goes straight to logout.
// =============================================================================

apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log('🟢 API Response:', response.config.url, response.status)
    }
    return response
  },
  async (error: AxiosError) => {
    // WHY: Capture the original config early. After any async await, the error
    // object's reference may be reused or mutated by axios internals.
    const originalConfig = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    const status = error.response?.status

    // -------------------------------------------------------------------------
    // NON-401 ERRORS — pass through immediately, no refresh attempt
    // -------------------------------------------------------------------------
    if (status !== 401) {
      if (import.meta.env.DEV) {
        console.error('❌ API Error:', status, error.message)
      }

      if (status === 403) {
        console.error('API: Access forbidden — user lacks permission for this resource')
      } else if (status === 404) {
        console.error('API: Resource not found:', originalConfig?.url)
      } else if (status === 500) {
        console.error('API: Internal server error — check backend logs')
      }

      return Promise.reject(error)
    }

    // -------------------------------------------------------------------------
    // 401 ON A RETRIED REQUEST — refresh already happened and still 401.
    // This means the server rejected the new token (revoked, invalid, etc.).
    // Hard logout — do not attempt another refresh.
    // -------------------------------------------------------------------------
    if (originalConfig?._retry) {
      console.error(
        'API: Token refresh succeeded but server still returned 401 on retry. ' +
        'Token may be revoked server-side. Logging out.'
      )
      clearAuthAndRedirect()
      return Promise.reject(error)
    }

    // -------------------------------------------------------------------------
    // 401 ON A FIRST ATTEMPT — check if we have a refresh token to use
    // -------------------------------------------------------------------------
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)

    if (!refreshToken) {
      // WHY: No refresh token means the user was never properly logged in,
      // or they already logged out. Hard redirect without attempting refresh.
      console.error('API: 401 received but no refresh token in storage. Redirecting to login.')
      clearAuthAndRedirect()
      return Promise.reject(error)
    }

    // -------------------------------------------------------------------------
    // ANOTHER REFRESH ALREADY IN FLIGHT — queue this request
    // WHY: Do not fire a second refresh. Queue this request's resolve/reject
    // callbacks. processQueue() will replay them when the in-flight refresh settles.
    // -------------------------------------------------------------------------
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then((newToken) => {
          // Attach the new token and retry this queued request
          if (originalConfig.headers) {
            originalConfig.headers.Authorization = `Bearer ${newToken}`
          }
          return apiClient(originalConfig)
        })
        .catch((queueError) => {
          // The refresh that was in flight failed — reject this queued request too
          return Promise.reject(queueError)
        })
    }

    // -------------------------------------------------------------------------
    // INITIATE TOKEN REFRESH
    // WHY: Mark _retry before the await so that if this same request gets a 401
    // after the retry, the guard at the top catches it and prevents infinite loop.
    // Mark isRefreshing before the await so concurrent 401s queue up rather than
    // each launching their own refresh.
    // -------------------------------------------------------------------------
    originalConfig._retry = true
    isRefreshing = true

    try {
      // WHY: Call axios directly (not apiClient) to bypass our own interceptors.
      // Using apiClient here would trigger the request interceptor which reads
      // the OLD access token from localStorage — but we need to send the refresh
      // token, not the access token. A direct axios call with explicit body is
      // clean and avoids interceptor interference.
      const refreshResponse = await axios.post<{ access_token: string }>(
        `${API_BASE_URL}/api/auth/refresh`,
        { refresh_token: refreshToken },
        { headers: { 'Content-Type': 'application/json' } }
      )

      const newAccessToken = refreshResponse.data.access_token

      // Persist the new access token so subsequent requests (and the retry below)
      // find it in localStorage
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, newAccessToken)

      if (import.meta.env.DEV) {
        console.log('🔄 Token refreshed successfully — replaying queued requests')
      }

      // Unblock all queued requests with the new token
      processQueue(null, newAccessToken)

      // Retry the original request that triggered this refresh
      if (originalConfig.headers) {
        originalConfig.headers.Authorization = `Bearer ${newAccessToken}`
      }

      return apiClient(originalConfig)
    } catch (refreshError) {
      // WHY: The refresh call itself failed (refresh token expired, server down,
      // network error). Every queued request must be rejected — they cannot be
      // replayed without a valid token. Then clear auth and redirect to login.
      processQueue(refreshError, null)
      console.error('API: Token refresh failed — session cannot be restored. Logging out.', refreshError)
      clearAuthAndRedirect()
      return Promise.reject(refreshError)
    } finally {
      // WHY: Always reset isRefreshing in finally, not in try/catch, so the flag
      // is cleared even if an unexpected error occurs mid-refresh. A stuck
      // isRefreshing = true would queue every future 401 forever.
      isRefreshing = false
    }
  }
)

// =============================================================================
// HELPER — clear auth storage and redirect to login
// WHY: Extracted as a named function so all logout paths (retry failure, no
// refresh token, refresh call failure) share identical cleanup logic. If we
// ever add more keys to clear (e.g. Redux store reset, analytics session end),
// we update this one function.
// =============================================================================

function clearAuthAndRedirect(): void {
  localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
  localStorage.removeItem(STORAGE_KEYS.USER)

  // WHY: window.location.href performs a full page navigation which clears all
  // React in-memory state (context, hooks, component state). This is intentional
  // on logout — we do not want stale user data in memory after session ends.
  window.location.href = '/login'
}

// =============================================================================
// EXPORTED UTILITIES
// =============================================================================

/**
 * ApiError
 * Typed shape for error objects returned from the backend.
 * WHY: Gives callers a predictable structure to check instead of casting
 * unknown error objects with as any.
 */
export interface ApiError {
  message: string
  status?: number
  detail?: string
}

/**
 * getErrorMessage
 * Extract a human-readable error string from any thrown value.
 * WHY: API errors, network errors, and unknown throws all have different shapes.
 * Centralizing extraction here means no component needs error-shape logic.
 *
 * @param error - Any thrown value (AxiosError, Error, string, unknown)
 * @returns Human-readable error string safe to display in UI
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    // WHY: FastAPI returns validation and business errors in detail field.
    // Fall back to message then generic string so the UI always has something to show.
    return (
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An error occurred'
    )
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}

export default apiClient