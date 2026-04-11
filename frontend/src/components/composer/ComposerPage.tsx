// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\pages\Composer\ComposerPage.tsx

/**
 * ComposerPage - Main Post Composition Interface
 * 
 * FAANG++++ Standards:
 * - Comprehensive state management
 * - Form validation
 * - API integration with error handling
 * - Auto-save functionality
 * - Loading states and optimistic updates
 * - Keyboard shortcuts
 * - Responsive layout
 * - Accessibility compliant
 * - Success/error feedback
 * 
 * Features:
 * - Rich text post composition
 * - Multi-platform selection
 * - Media upload
 * - Scheduling
 * - Live preview
 * - Character counting
 * - Draft management
 * - Form validation
 * - Submit handling
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Send,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Eye,
  Edit3,
} from 'lucide-react';

// Components
import PostEditor from '../../components/composer/PostEditor';
import PlatformSelector from '../../components/composer/PlatformSelector';
import MediaUploader from '../../components/composer/MediaUploader';
import SchedulePicker from '../../components/composer/SchedulePicker';
import CharacterCounter from '../../components/composer/CharacterCounter';
import PreviewPanel from '../../components/composer/PreviewPanel';

// Types
import {
  PlatformType,
  MediaFile,
  ComposerFormData,
  CreatePostRequest,
  exceedsAnyLimit,
} from '../../types/composer.types';

// API
import api from '../../api/client';

// ============================================================================
// INTERFACES
// ============================================================================

interface ComposerPageProps {
  // Optional: pre-fill data for editing
  initialData?: Partial<ComposerFormData>;
  mode?: 'create' | 'edit';
  postId?: string;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const ComposerPage: React.FC<ComposerPageProps> = ({
  initialData,
  mode = 'create',
  postId,
}) => {
  const navigate = useNavigate();

  // ============================================================================
  // STATE
  // ============================================================================

  // Form data
  const [content, setContent] = useState(initialData?.content || '');
  const [selectedPlatforms, setSelectedPlatforms] = useState<PlatformType[]>(
    initialData?.platforms || []
  );
  const [media, setMedia] = useState<MediaFile[]>(initialData?.media || []);
  const [scheduleType, setScheduleType] = useState<'now' | 'scheduled'>(
    initialData?.scheduleType || 'now'
  );
  const [scheduledFor, setScheduledFor] = useState<Date | undefined>(
    initialData?.scheduledFor
  );
  const [timezone, setTimezone] = useState(
    initialData?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
  );

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [connectedPlatforms, setConnectedPlatforms] = useState<PlatformType[]>([]);
  const [isLoadingPlatforms, setIsLoadingPlatforms] = useState(true);

  // User info (for preview)
  const [userName, setUserName] = useState('Your Name');
  const [userAvatar, setUserAvatar] = useState('');

  // ============================================================================
  // LOAD USER DATA AND CONNECTED PLATFORMS
  // ============================================================================

  useEffect(() => {
    const loadUserData = async () => {
      try {
        // Load user profile
        const userResponse = await api.get('/user/profile');
        setUserName(userResponse.data.name || 'Your Name');
        setUserAvatar(userResponse.data.avatar || '');

        // Load connected platforms
        const platformsResponse = await api.get('/platforms/connections');
        const connected = platformsResponse.data
          .filter((conn: any) => conn.status === 'connected')
          .map((conn: any) => conn.platform as PlatformType);
        
        setConnectedPlatforms(connected);
      } catch (error) {
        console.error('Failed to load user data:', error);
        // Set defaults
        setConnectedPlatforms([]);
      } finally {
        setIsLoadingPlatforms(false);
      }
    };

    loadUserData();
  }, []);

  // ============================================================================
  // VALIDATION
  // ============================================================================

  const validate = useCallback((): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    // Check if content or media exists
    if (!content.trim() && media.length === 0) {
      errors.push('Please add content or media to your post');
    }

    // Check if platforms selected
    if (selectedPlatforms.length === 0) {
      errors.push('Please select at least one platform');
    }

    // Check character limits
    if (exceedsAnyLimit(content, selectedPlatforms)) {
      errors.push('Content exceeds character limit for some platforms');
    }

    // Check scheduled time
    if (scheduleType === 'scheduled') {
      if (!scheduledFor) {
        errors.push('Please select a date and time for scheduling');
      } else {
        const now = new Date();
        if (scheduledFor <= new Date(now.getTime() + 5 * 60000)) {
          errors.push('Scheduled time must be at least 5 minutes in the future');
        }
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, [content, media, selectedPlatforms, scheduleType, scheduledFor]);

  // ============================================================================
  // SUBMIT HANDLER
  // ============================================================================

  const handleSubmit = async () => {
    // Validate
    const validation = validate();
    if (!validation.isValid) {
      setSubmitError(validation.errors.join('. '));
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Upload media first (if any)
      const mediaUrls: string[] = [];
      for (const mediaFile of media) {
        if (!mediaFile.uploadedUrl) {
          // Upload media
          const formData = new FormData();
          formData.append('file', mediaFile.file);
          formData.append('type', mediaFile.type);

          const uploadResponse = await api.post('/media/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });

          mediaUrls.push(uploadResponse.data.cdn_url);
        } else {
          mediaUrls.push(mediaFile.uploadedUrl);
        }
      }

      // Prepare request
      const request: CreatePostRequest = {
        content,
        platforms: selectedPlatforms,
        media_urls: mediaUrls.length > 0 ? mediaUrls : undefined,
        scheduled_for:
          scheduleType === 'scheduled' && scheduledFor
            ? scheduledFor.toISOString()
            : undefined,
        timezone: scheduleType === 'scheduled' ? timezone : undefined,
      };

      // Submit post
      if (mode === 'edit' && postId) {
        await api.put(`/posts/${postId}`, request);
      } else {
        await api.post('/posts', request);
      }

      // Success!
      setSubmitSuccess(true);
      
      // Clear form
      setTimeout(() => {
        if (mode === 'create') {
          // Clear draft
          localStorage.removeItem('composer-draft');
          
          // Redirect to posts or dashboard
          navigate('/posts');
        } else {
          // Redirect back
          navigate(-1);
        }
      }, 2000);

    } catch (error: any) {
      console.error('Submit error:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Failed to publish post. Please try again.';
      setSubmitError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ============================================================================
  // DISCARD HANDLER
  // ============================================================================

  const handleDiscard = useCallback(() => {
    if (
      content ||
      media.length > 0 ||
      selectedPlatforms.length > 0
    ) {
      const confirmed = window.confirm(
        'Are you sure you want to discard this post? All changes will be lost.'
      );
      if (!confirmed) return;
    }

    // Clear draft
    localStorage.removeItem('composer-draft');
    
    // Navigate back
    navigate(-1);
  }, [content, media, selectedPlatforms, navigate]);

  // ============================================================================
  // KEYBOARD SHORTCUTS
  // ============================================================================

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Enter = Submit
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }

      // Ctrl/Cmd + P = Toggle Preview
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        setShowPreview(!showPreview);
      }

      // Escape = Close preview
      if (e.key === 'Escape' && showPreview) {
        setShowPreview(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showPreview, handleSubmit]);

  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================

  const canSubmit =
    !isSubmitting &&
    !submitSuccess &&
    (content.trim() || media.length > 0) &&
    selectedPlatforms.length > 0 &&
    !exceedsAnyLimit(content, selectedPlatforms);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Title */}
            <div className="flex items-center gap-3">
              <Edit3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {mode === 'edit' ? 'Edit Post' : 'Create Post'}
              </h1>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              {/* Preview Toggle */}
              <button
                type="button"
                onClick={() => setShowPreview(!showPreview)}
                className={`
                  px-4 py-2 rounded-lg border transition-colors
                  ${showPreview
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }
                `}
                title="Toggle Preview (Ctrl+P)"
              >
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4" />
                  <span className="hidden sm:inline">Preview</span>
                </div>
              </button>

              {/* Discard */}
              <button
                type="button"
                onClick={handleDiscard}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-center gap-2">
                  <X className="w-4 h-4" />
                  <span className="hidden sm:inline">Discard</span>
                </div>
              </button>

              {/* Submit */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!canSubmit}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
                title="Submit Post (Ctrl+Enter)"
              >
                <div className="flex items-center gap-2">
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : submitSuccess ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  <span>
                    {isSubmitting
                      ? 'Publishing...'
                      : submitSuccess
                      ? 'Published!'
                      : scheduleType === 'scheduled'
                      ? 'Schedule'
                      : 'Publish'}
                  </span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success Message */}
        {submitSuccess && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg animate-fadeIn">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0" />
              <div>
                <div className="font-medium text-green-900 dark:text-green-100">
                  {scheduleType === 'scheduled'
                    ? 'Post scheduled successfully!'
                    : 'Post published successfully!'}
                </div>
                <div className="text-sm text-green-700 dark:text-green-300 mt-1">
                  Redirecting...
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {submitError && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium text-red-900 dark:text-red-100">
                  Failed to publish post
                </div>
                <div className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {submitError}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSubmitError(null)}
                className="text-red-400 hover:text-red-600 dark:hover:text-red-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Two-Column Layout */}
        <div className={`grid gap-6 ${showPreview ? 'lg:grid-cols-2' : 'lg:grid-cols-1'}`}>
          {/* Left Column - Composer */}
          <div className="space-y-6">
            {/* Post Editor */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Write Your Post
              </h2>
              <PostEditor
                value={content}
                onChange={setContent}
                selectedPlatforms={selectedPlatforms}
                autoFocus={true}
              />
            </div>

            {/* Media Upload */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Add Media
              </h2>
              <MediaUploader
                media={media}
                onChange={setMedia}
                selectedPlatforms={selectedPlatforms}
                disabled={isSubmitting}
              />
            </div>

            {/* Platform Selection */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              {isLoadingPlatforms ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              ) : (
                <PlatformSelector
                  selectedPlatforms={selectedPlatforms}
                  onChange={setSelectedPlatforms}
                  contentLength={content.length}
                  connectedPlatforms={connectedPlatforms}
                  disabled={isSubmitting}
                />
              )}
            </div>

            {/* Schedule */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <SchedulePicker
                scheduleType={scheduleType}
                scheduledFor={scheduledFor}
                timezone={timezone}
                onScheduleTypeChange={setScheduleType}
                onScheduledForChange={setScheduledFor}
                onTimezoneChange={setTimezone}
                disabled={isSubmitting}
              />
            </div>

            {/* Character Counter */}
            {selectedPlatforms.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <CharacterCounter
                  content={content}
                  selectedPlatforms={selectedPlatforms}
                  showDetails={true}
                />
              </div>
            )}
          </div>

          {/* Right Column - Preview (if enabled) */}
          {showPreview && (
            <div className="lg:sticky lg:top-24 lg:self-start">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 max-h-[calc(100vh-8rem)] overflow-y-auto">
                <PreviewPanel
                  content={content}
                  selectedPlatforms={selectedPlatforms}
                  media={media}
                  userName={userName}
                  userAvatar={userAvatar}
                />
              </div>
            </div>
          )}
        </div>

        {/* Bottom Actions (Mobile) */}
        <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 safe-area-inset-bottom">
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleDiscard}
              disabled={isSubmitting}
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 font-medium disabled:opacity-50"
            >
              Discard
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Publishing...</span>
                </div>
              ) : submitSuccess ? (
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Published!</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  <Send className="w-5 h-5" />
                  <span>
                    {scheduleType === 'scheduled' ? 'Schedule' : 'Publish'}
                  </span>
                </div>
              )}
            </button>
          </div>
        </div>

        {/* Keyboard Shortcuts Help */}
        <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <span className="font-medium text-gray-900 dark:text-gray-100">
              Keyboard shortcuts:
            </span>{' '}
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-xs">
              Ctrl+Enter
            </kbd>{' '}
            to publish •{' '}
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-xs">
              Ctrl+P
            </kbd>{' '}
            to toggle preview •{' '}
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-xs">
              Ctrl+B
            </kbd>{' '}
            bold •{' '}
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-xs">
              Ctrl+I
            </kbd>{' '}
            italic •{' '}
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-xs">
              Ctrl+K
            </kbd>{' '}
            link
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default ComposerPage;
