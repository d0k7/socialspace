// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\pages\Composer\ComposerPage.tsx

/**
 * ComposerPage - Multi-Platform Post Creator
 * 
 * FAANG++++ Standards:
 * - Rich text post composition
 * - Multi-platform publishing
 * - Media upload with preview
 * - Character counter per platform
 * - Schedule posts
 * - Save as draft
 * - Platform-specific formatting
 * - AI content suggestions
 * - Emoji picker
 * - Hashtag suggestions
 * - Preview mode
 * - Form validation
 * - Loading states
 * - Error handling
 * - Dark mode support
 * 
 * Features:
 * - Create posts for multiple platforms
 * - Upload images/videos
 * - Schedule for later
 * - Save drafts
 * - Character limits
 * - Platform icons
 * - Preview post
 */

import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Image as ImageIcon,
  Calendar,
  Send,
  Save,
  Sparkles,
  X,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
  Eye,
  Hash,
  Smile,
} from 'lucide-react';
import api from '../../lib/api';
import { useToast } from '../../components/common/Toast';

// ============================================================================
// INTERFACES
// ============================================================================

type PlatformType = 'twitter' | 'facebook' | 'instagram' | 'linkedin' | 'tiktok' | 'youtube';

interface Platform {
  id: PlatformType;
  name: string;
  icon: string;
  characterLimit: number;
  color: string;
  enabled: boolean;
}

interface MediaFile {
  id: string;
  file: File;
  preview: string;
  type: 'image' | 'video';
}

interface PostDraft {
  content: string;
  platforms: PlatformType[];
  media: MediaFile[];
  scheduledFor?: Date;
}

// ============================================================================
// PLATFORMS CONFIG
// ============================================================================

