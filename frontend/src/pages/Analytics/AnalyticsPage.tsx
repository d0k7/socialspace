// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\pages\Analytics\AnalyticsPage.tsx

/**
 * AnalyticsPage - Main Analytics Dashboard
 * 
 * FAANG++++ Standards:
 * - Comprehensive analytics dashboard
 * - Multi-component integration
 * - API data fetching with error handling
 * - State management
 * - Export functionality (CSV/PDF)
 * - Responsive layout
 * - Loading states
 * - Empty states
 * - Dark mode support
 * 
 * Features:
 * - Overview stats
 * - Engagement charts
 * - Platform breakdown
 * - Top posts
 * - Follower growth
 * - Date range filtering
 * - Platform filtering
 * - Export analytics
 * - Refresh data
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Download,
  RefreshCw,
  Filter,
  TrendingUp,
  Users,
  FileText,
  Eye,
  AlertCircle,
  Loader2,
  CheckCircle2,
} from 'lucide-react';

// Components
import EngagementChart from '../../components/analytics/EngagementChart';
import PlatformBreakdown from '../../components/analytics/PlatformBreakdown';
import TopPosts from '../../components/analytics/TopPosts';
import GrowthMetrics from '../../components/analytics/GrowthMetrics';
import DateRangePicker from '../../components/analytics/DateRangePicker';

// Types
import {
  GetAnalyticsRequest,
  GetAnalyticsResponse,
  ExportAnalyticsRequest,
  DateRange,
  TimePeriod,
  OverviewStats,
  formatNumber,
  formatPercentage,
  getDateRangeForPeriod,
} from '../../types/analytics.types';
import { PlatformType, PLATFORMS, PLATFORM_NAMES } from '../../types/composer.types';

// API
import api from '../../api/client';

// ============================================================================
// INTERFACES
// ============================================================================

interface AnalyticsPageProps {
  // Optional: pre-selected filters
  initialDateRange?: DateRange;
  initialPlatforms?: PlatformType[];
}

// ============================================================================
// COMPONENT
// ============================================================================

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({
  initialDateRange = getDateRangeForPeriod('30d'),
  initialPlatforms = [],
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  // Filters
  const [dateRange, setDateRange] = useState<DateRange>(initialDateRange);
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('30d');
  const [selectedPlatforms, setSelectedPlatforms] = useState<PlatformType[]>(initialPlatforms);
  const [showPlatformFilter, setShowPlatformFilter] = useState(false);

  // Data
  const [analyticsData, setAnalyticsData] = useState<GetAnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Export
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  // ============================================================================
  // FETCH DATA
  // ============================================================================

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const request: GetAnalyticsRequest = {
        startDate: dateRange.startDate.toISOString(),
        endDate: dateRange.endDate.toISOString(),
        platforms: selectedPlatforms.length > 0 ? selectedPlatforms : undefined,
        timePeriod: selectedPeriod,
      };

      const response = await api.get('/analytics', { params: request });
      const data: GetAnalyticsResponse = response.data;

      setAnalyticsData(data);
    } catch (err: any) {
      console.error('Failed to fetch analytics:', err);
      setError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to load analytics data. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [dateRange, selectedPlatforms, selectedPeriod]);

  // Load data on mount and when filters change
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // ============================================================================
  // EXPORT HANDLER
  // ============================================================================

  const handleExport = async (format: 'csv' | 'pdf') => {
    setIsExporting(true);
    setExportSuccess(false);

    try {
      const request: ExportAnalyticsRequest = {
        format,
        startDate: dateRange.startDate.toISOString(),
        endDate: dateRange.endDate.toISOString(),
        platforms: selectedPlatforms.length > 0 ? selectedPlatforms : undefined,
        includeCharts: format === 'pdf',
      };

      const response = await api.post('/analytics/export', request);
      const { downloadUrl } = response.data;

      // Trigger download
      window.open(downloadUrl, '_blank');

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (err: any) {
      console.error('Export failed:', err);
      alert('Failed to export analytics. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // ============================================================================
  // PLATFORM FILTER HANDLER
  // ============================================================================

  const togglePlatform = (platform: PlatformType) => {
    setSelectedPlatforms(prev => {
      if (prev.includes(platform)) {
        return prev.filter(p => p !== platform);
      } else {
        return [...prev, platform];
      }
    });
  };

  const clearPlatformFilter = () => {
    setSelectedPlatforms([]);
  };

  // ============================================================================
  // LOADING STATE
  // ============================================================================

  if (isLoading && !analyticsData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Loading analytics...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // ERROR STATE
  // ============================================================================

  if (error && !analyticsData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Failed to load analytics
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {error}
              </p>
              <button
                type="button"
                onClick={fetchAnalytics}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // EMPTY STATE
  // ============================================================================

  if (!analyticsData || analyticsData.overview.totalPosts === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                No analytics data yet
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Start posting content to see your analytics and insights
              </p>
              <a
                href="/compose"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <FileText className="w-4 h-4" />
                <span>Create Your First Post</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  const overview = analyticsData.overview;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Title */}
            <div className="flex items-center gap-3">
              <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Analytics
              </h1>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              {/* Date Range Picker */}
              <DateRangePicker
                value={dateRange}
                onChange={setDateRange}
                onPeriodChange={setSelectedPeriod}
              />

              {/* Platform Filter */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowPlatformFilter(!showPlatformFilter)}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors
                    ${selectedPlatforms.length > 0
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }
                  `}
                >
                  <Filter className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Platforms
                    {selectedPlatforms.length > 0 && ` (${selectedPlatforms.length})`}
                  </span>
                </button>

                {/* Platform Filter Dropdown */}
                {showPlatformFilter && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowPlatformFilter(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-20 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                          Filter by Platform
                        </h4>
                        {selectedPlatforms.length > 0 && (
                          <button
                            type="button"
                            onClick={clearPlatformFilter}
                            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                          >
                            Clear
                          </button>
                        )}
                      </div>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {PLATFORMS.map(platform => (
                          <label
                            key={platform}
                            className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded transition-colors"
                          >
                            <input
                              type="checkbox"
                              checked={selectedPlatforms.includes(platform)}
                              onChange={() => togglePlatform(platform)}
                              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-900 dark:text-gray-100">
                              {PLATFORM_NAMES[platform]}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Refresh */}
              <button
                type="button"
                onClick={fetchAnalytics}
                disabled={isLoading}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                title="Refresh data"
              >
                <RefreshCw className={`w-4 h-4 text-gray-700 dark:text-gray-300 ${isLoading ? 'animate-spin' : ''}`} />
              </button>

              {/* Export */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => handleExport('csv')}
                  disabled={isExporting}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
                >
                  {isExporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : exportSuccess ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  <span className="hidden sm:inline">
                    {isExporting ? 'Exporting...' : exportSuccess ? 'Exported!' : 'Export'}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Posts */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              {overview.trends.posts === 'up' && (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <TrendingUp className="w-4 h-4" />
                  <span>+{formatPercentage(overview.changes.posts, 0)}</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(overview.totalPosts)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Posts
            </div>
          </div>

          {/* Total Engagement */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              {overview.trends.engagement === 'up' && (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <TrendingUp className="w-4 h-4" />
                  <span>+{formatPercentage(overview.changes.engagement, 0)}</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(overview.totalEngagement)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Engagement
            </div>
          </div>

          {/* Total Reach */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Eye className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              {overview.trends.reach === 'up' && (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <TrendingUp className="w-4 h-4" />
                  <span>+{formatPercentage(overview.changes.reach, 0)}</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(overview.totalReach)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Reach
            </div>
          </div>

          {/* Total Followers */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Users className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              {overview.trends.followers === 'up' && (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                  <TrendingUp className="w-4 h-4" />
                  <span>+{formatPercentage(overview.changes.followers, 0)}</span>
                </div>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {formatNumber(overview.totalFollowers)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total Followers
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Engagement Chart (2 cols) */}
          <div className="lg:col-span-2">
            <EngagementChart
              data={analyticsData.engagementOverTime.data}
              platforms={selectedPlatforms.length > 0 ? selectedPlatforms : undefined}
              loading={isLoading}
            />
          </div>

          {/* Platform Breakdown (1 col) */}
          <div>
            <PlatformBreakdown
              data={analyticsData.platformAnalytics}
              loading={isLoading}
            />
          </div>
        </div>

        {/* Top Posts */}
        <div className="mb-8">
          <TopPosts
            posts={analyticsData.contentPerformance.topPosts}
            loading={isLoading}
          />
        </div>

        {/* Follower Growth */}
        <div>
          <GrowthMetrics
            audienceInsights={analyticsData.audienceInsights}
            loading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default AnalyticsPage;
