// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\pages\Dashboard\DashboardPage.tsx

/**
 * DashboardPage - Main Dashboard with Stats & Overview
 * 
 * FAANG++++ Standards:
 * - Real-time statistics
 * - Recent posts timeline
 * - Upcoming scheduled posts
 * - Quick actions
 * - Platform health indicators
 * - Analytics preview
 * - Loading states
 * - Error handling
 * - Dark mode support
 * - Responsive design
 * 
 * Features:
 * - Stats cards (posts, engagement, reach, followers)
 * - Recent activity feed
 * - Scheduled posts calendar
 * - Quick compose button
 * - Platform status badges
 * - Performance trends
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  TrendingUp,
  Users,
  Eye,
  Heart,
  MessageSquare,
  Share2,
  Plus,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  BarChart3,
  Loader2,
} from 'lucide-react';
import api from '../../lib/api';
import { useToast } from '../../components/common/Toast';

// ============================================================================
// INTERFACES
// ============================================================================

interface DashboardStats {
  totalPosts: number;
  totalEngagement: number;
  totalReach: number;
  totalFollowers: number;
  trends: {
    posts: number;
    engagement: number;
    reach: number;
    followers: number;
  };
}

interface RecentPost {
  id: string;
  content: string;
  platforms: string[];
  publishedAt: string;
  stats: {
    likes: number;
    comments: number;
    shares: number;
    reach: number;
  };
}

interface ScheduledPost {
  id: string;
  content: string;
  platforms: string[];
  scheduledFor: string;
  status: 'pending' | 'processing' | 'failed';
}

interface PlatformHealth {
  platform: string;
  status: 'connected' | 'disconnected' | 'warning';
  lastSync: string;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();

  // ============================================================================
  // STATE
  // ============================================================================

  const [stats, setStats] = useState<DashboardStats>({
    totalPosts: 0,
    totalEngagement: 0,
    totalReach: 0,
    totalFollowers: 0,
    trends: { posts: 0, engagement: 0, reach: 0, followers: 0 },
  });

  const [recentPosts, setRecentPosts] = useState<RecentPost[]>([]);
  const [scheduledPosts, setScheduledPosts] = useState<ScheduledPost[]>([]);
  const [platformHealth, setPlatformHealth] = useState<PlatformHealth[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // FETCH DATA
  // ============================================================================

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // In production, these would be real API calls
      // For now, using mock data
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock data
      setStats({
        totalPosts: 247,
        totalEngagement: 15420,
        totalReach: 89340,
        totalFollowers: 12850,
        trends: {
          posts: 12.5,
          engagement: 8.3,
          reach: 15.7,
          followers: 5.2,
        },
      });

      setRecentPosts([
        {
          id: '1',
          content: 'Just launched our new product line! 🚀 Check it out and let us know what you think.',
          platforms: ['Twitter', 'LinkedIn', 'Facebook'],
          publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          stats: { likes: 324, comments: 45, shares: 67, reach: 5420 },
        },
        {
          id: '2',
          content: 'Behind the scenes at our office today. Great team, great energy! 💪',
          platforms: ['Instagram', 'Twitter'],
          publishedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          stats: { likes: 189, comments: 23, shares: 12, reach: 2340 },
        },
        {
          id: '3',
          content: 'New blog post: 10 tips for social media success in 2026',
          platforms: ['LinkedIn', 'Twitter'],
          publishedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          stats: { likes: 445, comments: 78, shares: 123, reach: 8930 },
        },
      ]);

      setScheduledPosts([
        {
          id: '1',
          content: 'Weekend vibes! What are your plans? 🌟',
          platforms: ['Instagram', 'Facebook'],
          scheduledFor: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
          status: 'pending',
        },
        {
          id: '2',
          content: 'Announcing our Q2 results - record breaking quarter!',
          platforms: ['LinkedIn', 'Twitter'],
          scheduledFor: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          status: 'pending',
        },
      ]);

      setPlatformHealth([
        { platform: 'Twitter', status: 'connected', lastSync: '2 mins ago' },
        { platform: 'Instagram', status: 'connected', lastSync: '5 mins ago' },
        { platform: 'LinkedIn', status: 'connected', lastSync: '1 hour ago' },
        { platform: 'Facebook', status: 'warning', lastSync: '3 hours ago' },
        { platform: 'TikTok', status: 'disconnected', lastSync: 'Never' },
      ]);

    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // HELPERS
  // ============================================================================

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTimeAgo = (date: string): string => {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const formatScheduledTime = (date: string): string => {
    const scheduledDate = new Date(date);
    const now = new Date();
    const diffMs = scheduledDate.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffHours < 24) return `in ${diffHours}h`;
    const diffDays = Math.floor(diffMs / 86400000);
    return `in ${diffDays}d`;
  };

  // ============================================================================
  // LOADING STATE
  // ============================================================================

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // ERROR STATE
  // ============================================================================

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 max-w-md">
          <AlertCircle className="w-12 h-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 text-center">
            Failed to load dashboard
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 text-center">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Welcome back! Here's what's happening with your social media.
            </p>
          </div>
          <button
            onClick={() => navigate('/compose')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            <Plus className="w-5 h-5" />
            <span>Create Post</span>
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Posts */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              {stats.trends.posts > 0 ? (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <ArrowUpRight className="w-4 h-4" />
                  <span>{stats.trends.posts}%</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-red-600 dark:text-red-400 text-sm">
                  <ArrowDownRight className="w-4 h-4" />
                  <span>{Math.abs(stats.trends.posts)}%</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(stats.totalPosts)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Posts</div>
          </div>

          {/* Total Engagement */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              {stats.trends.engagement > 0 ? (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <ArrowUpRight className="w-4 h-4" />
                  <span>{stats.trends.engagement}%</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-red-600 dark:text-red-400 text-sm">
                  <ArrowDownRight className="w-4 h-4" />
                  <span>{Math.abs(stats.trends.engagement)}%</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(stats.totalEngagement)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Engagement</div>
          </div>

          {/* Total Reach */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Eye className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              {stats.trends.reach > 0 ? (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <ArrowUpRight className="w-4 h-4" />
                  <span>{stats.trends.reach}%</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-red-600 dark:text-red-400 text-sm">
                  <ArrowDownRight className="w-4 h-4" />
                  <span>{Math.abs(stats.trends.reach)}%</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(stats.totalReach)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Reach</div>
          </div>

          {/* Total Followers */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Users className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              {stats.trends.followers > 0 ? (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <ArrowUpRight className="w-4 h-4" />
                  <span>{stats.trends.followers}%</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-red-600 dark:text-red-400 text-sm">
                  <ArrowDownRight className="w-4 h-4" />
                  <span>{Math.abs(stats.trends.followers)}%</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(stats.totalFollowers)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Followers</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Posts - 2 columns */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Recent Posts
                </h2>
                <button
                  onClick={() => navigate('/analytics')}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                >
                  <span>View All</span>
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                {recentPosts.map((post) => (
                  <div
                    key={post.id}
                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
                  >
                    <p className="text-gray-900 dark:text-gray-100 mb-3 line-clamp-2">
                      {post.content}
                    </p>

                    {/* Platforms */}
                    <div className="flex items-center gap-2 mb-3">
                      {post.platforms.map((platform) => (
                        <span
                          key={platform}
                          className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                        >
                          {platform}
                        </span>
                      ))}
                      <span className="text-xs text-gray-500 dark:text-gray-400 ml-auto">
                        {formatTimeAgo(post.publishedAt)}
                      </span>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-1">
                        <Heart className="w-4 h-4" />
                        <span>{formatNumber(post.stats.likes)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MessageSquare className="w-4 h-4" />
                        <span>{formatNumber(post.stats.comments)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Share2 className="w-4 h-4" />
                        <span>{formatNumber(post.stats.shares)}</span>
                      </div>
                      <div className="flex items-center gap-1 ml-auto">
                        <Eye className="w-4 h-4" />
                        <span>{formatNumber(post.stats.reach)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar - 1 column */}
          <div className="space-y-6">
            {/* Scheduled Posts */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  Scheduled Posts
                </h3>
                <Calendar className="w-5 h-5 text-gray-400" />
              </div>

              <div className="space-y-3">
                {scheduledPosts.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                    No scheduled posts
                  </p>
                ) : (
                  scheduledPosts.map((post) => (
                    <div
                      key={post.id}
                      className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                    >
                      <p className="text-sm text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
                        {post.content}
                      </p>
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                          <Clock className="w-3 h-3" />
                          <span>{formatScheduledTime(post.scheduledFor)}</span>
                        </div>
                        {post.status === 'pending' && (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <button
                onClick={() => navigate('/compose')}
                className="w-full mt-4 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Schedule New Post
              </button>
            </div>

            {/* Platform Health */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  Platform Status
                </h3>
                <Zap className="w-5 h-5 text-gray-400" />
              </div>

              <div className="space-y-3">
                {platformHealth.map((platform) => (
                  <div
                    key={platform.platform}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          platform.status === 'connected'
                            ? 'bg-green-500'
                            : platform.status === 'warning'
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                      />
                      <span className="text-sm text-gray-900 dark:text-gray-100">
                        {platform.platform}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {platform.lastSync}
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => navigate('/platforms')}
                className="w-full mt-4 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Manage Platforms
              </button>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-6 text-white">
              <h3 className="font-semibold mb-2">Ready to grow?</h3>
              <p className="text-sm text-blue-100 mb-4">
                Check out your analytics to see what's working
              </p>
              <button
                onClick={() => navigate('/analytics')}
                className="w-full px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium flex items-center justify-center gap-2"
              >
                <BarChart3 className="w-4 h-4" />
                <span>View Analytics</span>
              </button>
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

export default DashboardPage;