// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\analytics\TopPosts.tsx

/**
 * TopPosts Component - Best Performing Content
 * 
 * FAANG++++ Standards:
 * - Display top performing posts
 * - Sortable by different metrics
 * - Post preview with thumbnails
 * - Engagement breakdown
 * - Platform indicators
 * - Click to view details
 * - Pagination support
 * - Loading and empty states
 * - Dark mode support
 * 
 * Features:
 * - Post content preview
 * - Media thumbnails
 * - Engagement metrics (likes, comments, shares, etc.)
 * - Platform badges
 * - Sort by metric
 * - Engagement rate calculation
 * - Published date
 * - View full post link
 */

import React, { useState, useMemo } from 'react';
import {
  Heart,
  MessageCircle,
  Share2,
  Eye,
  MousePointer,
  Bookmark,
  TrendingUp,
  Calendar,
  ExternalLink,
  ChevronDown,
  Award,
  BarChart3,
} from 'lucide-react';
import {
  PostAnalytics,
  formatNumber,
  formatPercentage,
  formatDateForDisplay,
} from '../../types/analytics.types';
import { PlatformType, PLATFORM_COLORS, PLATFORM_NAMES } from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface TopPostsProps {
  posts: PostAnalytics[];
  maxPosts?: number;
  sortBy?: keyof PostAnalytics['metrics'] | 'totalEngagement' | 'engagementRate';
  showMetrics?: (keyof PostAnalytics['metrics'])[];
  onPostClick?: (post: PostAnalytics) => void;
  loading?: boolean;
}

interface MetricDisplayProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}

// ============================================================================
// SORT OPTIONS
// ============================================================================

const SORT_OPTIONS = [
  { value: 'totalEngagement', label: 'Total Engagement' },
  { value: 'engagementRate', label: 'Engagement Rate' },
  { value: 'likes', label: 'Likes' },
  { value: 'comments', label: 'Comments' },
  { value: 'shares', label: 'Shares' },
  { value: 'views', label: 'Views' },
  { value: 'clicks', label: 'Clicks' },
  { value: 'saves', label: 'Saves' },
];

// ============================================================================
// METRIC DISPLAY COMPONENT
// ============================================================================

const MetricDisplay: React.FC<MetricDisplayProps> = ({ icon, label, value, color }) => (
  <div className="flex items-center gap-2">
    <div className={`${color}`}>
      {icon}
    </div>
    <div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        {formatNumber(value)}
      </div>
    </div>
  </div>
);

// ============================================================================
// POST CARD COMPONENT
// ============================================================================

interface PostCardProps {
  post: PostAnalytics;
  rank: number;
  onClick?: () => void;
}

