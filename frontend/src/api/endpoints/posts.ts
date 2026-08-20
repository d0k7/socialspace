/**
 * Posts API -- Scheduling Endpoints
 * ===================================
 * Created: Phase 5, Session 5.x (frontend wiring)
 * August 2026
 *
 * WHY this file exists (separate from platformStatus.ts):
 * platformStatus.ts covers platform connection status. This file covers
 * the actual content lifecycle: schedule, list what is upcoming, cancel.
 * Same reasoning as platformStatus.ts's own separation from platforms.ts,
 * one file per real, live backend concern, not one grab bag file.
 *
 * Endpoints covered:
 *   POST   /api/posts/schedule            -- create + schedule a post
 *   GET    /api/posts/scheduled           -- list this user's upcoming posts
 *   DELETE /api/posts/scheduled/{post_id} -- cancel before it publishes
 *
 * Backend contract source: backend/app/routers/posts.py
 */

import apiClient from '@/api/client'

// ============================================================================
// REQUEST / RESPONSE TYPE DEFINITIONS
// WHY explicit interfaces instead of inferred: these shapes must match
// posts.py's Pydantic models exactly. A field typo here fails at compile
// time instead of silently sending undefined to the backend.
// ============================================================================

export interface SchedulePostRequest {
  content: string
  platforms: string[]
  /** Naive local datetime with no offset, e.g. "2026-08-20T09:00:00" */
  scheduled_at_local: string
  /** IANA timezone name, e.g. "Asia/Kolkata" */
  timezone: string
  media_urls?: string[]
  is_ai_generated?: boolean
  ai_prompt?: string
  ai_model_used?: string
}

export interface SchedulePostResponse {
  post_id: string
  scheduled_at_utc: string
  scheduled_at_local: string
  timezone: string
  platforms: string[]
  status: string
}

export interface ScheduledPostSummary {
  post_id: string
  content_preview: string
  platforms: string[]
  status: string
  scheduled_at_utc: string
  timezone: string
  retry_count: number
  max_retries: number
  created_at: string
}

export interface CancelScheduledPostResponse {
  cancelled: boolean
  post_id: string
}

// ============================================================================
// ENDPOINTS
// ============================================================================

/**
 * Create a new post and schedule it for future publishing.
 * Backend rejects (400) if the target time is in the past, the timezone
 * name is not a valid IANA name, or any target platform is not connected.
 */
export async function schedulePost(
  request: SchedulePostRequest
): Promise<SchedulePostResponse> {
  const response = await apiClient.post<SchedulePostResponse>(
    '/api/posts/schedule',
    request
  )
  return response.data
}

/**
 * List this user's posts that are currently scheduled or publishing,
 * soonest first. Does not include published, failed, or cancelled posts,
 * see posts.py list_scheduled_posts for why that scope is intentional.
 */
export async function getScheduledPosts(): Promise<ScheduledPostSummary[]> {
  const response = await apiClient.get<ScheduledPostSummary[]>(
    '/api/posts/scheduled'
  )
  return response.data
}

/**
 * Cancel a scheduled post before it publishes.
 * Backend rejects (400) if the post is already publishing, published,
 * failed, or already cancelled, only 'scheduled' status is cancellable.
 */
export async function cancelScheduledPost(
  postId: string
): Promise<CancelScheduledPostResponse> {
  const response = await apiClient.delete<CancelScheduledPostResponse>(
    `/api/posts/scheduled/${postId}`
  )
  return response.data
}
