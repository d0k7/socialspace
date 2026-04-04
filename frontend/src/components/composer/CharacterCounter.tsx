// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\composer\CharacterCounter.tsx

/**
 * CharacterCounter Component - Visual Character Limit Display
 * 
 * FAANG++++ Standards:
 * - Real-time character counting
 * - Color-coded visual feedback (green → yellow → orange → red)
 * - Progress ring/bar visualization
 * - Per-platform character limits
 * - Warning messages
 * - Accessible with screen reader support
 * - Smooth animations
 * 
 * Features:
 * - Circular progress indicator
 * - Color transitions based on percentage
 * - Platform-specific limit breakdown
 * - Warning badges
 * - Keyboard accessible
 * - Responsive design
 */

import React, { useMemo } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import {
  PlatformType,
  PLATFORM_NAMES,
  PLATFORM_COLORS,
  getCharacterLimit,
  getCharacterCountStatus,
} from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface CharacterCounterProps {
  content: string;
  selectedPlatforms: PlatformType[];
  showDetails?: boolean;
  compact?: boolean;
}

interface PlatformLimitProps {
  platform: PlatformType;
  characterCount: number;
  characterLimit: number;
  compact?: boolean;
}

// ============================================================================
// CIRCULAR PROGRESS COMPONENT
// ============================================================================

interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  status: 'safe' | 'warning' | 'danger';
  children?: React.ReactNode;
}