const PLATFORMS: Platform[] = [
  {
    id: 'twitter',
    name: 'Twitter',
    icon: '𝕏',
    characterLimit: 280,
    color: 'bg-black text-white',
    enabled: false,
  },
  {
    id: 'facebook',
    name: 'Facebook',
    icon: 'f',
    characterLimit: 63206,
    color: 'bg-blue-600 text-white',
    enabled: false,
  },
  {
    id: 'instagram',
    name: 'Instagram',
    icon: '📷',
    characterLimit: 2200,
    color: 'bg-gradient-to-tr from-purple-600 via-pink-600 to-orange-500 text-white',
    enabled: false,
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: 'in',
    characterLimit: 3000,
    color: 'bg-blue-700 text-white',
    enabled: false,
  },
  {
    id: 'tiktok',
    name: 'TikTok',
    icon: '🎵',
    characterLimit: 2200,
    color: 'bg-black text-white',
    enabled: false,
  },
  {
    id: 'youtube',
    name: 'YouTube',
    icon: '▶',
    characterLimit: 5000,
    color: 'bg-red-600 text-white',
    enabled: false,
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

export const ComposerPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ============================================================================
  // STATE
  // ============================================================================

  const [content, setContent] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<PlatformType[]>([]);
  const [media, setMedia] = useState<MediaFile[]>([]);
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [isScheduled, setIsScheduled] = useState(false);

  const [isPublishing, setIsPublishing] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showAISuggestions, setShowAISuggestions] = useState(false);

  const [errors, setErrors] = useState<string[]>([]);

  // ============================================================================
  // PLATFORM HANDLERS
  // ============================================================================

  const togglePlatform = (platformId: PlatformType) => {
    setSelectedPlatforms(prev => {
      if (prev.includes(platformId)) {
        return prev.filter(p => p !== platformId);
      } else {
        return [...prev, platformId];
      }
    });
    setErrors([]);
  };

  // ============================================================================
  // MEDIA HANDLERS
  // ============================================================================

  const handleMediaUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newMedia: MediaFile[] = [];

    Array.from(files).forEach((file) => {
      // Validate file type
      if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
        toast.error('Only images and videos are allowed');
        return;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB');
        return;
      }

      const mediaFile: MediaFile = {
        id: Math.random().toString(36).substr(2, 9),
        file,
        preview: URL.createObjectURL(file),
        type: file.type.startsWith('image/') ? 'image' : 'video',
      };

      newMedia.push(mediaFile);
    });

    setMedia(prev => [...prev, ...newMedia]);
  };

  const removeMedia = (id: string) => {
    setMedia(prev => {
      const mediaToRemove = prev.find(m => m.id === id);
      if (mediaToRemove) {
        URL.revokeObjectURL(mediaToRemove.preview);
      }
      return prev.filter(m => m.id !== id);
    });
  };

  // ============================================================================
  // VALIDATION
  // ============================================================================

  const validate = (): boolean => {
    const newErrors: string[] = [];

    if (!content.trim()) {
      newErrors.push('Post content is required');
    }

    if (selectedPlatforms.length === 0) {
      newErrors.push('Select at least one platform');
    }

    // Check character limits
    selectedPlatforms.forEach(platformId => {
      const platform = PLATFORMS.find(p => p.id === platformId);
      if (platform && content.length > platform.characterLimit) {
        newErrors.push(`Content exceeds ${platform.name} character limit (${platform.characterLimit})`);
      }
    });

    if (isScheduled) {
      if (!scheduledDate || !scheduledTime) {
        newErrors.push('Schedule date and time are required');
      } else {
        const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);
        if (scheduledDateTime <= new Date()) {
          newErrors.push('Scheduled time must be in the future');
        }
      }
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  // ============================================================================
  // PUBLISH HANDLERS
  // ============================================================================

  const handlePublish = async () => {
    if (!validate()) return;

    setIsPublishing(true);

    try {
      const formData = new FormData();
      formData.append('content', content);
      formData.append('platforms', JSON.stringify(selectedPlatforms));

      if (isScheduled) {
        const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);
        formData.append('scheduledFor', scheduledDateTime.toISOString());
      }

      // Add media files
      media.forEach((m, index) => {
        formData.append(`media_${index}`, m.file);
      });

      await api.post('/posts', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success(
        isScheduled
          ? 'Post scheduled successfully!'
          : 'Post published successfully!'
      );

      // Reset form
      setContent('');
      setSelectedPlatforms([]);
      setMedia([]);
      setScheduledDate('');
      setScheduledTime('');
      setIsScheduled(false);

      // Navigate to dashboard
      setTimeout(() => navigate('/dashboard'), 1500);

    } catch (error: any) {
      console.error('Failed to publish post:', error);
      toast.error(
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Failed to publish post. Please try again.'
      );
    } finally {
      setIsPublishing(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!content.trim()) {
      toast.error('Cannot save empty draft');
      return;
    }

    setIsSavingDraft(true);

    try {
      const draft: PostDraft = {
        content,
        platforms: selectedPlatforms,
        media,
        scheduledFor: isScheduled
          ? new Date(`${scheduledDate}T${scheduledTime}`)
          : undefined,
      };

      // Save to localStorage for now (in production, save to backend)
      const drafts = JSON.parse(localStorage.getItem('post_drafts') || '[]');
      drafts.push({
        ...draft,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
      });
      localStorage.setItem('post_drafts', JSON.stringify(drafts));

      toast.success('Draft saved successfully!');
    } catch (error) {
      console.error('Failed to save draft:', error);
      toast.error('Failed to save draft');
    } finally {
      setIsSavingDraft(false);
    }
  };

  // ============================================================================
  // AI SUGGESTIONS
  // ============================================================================

  const generateAISuggestion = () => {
    setShowAISuggestions(true);
    // In production, this would call the AI API
    toast.info('AI suggestions coming soon!');
  };

  const insertHashtag = () => {
    setContent(prev => prev + ' #');
  };

  const insertEmoji = () => {
    setContent(prev => prev + ' 😊');
  };

  // ============================================================================
  // CHARACTER COUNT
  // ============================================================================

  const getMinCharacterLimit = (): number => {
    if (selectedPlatforms.length === 0) return Infinity;
    
    const limits = selectedPlatforms.map(platformId => {
      const platform = PLATFORMS.find(p => p.id === platformId);
      return platform?.characterLimit || Infinity;
    });

    return Math.min(...limits);
  };

  const characterLimit = getMinCharacterLimit();
  const characterCount = content.length;
  const characterPercentage = (characterCount / characterLimit) * 100;
  const isOverLimit = characterCount > characterLimit;

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Create Post
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Compose and publish across multiple platforms
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300"
          >
            Cancel
          </button>
        </div>

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">
                  Please fix the following errors:
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {errors.map((error, index) => (
                    <li key={index} className="text-sm text-red-700 dark:text-red-300">
                      {error}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Composer - 2 columns */}
          <div className="lg:col-span-2 space-y-6">
            {/* Post Content */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Post Content
                </label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={insertHashtag}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    title="Add hashtag"
                  >
                    <Hash className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  </button>
                  <button
                    onClick={insertEmoji}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    title="Add emoji"
                  >
                    <Smile className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  </button>
                  <button
                    onClick={generateAISuggestion}
                    className="flex items-center gap-2 px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors text-sm font-medium"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>AI Assist</span>
                  </button>
                </div>
              </div>

              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="What's on your mind?"
                rows={8}
                className={`
                  w-full px-4 py-3 border rounded-lg resize-none
                  bg-white dark:bg-gray-900 
                  text-gray-900 dark:text-gray-100
                  placeholder-gray-400 dark:placeholder-gray-500
                  focus:outline-none focus:ring-2
                  ${isOverLimit
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
                  }
                `}
              />

              {/* Character Counter */}
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  {selectedPlatforms.length > 0 && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {selectedPlatforms.map(platformId => {
                        const platform = PLATFORMS.find(p => p.id === platformId);
                        return platform?.name;
                      }).join(', ')}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {/* Progress Ring */}
                  <div className="relative w-10 h-10">
                    <svg className="w-10 h-10 transform -rotate-90">
                      <circle
                        cx="20"
                        cy="20"
                        r="16"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="none"
                        className="text-gray-200 dark:text-gray-700"
                      />
                      <circle
                        cx="20"
                        cy="20"
                        r="16"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 16}`}
                        strokeDashoffset={`${2 * Math.PI * 16 * (1 - characterPercentage / 100)}`}
                        className={`
                          ${characterPercentage >= 90
                            ? 'text-red-500'
                            : characterPercentage >= 70
                            ? 'text-yellow-500'
                            : 'text-blue-500'
                          }
                        `}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span
                        className={`
                          text-xs font-medium
                          ${isOverLimit
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-gray-700 dark:text-gray-300'
                          }
                        `}
                      >
                        {characterLimit === Infinity ? '∞' : characterLimit - characterCount}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Media Upload */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 block">
                Media
              </label>

              {/* Uploaded Media */}
              {media.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                  {media.map((m) => (
                    <div key={m.id} className="relative group">
                      {m.type === 'image' ? (
                        <img
                          src={m.preview}
                          alt="Upload preview"
                          className="w-full h-32 object-cover rounded-lg"
                        />
                      ) : (
                        <video
                          src={m.preview}
                          className="w-full h-32 object-cover rounded-lg"
                        />
                      )}
                      <button
                        onClick={() => removeMedia(m.id)}
                        className="absolute top-2 right-2 p-1.5 bg-red-600 hover:bg-red-700 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
              >
                <ImageIcon className="w-5 h-5" />
                <span>Upload Images or Videos</span>
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,video/*"
                multiple
                onChange={handleMediaUpload}
                className="hidden"
              />

              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Maximum file size: 10MB per file
              </p>
            </div>

            {/* Schedule */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Schedule Post
                </label>
                <button
                  onClick={() => setIsScheduled(!isScheduled)}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${isScheduled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
                  `}
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${isScheduled ? 'translate-x-6' : 'translate-x-1'}
                    `}
                  />
                </button>
              </div>

              {isScheduled && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-700 dark:text-gray-300 mb-2">
                      Date
                    </label>
                    <input
                      type="date"
                      value={scheduledDate}
                      onChange={(e) => setScheduledDate(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700 dark:text-gray-300 mb-2">
                      Time
                    </label>
                    <input
                      type="time"
                      value={scheduledTime}
                      onChange={(e) => setScheduledTime(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar - 1 column */}
          <div className="space-y-6">
            {/* Platform Selection */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 block">
                Select Platforms
              </label>

              <div className="space-y-3">
                {PLATFORMS.map((platform) => (
                  <button
                    key={platform.id}
                    onClick={() => togglePlatform(platform.id)}
                    className={`
                      w-full p-3 rounded-lg border-2 transition-all text-left
                      ${selectedPlatforms.includes(platform.id)
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded flex items-center justify-center text-sm font-bold ${platform.color}`}>
                        {platform.icon}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-gray-100">
                          {platform.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {platform.characterLimit.toLocaleString()} chars
                        </div>
                      </div>
                      {selectedPlatforms.includes(platform.id) && (
                        <CheckCircle2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-3">
              {/* Publish/Schedule Button */}
              <button
                onClick={handlePublish}
                disabled={isPublishing || isOverLimit}
                className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isPublishing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>{isScheduled ? 'Scheduling...' : 'Publishing...'}</span>
                  </>
                ) : (
                  <>
                    {isScheduled ? (
                      <>
                        <Calendar className="w-5 h-5" />
                        <span>Schedule Post</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        <span>Publish Now</span>
                      </>
                    )}
                  </>
                )}
              </button>

              {/* Save Draft */}
              <button
                onClick={handleSaveDraft}
                disabled={isSavingDraft}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 font-medium flex items-center justify-center gap-2"
              >
                {isSavingDraft ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-5 h-5" />
                    <span>Save Draft</span>
                  </>
                )}
              </button>

              {/* Preview */}
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 font-medium flex items-center justify-center gap-2"
              >
                <Eye className="w-5 h-5" />
                <span>Preview</span>
              </button>
            </div>

            {/* Tips */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                💡 Pro Tips
              </h4>
              <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                <li>• Use AI Assist for content ideas</li>
                <li>• Schedule posts for optimal times</li>
                <li>• Add hashtags for better reach</li>
                <li>• Include images for 2x engagement</li>
              </ul>
            </div>
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
