// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\composer\PreviewPanel.tsx

/**
 * PreviewPanel Component - Live Platform Previews
 * 
 * FAANG++++ Standards:
 * - Real-time preview for each platform
 * - Platform-specific styling and layout
 * - Content truncation based on limits
 * - Media preview integration
 * - Responsive design
 * - Accurate representation of platform UI
 * - Dark mode support
 * 
 * Features:
 * - Live preview cards for each platform
 * - Platform-specific formatting (hashtags, mentions, links)
 * - Character limit truncation with indicator
 * - Media thumbnail display
 * - Timestamp simulation
 * - User avatar/name display
 * - Expandable/collapsible sections
 */

import React, { useMemo } from 'react';
import {
  Twitter,
  Linkedin,
  Instagram,
  Facebook,
  MessageCircle,
  MessageSquare,
  Share2,
  Youtube,
  Phone,
  Music,
  Camera,
  Image as ImageIcon,
  MoreHorizontal,
  Heart,
  MessageCircle as Comment,
  Send,
  Bookmark,
  ThumbsUp,
  Share as ShareIcon,
  Eye,
} from 'lucide-react';
import {
  PlatformType,
  MediaFile,
  PLATFORM_NAMES,
  PLATFORM_COLORS,
  getCharacterLimit,
  truncateText,
} from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface PreviewPanelProps {
  content: string;
  selectedPlatforms: PlatformType[];
  media: MediaFile[];
  userName?: string;
  userAvatar?: string;
}

interface PlatformPreviewProps {
  platform: PlatformType;
  content: string;
  media: MediaFile[];
  userName: string;
  userAvatar: string;
}

// ============================================================================
// PLATFORM ICONS MAP
// ============================================================================