const CircularProgress: React.FC<CircularProgressProps> = ({
  percentage,
  size = 80,
  strokeWidth = 6,
  status,
  children,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(percentage, 100) / 100) * circumference;

  // Color based on status
  const getColor = () => {
    switch (status) {
      case 'safe':
        return '#10b981'; // green-500
      case 'warning':
        return '#f59e0b'; // amber-500
      case 'danger':
        return '#ef4444'; // red-500
      default:
        return '#6b7280'; // gray-500
    }
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-300 ease-in-out"
        />
      </svg>
      {/* Content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children}
      </div>
    </div>
  );
};

// ============================================================================
// PLATFORM LIMIT DISPLAY
// ============================================================================

const PlatformLimit: React.FC<PlatformLimitProps> = ({
  platform,
  characterCount,
  characterLimit,
  compact = false,
}) => {
  const exceeds = characterCount > characterLimit;
  const percentage = (characterCount / characterLimit) * 100;
  
  let status: 'safe' | 'warning' | 'danger';
  if (exceeds) {
    status = 'danger';
  } else if (percentage >= 95) {
    status = 'danger';
  } else if (percentage >= 80) {
    status = 'warning';
  } else {
    status = 'safe';
  }

  const getStatusIcon = () => {
    if (exceeds) {
      return <XCircle className="w-4 h-4 text-red-500 dark:text-red-400" />;
    } else if (status === 'danger') {
      return <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400" />;
    } else if (status === 'warning') {
      return <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400" />;
    } else {
      return <CheckCircle2 className="w-4 h-4 text-green-500 dark:text-green-400" />;
    }
  };

  const getTextColor = () => {
    if (exceeds) {
      return 'text-red-600 dark:text-red-400';
    } else if (status === 'danger') {
      return 'text-red-600 dark:text-red-400';
    } else if (status === 'warning') {
      return 'text-amber-600 dark:text-amber-400';
    } else {
      return 'text-gray-700 dark:text-gray-300';
    }
  };

  if (compact) {
    return (
      <div className={`flex items-center gap-2 text-sm ${getTextColor()}`}>
        {getStatusIcon()}
        <span className="font-medium">{PLATFORM_NAMES[platform]}</span>
        <span className="font-mono">
          {characterCount}/{characterLimit}
        </span>
        {exceeds && (
          <span className="text-xs">
            (+{characterCount - characterLimit})
          </span>
        )}
      </div>
    );
  }

  return (
    <div
      className={`
        flex items-center justify-between p-3 rounded-lg border
        ${exceeds
          ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          : status === 'danger'
          ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          : status === 'warning'
          ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
          : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
        }
      `}
    >
      <div className="flex items-center gap-2">
        {getStatusIcon()}
        <span
          className="text-sm font-medium"
          style={{ color: PLATFORM_COLORS[platform] }}
        >
          {PLATFORM_NAMES[platform]}
        </span>
      </div>

      <div className={`text-sm font-mono font-semibold ${getTextColor()}`}>
        {characterCount} / {characterLimit}
        {exceeds && (
          <span className="ml-2 text-xs">
            ({characterCount - characterLimit} over)
          </span>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const CharacterCounter: React.FC<CharacterCounterProps> = ({
  content,
  selectedPlatforms,
  showDetails = true,
  compact = false,
}) => {
  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================

  const characterCount = content.length;

  // Get minimum limit from selected platforms
  const minLimit = useMemo(() => {
    if (selectedPlatforms.length === 0) return Infinity;
    return Math.min(...selectedPlatforms.map(p => getCharacterLimit(p)));
  }, [selectedPlatforms]);

  // Get status for overall counter
  const overallStatus = useMemo(() => {
    if (selectedPlatforms.length === 0) {
      return getCharacterCountStatus(characterCount, Infinity);
    }
    return getCharacterCountStatus(characterCount, minLimit);
  }, [characterCount, minLimit, selectedPlatforms]);

  // Platforms exceeding limit
  const platformsExceeding = useMemo(() => {
    return selectedPlatforms.filter(
      platform => characterCount > getCharacterLimit(platform)
    );
  }, [selectedPlatforms, characterCount]);

  // Platforms in warning zone (80-95%)
  const platformsWarning = useMemo(() => {
    return selectedPlatforms.filter(platform => {
      const limit = getCharacterLimit(platform);
      const percentage = (characterCount / limit) * 100;
      return percentage >= 80 && percentage < 95 && characterCount <= limit;
    });
  }, [selectedPlatforms, characterCount]);

  const hasExceeding = platformsExceeding.length > 0;
  const hasWarnings = platformsWarning.length > 0;

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const getStatusMessage = () => {
    if (selectedPlatforms.length === 0) {
      return 'Select platforms to see character limits';
    }

    if (hasExceeding) {
      return `Content exceeds limit for ${platformsExceeding.length} platform${platformsExceeding.length !== 1 ? 's' : ''}`;
    }

    if (hasWarnings) {
      return `Approaching limit for ${platformsWarning.length} platform${platformsWarning.length !== 1 ? 's' : ''}`;
    }

    if (overallStatus.status === 'safe') {
      return 'All platforms within limits';
    }

    return '';
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (selectedPlatforms.length === 0) {
    return (
      <div className="text-center py-6">
        <div className="text-gray-400 dark:text-gray-600 text-sm">
          Select platforms to see character limits
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Main Counter */}
      <div className="flex items-center justify-between mb-4">
        {/* Circular Progress */}
        <div className="flex items-center gap-4">
          <CircularProgress
            percentage={overallStatus.percentage}
            status={overallStatus.status}
            size={compact ? 60 : 80}
            strokeWidth={compact ? 4 : 6}
          >
            <div className="text-center">
              <div
                className={`
                  font-bold font-mono
                  ${compact ? 'text-sm' : 'text-lg'}
                  ${overallStatus.status === 'danger'
                    ? 'text-red-600 dark:text-red-400'
                    : overallStatus.status === 'warning'
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-gray-900 dark:text-gray-100'
                  }
                `}
              >
                {characterCount}
              </div>
              {!compact && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  / {minLimit}
                </div>
              )}
            </div>
          </CircularProgress>

          {/* Status Text */}
          <div>
            <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {characterCount.toLocaleString()} characters
            </div>
            <div
              className={`
                text-sm
                ${hasExceeding
                  ? 'text-red-600 dark:text-red-400 font-medium'
                  : hasWarnings
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-gray-600 dark:text-gray-400'
                }
              `}
            >
              {getStatusMessage()}
            </div>
          </div>
        </div>

        {/* Overall Status Badge */}
        {hasExceeding && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full text-sm font-medium">
            <AlertCircle className="w-4 h-4" />
            <span>Over limit</span>
          </div>
        )}
        {!hasExceeding && hasWarnings && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-sm font-medium">
            <AlertTriangle className="w-4 h-4" />
            <span>Near limit</span>
          </div>
        )}
        {!hasExceeding && !hasWarnings && characterCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm font-medium">
            <CheckCircle2 className="w-4 h-4" />
            <span>Good to go</span>
          </div>
        )}
      </div>

      {/* Platform-Specific Limits */}
      {showDetails && selectedPlatforms.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Per-Platform Limits
          </div>

          {/* Show exceeding platforms first */}
          {platformsExceeding.map(platform => (
            <PlatformLimit
              key={platform}
              platform={platform}
              characterCount={characterCount}
              characterLimit={getCharacterLimit(platform)}
              compact={compact}
            />
          ))}

          {/* Then warning platforms */}
          {platformsWarning.map(platform => (
            <PlatformLimit
              key={platform}
              platform={platform}
              characterCount={characterCount}
              characterLimit={getCharacterLimit(platform)}
              compact={compact}
            />
          ))}

          {/* Then safe platforms (collapsed) */}
          {!compact && (
            <details className="group">
              <summary className="cursor-pointer text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                <span className="inline-flex items-center gap-2">
                  <span className="transform group-open:rotate-90 transition-transform">
                    ▶
                  </span>
                  <span>
                    Show all platforms ({selectedPlatforms.length - platformsExceeding.length - platformsWarning.length} within limits)
                  </span>
                </span>
              </summary>

              <div className="mt-2 space-y-2">
                {selectedPlatforms
                  .filter(
                    platform =>
                      !platformsExceeding.includes(platform) &&
                      !platformsWarning.includes(platform)
                  )
                  .map(platform => (
                    <PlatformLimit
                      key={platform}
                      platform={platform}
                      characterCount={characterCount}
                      characterLimit={getCharacterLimit(platform)}
                      compact={compact}
                    />
                  ))}
              </div>
            </details>
          )}
        </div>
      )}

      {/* Help Text */}
      {hasExceeding && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-900 dark:text-red-100">
              <p className="font-medium">Content too long</p>
              <p className="text-xs text-red-700 dark:text-red-300 mt-1">
                Your post exceeds the character limit for{' '}
                {platformsExceeding.map(p => PLATFORM_NAMES[p]).join(', ')}.
                Please shorten your content or deselect these platforms.
              </p>
            </div>
          </div>
        </div>
      )}

      {!hasExceeding && hasWarnings && (
        <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-900 dark:text-amber-100">
              <p className="font-medium">Approaching character limit</p>
              <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                You're near the limit for{' '}
                {platformsWarning.map(p => PLATFORM_NAMES[p]).join(', ')}.
                Consider keeping it shorter for better engagement.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Accessibility - Screen reader only */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {characterCount} characters. {getStatusMessage()}.
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default CharacterCounter;