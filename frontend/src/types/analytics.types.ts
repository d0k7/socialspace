// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\types\analytics.types.ts

/**
 * Analytics Type Definitions
 * 
 * FAANG++++ Standards:
 * - Comprehensive type coverage
 * - API response types
 * - Chart data structures
 * - Metric calculations
 * - Export formats
 */

import { PlatformType } from './composer.types';

// ============================================================================
// TIME PERIODS
// ============================================================================

export type TimePeriod = '7d' | '30d' | '90d' | '1y' | 'all' | 'custom';

export interface DateRange {
  startDate: Date;
  endDate: Date;
}

export const TIME_PERIOD_LABELS: Record<TimePeriod, string> = {
  '7d': 'Last 7 days',
  '30d': 'Last 30 days',
  '90d': 'Last 90 days',
  '1y': 'Last year',
  'all': 'All time',
  'custom': 'Custom range',
};

// ============================================================================
// ENGAGEMENT METRICS
// ============================================================================

export interface EngagementMetrics {
  likes: number;
  comments: number;
  shares: number;
  views: number;
  clicks: number;
  saves: number;
}

export interface EngagementRate {
  rate: number; // Percentage
  trend: 'up' | 'down' | 'stable';
  change: number; // Percentage change from previous period
}

// ============================================================================
// PLATFORM ANALYTICS
// ============================================================================

export interface PlatformAnalytics {
  platform: PlatformType;
  totalPosts: number;
  totalEngagement: number;
  averageEngagement: number;
  engagementRate: number;
  followers: number;
  followerGrowth: number; // Percentage
  metrics: EngagementMetrics;
  topPost?: PostAnalytics;
}

// ============================================================================
// POST ANALYTICS
// ============================================================================

export interface PostAnalytics {
  postId: string;
  content: string;
  platforms: PlatformType[];
  publishedAt: string; // ISO 8601
  metrics: EngagementMetrics;
  totalEngagement: number;
  engagementRate: number;
  mediaUrls?: string[];
  link?: string;
}

// ============================================================================
// TIME SERIES DATA
// ============================================================================

export interface TimeSeriesDataPoint {
  date: string; // ISO 8601 or formatted date
  value: number;
  platform?: PlatformType;
  metric?: keyof EngagementMetrics;
}

export interface EngagementOverTime {
  data: TimeSeriesDataPoint[];
  total: number;
  average: number;
  peak: TimeSeriesDataPoint;
  trend: 'up' | 'down' | 'stable';
}

// ============================================================================
// FOLLOWER ANALYTICS
// ============================================================================

export interface FollowerGrowth {
  platform: PlatformType;
  current: number;
  previous: number;
  growth: number; // Absolute change
  growthRate: number; // Percentage
  data: TimeSeriesDataPoint[];
}

export interface AudienceInsights {
  totalFollowers: number;
  totalGrowth: number;
  growthRate: number;
  platforms: FollowerGrowth[];
}

// ============================================================================
// CONTENT PERFORMANCE
// ============================================================================

export interface ContentPerformance {
  topPosts: PostAnalytics[];
  averageEngagement: number;
  totalPosts: number;
  totalEngagement: number;
  bestPerformingPlatform: PlatformType;
  bestPerformingTime: {
    hour: number; // 0-23
    dayOfWeek: number; // 0-6 (0 = Sunday)
  };
}

// ============================================================================
// OVERVIEW STATS
// ============================================================================

export interface OverviewStats {
  totalPosts: number;
  totalEngagement: number;
  totalReach: number;
  averageEngagementRate: number;
  activePlatforms: number;
  totalFollowers: number;
  trends: {
    posts: 'up' | 'down' | 'stable';
    engagement: 'up' | 'down' | 'stable';
    reach: 'up' | 'down' | 'stable';
    followers: 'up' | 'down' | 'stable';
  };
  changes: {
    posts: number; // Percentage
    engagement: number;
    reach: number;
    followers: number;
  };
}

// ============================================================================
// API REQUEST/RESPONSE TYPES
// ============================================================================