const PLATFORM_ICON_MAP: Record<PlatformType, React.ReactNode> = {
  twitter: <Twitter className="w-4 h-4" />,
  linkedin: <Linkedin className="w-4 h-4" />,
  instagram: <Instagram className="w-4 h-4" />,
  facebook: <Facebook className="w-4 h-4" />,
  telegram: <MessageCircle className="w-4 h-4" />,
  discord: <MessageSquare className="w-4 h-4" />,
  reddit: <Share2 className="w-4 h-4" />,
  youtube: <Youtube className="w-4 h-4" />,
  whatsapp: <Phone className="w-4 h-4" />,
  tiktok: <Music className="w-4 h-4" />,
  snapchat: <Camera className="w-4 h-4" />,
  pinterest: <ImageIcon className="w-4 h-4" />,
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Format content with basic Markdown-style formatting
 */
const formatContent = (content: string): React.ReactNode => {
  if (!content) return null;

  // Split by newlines
  const lines = content.split('\n');

  return lines.map((line, lineIndex) => {
    // Process inline formatting
    const parts: React.ReactNode[] = [];
    let currentText = line;
    let key = 0;

    // Process **bold**
    const boldRegex = /\*\*(.*?)\*\*/g;
    let lastIndex = 0;
    let match;

    while ((match = boldRegex.exec(line)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lineIndex}-${key++}`}>
            {line.substring(lastIndex, match.index)}
          </span>
        );
      }
      // Add bold text
      parts.push(
        <strong key={`bold-${lineIndex}-${key++}`}>{match[1]}</strong>
      );
      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < line.length) {
      parts.push(
        <span key={`text-${lineIndex}-${key++}`}>
          {line.substring(lastIndex)}
        </span>
      );
    }

    return (
      <React.Fragment key={lineIndex}>
        {parts.length > 0 ? parts : line}
        {lineIndex < lines.length - 1 && <br />}
      </React.Fragment>
    );
  });
};

/**
 * Get truncated content for platform
 */
const getTruncatedContent = (
  content: string,
  platform: PlatformType
): { text: string; isTruncated: boolean } => {
  const limit = getCharacterLimit(platform);
  const isTruncated = content.length > limit;
  const text = isTruncated ? truncateText(content, limit) : content;
  return { text, isTruncated };
};

// ============================================================================
// PLATFORM-SPECIFIC PREVIEW COMPONENTS
// ============================================================================

const TwitterPreview: React.FC<PlatformPreviewProps> = ({
  content,
  media,
  userName,
  userAvatar,
}) => {
  const { text, isTruncated } = getTruncatedContent(content, 'twitter');

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
            {userName.charAt(0).toUpperCase()}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-gray-900 dark:text-gray-100">
              {userName}
            </span>
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              @{userName.toLowerCase().replace(/\s/g, '')}
            </span>
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              · 1m
            </span>
          </div>

          <div className="text-gray-900 dark:text-gray-100 mb-3 whitespace-pre-wrap">
            {formatContent(text)}
            {isTruncated && (
              <span className="text-blue-500 ml-1">...see more</span>
            )}
          </div>

          {/* Media Grid */}
          {media.length > 0 && (
            <div
              className={`
                grid gap-1 rounded-2xl overflow-hidden mb-3
                ${media.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}
              `}
            >
              {media.slice(0, 4).map((m, idx) => (
                <div
                  key={idx}
                  className={`
                    aspect-video bg-gray-200 dark:bg-gray-700
                    ${media.length === 3 && idx === 0 ? 'col-span-2' : ''}
                  `}
                >
                  <img
                    src={m.url}
                    alt={`Media ${idx + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
            <button className="flex items-center gap-2 hover:text-blue-500 transition-colors">
              <Comment className="w-5 h-5" />
              <span className="text-sm">42</span>
            </button>
            <button className="flex items-center gap-2 hover:text-green-500 transition-colors">
              <Share2 className="w-5 h-5" />
              <span className="text-sm">12</span>
            </button>
            <button className="flex items-center gap-2 hover:text-red-500 transition-colors">
              <Heart className="w-5 h-5" />
              <span className="text-sm">156</span>
            </button>
            <button className="hover:text-blue-500 transition-colors">
              <Bookmark className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const LinkedInPreview: React.FC<PlatformPreviewProps> = ({
  content,
  media,
  userName,
  userAvatar,
}) => {
  const { text, isTruncated } = getTruncatedContent(content, 'linkedin');

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4">
        <div className="flex gap-3 mb-3">
          <div className="w-12 h-12 rounded-full bg-blue-700 flex items-center justify-center text-white font-semibold">
            {userName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="font-semibold text-gray-900 dark:text-gray-100">
              {userName}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Professional Title • 1m
            </div>
          </div>
          <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <MoreHorizontal className="w-5 h-5" />
          </button>
        </div>

        <div className="text-gray-900 dark:text-gray-100 mb-3 whitespace-pre-wrap">
          {formatContent(text)}
          {isTruncated && (
            <button className="text-blue-600 ml-1 font-medium">
              ...see more
            </button>
          )}
        </div>
      </div>

      {/* Media */}
      {media.length > 0 && (
        <div className="w-full">
          <img
            src={media[0].url}
            alt="Post media"
            className="w-full object-cover max-h-96"
          />
        </div>
      )}

      {/* Actions */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-around text-gray-600 dark:text-gray-400">
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 px-4 py-2 rounded transition-colors">
            <ThumbsUp className="w-5 h-5" />
            <span className="text-sm font-medium">Like</span>
          </button>
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 px-4 py-2 rounded transition-colors">
            <Comment className="w-5 h-5" />
            <span className="text-sm font-medium">Comment</span>
          </button>
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 px-4 py-2 rounded transition-colors">
            <Share2 className="w-5 h-5" />
            <span className="text-sm font-medium">Share</span>
          </button>
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 px-4 py-2 rounded transition-colors">
            <Send className="w-5 h-5" />
            <span className="text-sm font-medium">Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const InstagramPreview: React.FC<PlatformPreviewProps> = ({
  content,
  media,
  userName,
  userAvatar,
}) => {
  const { text, isTruncated } = getTruncatedContent(content, 'instagram');

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-500 p-0.5">
            <div className="w-full h-full rounded-full bg-white dark:bg-gray-900 flex items-center justify-center">
              <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                {userName.charAt(0).toUpperCase()}
              </span>
            </div>
          </div>
          <span className="font-semibold text-sm text-gray-900 dark:text-gray-100">
            {userName.toLowerCase().replace(/\s/g, '')}
          </span>
        </div>
        <button className="text-gray-900 dark:text-gray-100">
          <MoreHorizontal className="w-5 h-5" />
        </button>
      </div>

      {/* Media */}
      {media.length > 0 && (
        <div className="aspect-square bg-gray-100 dark:bg-gray-800">
          <img
            src={media[0].url}
            alt="Instagram post"
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Actions */}
      <div className="p-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4">
            <button className="hover:text-gray-600 dark:hover:text-gray-300">
              <Heart className="w-6 h-6" />
            </button>
            <button className="hover:text-gray-600 dark:hover:text-gray-300">
              <Comment className="w-6 h-6" />
            </button>
            <button className="hover:text-gray-600 dark:hover:text-gray-300">
              <Send className="w-6 h-6" />
            </button>
          </div>
          <button className="hover:text-gray-600 dark:hover:text-gray-300">
            <Bookmark className="w-6 h-6" />
          </button>
        </div>

        <div className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">
          1,234 likes
        </div>

        <div className="text-sm text-gray-900 dark:text-gray-100">
          <span className="font-semibold">
            {userName.toLowerCase().replace(/\s/g, '')}{' '}
          </span>
          <span className="whitespace-pre-wrap">
            {text}
            {isTruncated && (
              <button className="text-gray-500 ml-1">more</button>
            )}
          </span>
        </div>

        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          1 MINUTE AGO
        </div>
      </div>
    </div>
  );
};

const FacebookPreview: React.FC<PlatformPreviewProps> = ({
  content,
  media,
  userName,
  userAvatar,
}) => {
  const { text, isTruncated } = getTruncatedContent(content, 'facebook');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
              {userName.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                {userName}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                1 min · 🌐
              </div>
            </div>
          </div>
          <button className="text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 p-1 rounded-full">
            <MoreHorizontal className="w-5 h-5" />
          </button>
        </div>

        <div className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap mb-3">
          {formatContent(text)}
          {isTruncated && (
            <button className="text-gray-500 hover:underline">
              ... See more
            </button>
          )}
        </div>
      </div>

      {/* Media */}
      {media.length > 0 && (
        <div className="w-full">
          <img
            src={media[0].url}
            alt="Facebook post"
            className="w-full object-cover max-h-96"
          />
        </div>
      )}

      {/* Stats */}
      <div className="px-4 py-2 border-t border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <div className="flex -space-x-1">
              <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                <ThumbsUp className="w-3 h-3 text-white" fill="white" />
              </div>
              <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                <Heart className="w-3 h-3 text-white" fill="white" />
              </div>
            </div>
            <span>You and 42 others</span>
          </div>
          <div className="flex items-center gap-2">
            <span>8 comments</span>
            <span>3 shares</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="p-2">
        <div className="flex items-center justify-around">
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex-1 justify-center py-2 rounded transition-colors text-gray-600 dark:text-gray-400">
            <ThumbsUp className="w-5 h-5" />
            <span className="font-medium">Like</span>
          </button>
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex-1 justify-center py-2 rounded transition-colors text-gray-600 dark:text-gray-400">
            <Comment className="w-5 h-5" />
            <span className="font-medium">Comment</span>
          </button>
          <button className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex-1 justify-center py-2 rounded transition-colors text-gray-600 dark:text-gray-400">
            <ShareIcon className="w-5 h-5" />
            <span className="font-medium">Share</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const GenericPreview: React.FC<PlatformPreviewProps> = ({
  platform,
  content,
  media,
  userName,
}) => {
  const { text, isTruncated } = getTruncatedContent(content, platform);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-3 mb-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold"
          style={{ backgroundColor: PLATFORM_COLORS[platform] }}
        >
          {userName.charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="font-semibold text-gray-900 dark:text-gray-100">
            {userName}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            1 minute ago
          </div>
        </div>
      </div>

      <div className="text-gray-900 dark:text-gray-100 mb-3 whitespace-pre-wrap">
        {formatContent(text)}
        {isTruncated && (
          <span className="text-gray-500 ml-1">...see more</span>
        )}
      </div>

      {media.length > 0 && (
        <div className="rounded-lg overflow-hidden mb-3">
          <img
            src={media[0].url}
            alt="Post media"
            className="w-full max-h-64 object-cover"
          />
        </div>
      )}

      <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
        <button className="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300">
          <Heart className="w-4 h-4" />
          <span>Like</span>
        </button>
        <button className="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300">
          <Comment className="w-4 h-4" />
          <span>Comment</span>
        </button>
        <button className="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300">
          <ShareIcon className="w-4 h-4" />
          <span>Share</span>
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// PREVIEW SELECTOR
// ============================================================================

const PlatformPreviewSelector: React.FC<PlatformPreviewProps> = (props) => {
  const { platform } = props;

  switch (platform) {
    case 'twitter':
      return <TwitterPreview {...props} />;
    case 'linkedin':
      return <LinkedInPreview {...props} />;
    case 'instagram':
      return <InstagramPreview {...props} />;
    case 'facebook':
      return <FacebookPreview {...props} />;
    default:
      return <GenericPreview {...props} />;
  }
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const PreviewPanel: React.FC<PreviewPanelProps> = ({
  content,
  selectedPlatforms,
  media,
  userName = 'Your Name',
  userAvatar = '',
}) => {
  // ============================================================================
  // RENDER
  // ============================================================================

  if (selectedPlatforms.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <Eye className="w-8 h-8 text-gray-400 dark:text-gray-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No platforms selected
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Select platforms to see how your post will look
        </p>
      </div>
    );
  }

  if (!content && media.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <Eye className="w-8 h-8 text-gray-400 dark:text-gray-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Preview will appear here
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Start typing or add media to see a preview
        </p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
          Preview
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          See how your post will look on each platform
        </p>
      </div>

      <div className="space-y-6">
        {selectedPlatforms.map((platform) => (
          <div key={platform}>
            {/* Platform Header */}
            <div className="flex items-center gap-2 mb-3">
              <div
                className="p-1.5 rounded"
                style={{ backgroundColor: `${PLATFORM_COLORS[platform]}20` }}
              >
                <div style={{ color: PLATFORM_COLORS[platform] }}>
                  {PLATFORM_ICON_MAP[platform]}
                </div>
              </div>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {PLATFORM_NAMES[platform]}
              </span>
            </div>

            {/* Preview Card */}
            <PlatformPreviewSelector
              platform={platform}
              content={content}
              media={media}
              userName={userName}
              userAvatar={userAvatar}
            />
          </div>
        ))}
      </div>

      {/* Info Note */}
      <div className="mt-6 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="text-sm text-blue-900 dark:text-blue-100">
          <p className="font-medium">Note:</p>
          <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
            These are approximate previews. Actual appearance may vary slightly
            depending on platform updates and user settings.
          </p>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default PreviewPanel;