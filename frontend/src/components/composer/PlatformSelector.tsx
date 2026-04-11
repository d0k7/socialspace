// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\composer\PlatformSelector.tsx

/**
 * PlatformSelector Component - Multi-Platform Selection
 * 
 * FAANG++++ Standards:
 * - Multi-select checkbox grid
 * - Platform-specific branding (icons, colors)
 * - Real-time character limit display
 * - Visual warnings for content length issues
 * - Keyboard navigation support
 * - Accessibility compliant
 * - Responsive design
 * 
 * Features:
 * - Select/deselect platforms
 * - Visual indicators for connected platforms
 * - Character limit per platform
 * - Warning badges when content exceeds limit
 * - Group by category (Free vs Business)
 * - Bulk select/deselect
 */

import React, { useMemo } from 'react';
import {
  Twitter,
  Linkedin,
  Instagram,
  Facebook,
  MessageCircle, // Telegram
  MessageSquare, // Discord
  Share2, // Reddit
  Youtube,
  Phone, // WhatsApp
  Music, // TikTok
  Camera, // Snapchat
  Image as ImageIcon, // Pinterest
  AlertCircle,
  CheckCircle2,
  Circle,
} from 'lucide-react';
import {
  PlatformType,
  PLATFORMS,
  PLATFORM_NAMES,
  PLATFORM_COLORS,
  getCharacterLimit,
} from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface PlatformSelectorProps {
  selectedPlatforms: PlatformType[];
  onChange: (platforms: PlatformType[]) => void;
  contentLength: number;
  connectedPlatforms?: PlatformType[]; // Platforms user has connected
  disabled?: boolean;
}

interface PlatformCardProps {
  platform: PlatformType;
  isSelected: boolean;
  isConnected: boolean;
  contentLength: number;
  onToggle: () => void;
  disabled?: boolean;
}

// ============================================================================
// PLATFORM ICONS
// ============================================================================

const PLATFORM_ICONS: Record<PlatformType, React.ReactNode> = {
  twitter: <Twitter className="w-5 h-5" />,
  linkedin: <Linkedin className="w-5 h-5" />,
  instagram: <Instagram className="w-5 h-5" />,
  facebook: <Facebook className="w-5 h-5" />,
  telegram: <MessageCircle className="w-5 h-5" />,
  discord: <MessageSquare className="w-5 h-5" />,
  reddit: <Share2 className="w-5 h-5" />,
  youtube: <Youtube className="w-5 h-5" />,
  whatsapp: <Phone className="w-5 h-5" />,
  tiktok: <Music className="w-5 h-5" />,
  snapchat: <Camera className="w-5 h-5" />,
  pinterest: <ImageIcon className="w-5 h-5" />,
};

// ============================================================================
// PLATFORM CATEGORIES
// ============================================================================

const FREE_PLATFORMS: PlatformType[] = [
  'telegram',
  'discord',
  'reddit',
  'twitter',
  'youtube',
];

const BUSINESS_PLATFORMS: PlatformType[] = [
  'whatsapp',
  'instagram',
  'facebook',
  'linkedin',
  'tiktok',
  'snapchat',
  'pinterest',
];

// ============================================================================
// PLATFORM CARD COMPONENT
// ============================================================================