export interface GetAnalyticsRequest {
  startDate?: string; // ISO 8601
  endDate?: string; // ISO 8601
  platforms?: PlatformType[];
  timePeriod?: TimePeriod;
}

export interface GetAnalyticsResponse {
  overview: OverviewStats;
  platformAnalytics: PlatformAnalytics[];
  engagementOverTime: EngagementOverTime;
  contentPerformance: ContentPerformance;
  audienceInsights: AudienceInsights;
  generatedAt: string; // ISO 8601
}

export interface ExportAnalyticsRequest {
  format: 'csv' | 'pdf' | 'json';
  startDate?: string;
  endDate?: string;
  platforms?: PlatformType[];
  includeCharts?: boolean;
}

export interface ExportAnalyticsResponse {
  downloadUrl: string;
  expiresAt: string; // ISO 8601
  fileSize: number; // bytes
  format: 'csv' | 'pdf' | 'json';
}

// ============================================================================
// CHART DATA TYPES
// ============================================================================

export interface LineChartData {
  name: string; // X-axis label (date)
  [key: string]: number | string; // Dynamic keys for each metric/platform
}

export interface PieChartData {
  name: string; // Platform name
  value: number;
  color: string;
  percentage: number;
}

export interface BarChartData {
  name: string; // Category name
  value: number;
  color?: string;
}

// ============================================================================
// COMPARISON DATA
// ============================================================================

export interface ComparisonData {
  current: number;
  previous: number;
  change: number; // Absolute change
  changePercentage: number;
  trend: 'up' | 'down' | 'stable';
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Calculate engagement rate
 */
export const calculateEngagementRate = (
  engagement: number,
  reach: number
): number => {
  if (reach === 0) return 0;
  return (engagement / reach) * 100;
};

/**
 * Calculate total engagement
 */
export const calculateTotalEngagement = (
  metrics: EngagementMetrics
): number => {
  return (
    metrics.likes +
    metrics.comments +
    metrics.shares +
    metrics.clicks +
    metrics.saves
  );
};

/**
 * Determine trend direction
 */
export const determineTrend = (
  current: number,
  previous: number
): 'up' | 'down' | 'stable' => {
  const threshold = 0.05; // 5% threshold for "stable"
  const change = ((current - previous) / previous) * 100;

  if (Math.abs(change) < threshold) return 'stable';
  return change > 0 ? 'up' : 'down';
};

/**
 * Format number with K/M suffix
 */
export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

/**
 * Format percentage
 */
export const formatPercentage = (num: number, decimals: number = 1): string => {
  return num.toFixed(decimals) + '%';
};

/**
 * Calculate percentage change
 */
export const calculatePercentageChange = (
  current: number,
  previous: number
): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

/**
 * Get date range for time period
 */
export const getDateRangeForPeriod = (period: TimePeriod): DateRange => {
  const endDate = new Date();
  const startDate = new Date();

  switch (period) {
    case '7d':
      startDate.setDate(endDate.getDate() - 7);
      break;
    case '30d':
      startDate.setDate(endDate.getDate() - 30);
      break;
    case '90d':
      startDate.setDate(endDate.getDate() - 90);
      break;
    case '1y':
      startDate.setFullYear(endDate.getFullYear() - 1);
      break;
    case 'all':
      startDate.setFullYear(2020, 0, 1); // Arbitrary start date
      break;
    default:
      startDate.setDate(endDate.getDate() - 30);
  }

  return { startDate, endDate };
};

/**
 * Format date for display
 */
export const formatDateForDisplay = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

/**
 * Format date for API
 */
export const formatDateForAPI = (date: Date): string => {
  return date.toISOString();
};

/**
 * Group data by time interval
 */
export const groupByTimeInterval = (
  data: TimeSeriesDataPoint[],
  _interval: 'hour' | 'day' | 'week' | 'month'
): TimeSeriesDataPoint[] => {
  // Simplified implementation - would need proper grouping logic
  return data;
};