const PostCard: React.FC<PostCardProps> = ({ post, rank, onClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const truncatedContent = useMemo(() => {
    if (post.content.length <= 150) return post.content;
    return post.content.substring(0, 150) + '...';
  }, [post.content]);

  const shouldShowExpand = post.content.length > 150;

  return (
    <div
      className={`
        bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4
        hover:shadow-lg transition-all duration-200
        ${onClick ? 'cursor-pointer' : ''}
      `}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Rank Badge */}
          <div
            className={`
              w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
              ${rank === 1
                ? 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white'
                : rank === 2
                ? 'bg-gradient-to-br from-gray-300 to-gray-500 text-white'
                : rank === 3
                ? 'bg-gradient-to-br from-orange-400 to-orange-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }
            `}
          >
            {rank <= 3 ? <Award className="w-4 h-4" /> : rank}
          </div>

          {/* Platform Badges */}
          <div className="flex flex-wrap gap-1">
            {post.platforms.map(platform => (
              <div
                key={platform}
                className="px-2 py-1 rounded text-xs font-medium text-white"
                style={{ backgroundColor: PLATFORM_COLORS[platform] }}
              >
                {PLATFORM_NAMES[platform]}
              </div>
            ))}
          </div>
        </div>

        {/* Published Date */}
        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
          <Calendar className="w-3 h-3" />
          <span>{formatDateForDisplay(post.publishedAt)}</span>
        </div>
      </div>

      {/* Content & Media */}
      <div className="mb-4">
        <div className="flex gap-4">
          {/* Media Thumbnail */}
          {post.mediaUrls && post.mediaUrls.length > 0 && (
            <div className="flex-shrink-0">
              <img
                src={post.mediaUrls[0]}
                alt="Post media"
                className="w-20 h-20 rounded-lg object-cover"
              />
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {isExpanded ? post.content : truncatedContent}
            </p>
            {shouldShowExpand && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className="mt-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                {isExpanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        <MetricDisplay
          icon={<Heart className="w-4 h-4" />}
          label="Likes"
          value={post.metrics.likes}
          color="text-red-500"
        />
        <MetricDisplay
          icon={<MessageCircle className="w-4 h-4" />}
          label="Comments"
          value={post.metrics.comments}
          color="text-blue-500"
        />
        <MetricDisplay
          icon={<Share2 className="w-4 h-4" />}
          label="Shares"
          value={post.metrics.shares}
          color="text-green-500"
        />
        <MetricDisplay
          icon={<Eye className="w-4 h-4" />}
          label="Views"
          value={post.metrics.views}
          color="text-purple-500"
        />
        <MetricDisplay
          icon={<MousePointer className="w-4 h-4" />}
          label="Clicks"
          value={post.metrics.clicks}
          color="text-orange-500"
        />
        <MetricDisplay
          icon={<Bookmark className="w-4 h-4" />}
          label="Saves"
          value={post.metrics.saves}
          color="text-pink-500"
        />
      </div>

      {/* Footer Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Total Engagement */}
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Total Engagement
              </div>
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {formatNumber(post.totalEngagement)}
              </div>
            </div>
          </div>

          {/* Engagement Rate */}
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Engagement Rate
              </div>
              <div className="text-sm font-semibold text-green-600 dark:text-green-400">
                {formatPercentage(post.engagementRate)}
              </div>
            </div>
          </div>
        </div>

        {/* View Post Link */}
        {post.link && (
          <a
            href={post.link}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            <span>View Post</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENT
// ============================================================================

export const TopPosts: React.FC<TopPostsProps> = ({
  posts,
  maxPosts = 10,
  sortBy = 'totalEngagement',
  showMetrics = ['likes', 'comments', 'shares', 'views', 'clicks', 'saves'],
  onPostClick,
  loading = false,
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [currentSortBy, setCurrentSortBy] = useState<string>(sortBy);
  const [showSortMenu, setShowSortMenu] = useState(false);

  // ============================================================================
  // SORT POSTS
  // ============================================================================

  const sortedPosts = useMemo(() => {
    if (!posts || posts.length === 0) return [];

    const sorted = [...posts].sort((a, b) => {
      let aValue: number;
      let bValue: number;

      if (currentSortBy === 'totalEngagement') {
        aValue = a.totalEngagement;
        bValue = b.totalEngagement;
      } else if (currentSortBy === 'engagementRate') {
        aValue = a.engagementRate;
        bValue = b.engagementRate;
      } else {
        aValue = a.metrics[currentSortBy as keyof typeof a.metrics];
        bValue = b.metrics[currentSortBy as keyof typeof b.metrics];
      }

      return bValue - aValue; // Descending order
    });

    return sorted.slice(0, maxPosts);
  }, [posts, currentSortBy, maxPosts]);

  // ============================================================================
  // CALCULATE STATS
  // ============================================================================

  const stats = useMemo(() => {
    if (sortedPosts.length === 0) {
      return {
        avgEngagement: 0,
        avgEngagementRate: 0,
        totalPosts: 0,
      };
    }

    const totalEngagement = sortedPosts.reduce(
      (sum, post) => sum + post.totalEngagement,
      0
    );
    const totalEngagementRate = sortedPosts.reduce(
      (sum, post) => sum + post.engagementRate,
      0
    );

    return {
      avgEngagement: totalEngagement / sortedPosts.length,
      avgEngagementRate: totalEngagementRate / sortedPosts.length,
      totalPosts: sortedPosts.length,
    };
  }, [sortedPosts]);

  // ============================================================================
  // LOADING STATE
  // ============================================================================

  if (loading) {
    return (
      <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  // ============================================================================
  // EMPTY STATE
  // ============================================================================

  if (!sortedPosts || sortedPosts.length === 0) {
    return (
      <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="text-center py-12">
          <Award className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No posts yet
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Start posting to see your top performing content
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
            Top Performing Posts
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">Posts:</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {stats.totalPosts}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">Avg Engagement:</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {formatNumber(stats.avgEngagement)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">Avg Rate:</span>
              <span className="font-semibold text-green-600 dark:text-green-400">
                {formatPercentage(stats.avgEngagementRate)}
              </span>
            </div>
          </div>
        </div>

        {/* Sort Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowSortMenu(!showSortMenu)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Sort by: {SORT_OPTIONS.find(opt => opt.value === currentSortBy)?.label}
            </span>
            <ChevronDown className="w-4 h-4 text-gray-500" />
          </button>

          {/* Dropdown Menu */}
          {showSortMenu && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowSortMenu(false)}
              />

              {/* Menu */}
              <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20">
                {SORT_OPTIONS.map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      setCurrentSortBy(option.value);
                      setShowSortMenu(false);
                    }}
                    className={`
                      w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors
                      ${currentSortBy === option.value
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium'
                        : 'text-gray-700 dark:text-gray-300'
                      }
                      ${option === SORT_OPTIONS[0] ? 'rounded-t-lg' : ''}
                      ${option === SORT_OPTIONS[SORT_OPTIONS.length - 1] ? 'rounded-b-lg' : ''}
                    `}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Posts List */}
      <div className="space-y-4">
        {sortedPosts.map((post, index) => (
          <PostCard
            key={post.postId}
            post={post}
            rank={index + 1}
            onClick={onPostClick ? () => onPostClick(post) : undefined}
          />
        ))}
      </div>

      {/* Footer Tip */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900 dark:text-blue-100">
            <p className="font-medium">💡 Pro Tip</p>
            <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
              Analyze your top posts to identify patterns in content type, posting time,
              and platform performance. Replicate what works!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default TopPosts;