const PlatformCard: React.FC<PlatformCardProps> = ({
  platform,
  isSelected,
  isConnected,
  contentLength,
  onToggle,
  disabled = false,
}) => {
  const characterLimit = getCharacterLimit(platform);
  const exceedsLimit = contentLength > characterLimit;
  const limitPercentage = (contentLength / characterLimit) * 100;

  // Get status color
  const getStatusColor = () => {
    if (!isSelected) return 'text-gray-400 dark:text-gray-600';
    if (exceedsLimit) return 'text-red-500 dark:text-red-400';
    if (limitPercentage >= 95) return 'text-orange-500 dark:text-orange-400';
    if (limitPercentage >= 80) return 'text-yellow-500 dark:text-yellow-400';
    return 'text-green-500 dark:text-green-400';
  };

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled || !isConnected}
      className={`
        relative p-4 rounded-lg border-2 transition-all
        ${isSelected 
          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 dark:border-blue-400 shadow-md' 
          : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        }
        ${!isConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      aria-label={`${isSelected ? 'Deselect' : 'Select'} ${PLATFORM_NAMES[platform]}`}
      aria-pressed={isSelected}
      aria-disabled={!isConnected || disabled}
    >
      {/* Connected Badge */}
      {!isConnected && (
        <div className="absolute -top-2 -right-2 bg-gray-500 text-white text-xs px-2 py-1 rounded-full">
          Not Connected
        </div>
      )}

      {/* Selection Indicator */}
      <div className="absolute top-2 right-2">
        {isSelected ? (
          <CheckCircle2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        ) : (
          <Circle className="w-5 h-5 text-gray-400 dark:text-gray-600" />
        )}
      </div>

      {/* Platform Info */}
      <div className="flex flex-col items-center gap-2 mt-2">
        {/* Icon */}
        <div
          className={`p-3 rounded-full`}
          style={{
            backgroundColor: isSelected ? `${PLATFORM_COLORS[platform]}20` : 'transparent',
            color: PLATFORM_COLORS[platform],
          }}
        >
          {PLATFORM_ICONS[platform]}
        </div>

        {/* Name */}
        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {PLATFORM_NAMES[platform]}
        </div>

        {/* Character Limit */}
        {isSelected && (
          <div className="text-xs text-center">
            <div className={`font-semibold ${getStatusColor()}`}>
              {contentLength} / {characterLimit}
            </div>
            {exceedsLimit && (
              <div className="flex items-center gap-1 text-red-600 dark:text-red-400 mt-1">
                <AlertCircle className="w-3 h-3" />
                <span>Too long</span>
              </div>
            )}
          </div>
        )}
      </div>
    </button>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const PlatformSelector: React.FC<PlatformSelectorProps> = ({
  selectedPlatforms,
  onChange,
  contentLength,
  connectedPlatforms = PLATFORMS, // Default: all platforms connected
  disabled = false,
}) => {
  // ============================================================================
  // HANDLERS
  // ============================================================================

  const togglePlatform = (platform: PlatformType) => {
    if (selectedPlatforms.includes(platform)) {
      onChange(selectedPlatforms.filter(p => p !== platform));
    } else {
      onChange([...selectedPlatforms, platform]);
    }
  };

  const selectAll = () => {
    onChange(connectedPlatforms);
  };

  const deselectAll = () => {
    onChange([]);
  };

  const selectFree = () => {
    const freePlatformsConnected = FREE_PLATFORMS.filter(p =>
      connectedPlatforms.includes(p)
    );
    onChange(freePlatformsConnected);
  };

  const selectBusiness = () => {
    const businessPlatformsConnected = BUSINESS_PLATFORMS.filter(p =>
      connectedPlatforms.includes(p)
    );
    onChange(businessPlatformsConnected);
  };

  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================

  const connectedCount = connectedPlatforms.length;
  const selectedCount = selectedPlatforms.length;

  const platformsExceedingLimit = useMemo(() => {
    return selectedPlatforms.filter(
      platform => contentLength > getCharacterLimit(platform)
    );
  }, [selectedPlatforms, contentLength]);

  const hasExceedingPlatforms = platformsExceedingLimit.length > 0;

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Select Platforms
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Choose where to publish ({selectedCount} selected, {connectedCount} connected)
            </p>
          </div>

          {/* Bulk Actions */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAll}
              disabled={disabled || connectedCount === 0}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={deselectAll}
              disabled={disabled || selectedCount === 0}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Deselect All
            </button>
          </div>
        </div>

        {/* Warning Banner */}
        {hasExceedingPlatforms && contentLength > 0 && (
          <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-red-900 dark:text-red-100">
                  Content exceeds character limit
                </div>
                <div className="text-xs text-red-700 dark:text-red-300 mt-1">
                  Your content is too long for:{' '}
                  {platformsExceedingLimit
                    .map(p => PLATFORM_NAMES[p])
                    .join(', ')}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Free Platforms Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
            Free Platforms
          </h4>
          <button
            type="button"
            onClick={selectFree}
            disabled={disabled}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline disabled:opacity-50"
          >
            Select All Free
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {FREE_PLATFORMS.map(platform => (
            <PlatformCard
              key={platform}
              platform={platform}
              isSelected={selectedPlatforms.includes(platform)}
              isConnected={connectedPlatforms.includes(platform)}
              contentLength={contentLength}
              onToggle={() => togglePlatform(platform)}
              disabled={disabled}
            />
          ))}
        </div>
      </div>

      {/* Business Platforms Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
            Business Platforms
          </h4>
          <button
            type="button"
            onClick={selectBusiness}
            disabled={disabled}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline disabled:opacity-50"
          >
            Select All Business
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {BUSINESS_PLATFORMS.map(platform => (
            <PlatformCard
              key={platform}
              platform={platform}
              isSelected={selectedPlatforms.includes(platform)}
              isConnected={connectedPlatforms.includes(platform)}
              contentLength={contentLength}
              onToggle={() => togglePlatform(platform)}
              disabled={disabled}
            />
          ))}
        </div>
      </div>

      {/* Help Text */}
      {connectedCount === 0 && (
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                No platforms connected
              </div>
              <div className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                Go to{' '}
                <a href="/platforms" className="underline font-medium">
                  Platform Settings
                </a>{' '}
                to connect your accounts.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selected Summary */}
      {selectedCount > 0 && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <span className="font-medium">
                {selectedCount} platform{selectedCount !== 1 ? 's' : ''} selected
              </span>
              {contentLength > 0 && (
                <>
                  {' • '}
                  <span>
                    Shortest limit:{' '}
                    {Math.min(
                      ...selectedPlatforms.map(p => getCharacterLimit(p))
                    )}{' '}
                    characters
                  </span>
                </>
              )}
            </div>
            {hasExceedingPlatforms && (
              <div className="text-xs text-red-600 dark:text-red-400 font-medium">
                {platformsExceedingLimit.length} platform
                {platformsExceedingLimit.length !== 1 ? 's' : ''} over limit
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default PlatformSelector;
