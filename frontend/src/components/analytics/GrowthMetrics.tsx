// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\analytics\GrowthMetrics.tsx

/**
 * GrowthMetrics Component - Follower Growth Tracking
 * 
 * FAANG++++ Standards:
 * - Follower growth visualization
 * - Multi-platform growth comparison
 * - Growth rate calculations
 * - Trend indicators
 * - Period-over-period comparison
 * - Interactive charts
 * - Loading and empty states
 * - Dark mode support
 * 
 * Features:
 * - Line chart for follower growth
 * - Platform selector
 * - Growth rate percentage
 * - Absolute growth numbers
 * - Trend direction (up/down/stable)
 * - Period comparison
 * - Milestone tracking
 * - Insights and recommendations
 */

import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import {
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  Award,
  Target,
  ArrowUp,
  ArrowDown,
  Calendar,
} from 'lucide-react';
import {
  FollowerGrowth,
  AudienceInsights,
  formatNumber,
  formatPercentage,
  formatDateForDisplay,
  determineTrend,
} from '../../types/analytics.types';
import { PlatformType, PLATFORM_COLORS, PLATFORM_NAMES } from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface GrowthMetricsProps {
  audienceInsights: AudienceInsights;
  showAllPlatforms?: boolean;
  chartHeight?: number;
  loading?: boolean;
}

interface ChartDataPoint {
  date: string;
  [key: string]: number | string;
}

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({
  active,
  payload,
  label,
}) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4">
      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
        {formatDateForDisplay(label)}
      </div>
      <div className="space-y-1">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {entry.name}
              </span>
            </div>
            <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
              {formatNumber(entry.value as number)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// GROWTH CARD COMPONENT
// ============================================================================

interface GrowthCardProps {
  growth: FollowerGrowth;
  isSelected?: boolean;
  onClick?: () => void;
}

const GrowthCard: React.FC<GrowthCardProps> = ({ growth, isSelected, onClick }) => {
  const trend = determineTrend(growth.current, growth.previous);
  const isPositive = growth.growth > 0;
  const isNegative = growth.growth < 0;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        w-full p-4 rounded-lg border-2 transition-all text-left
        ${isSelected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 bg-white dark:bg-gray-800'
        }
      `}
    >
      {/* Platform Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: PLATFORM_COLORS[growth.platform] }}
          />
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {PLATFORM_NAMES[growth.platform]}
          </span>
        </div>

        {/* Trend Icon */}
        {trend === 'up' && (
          <TrendingUp className="w-5 h-5 text-green-500" />
        )}
        {trend === 'down' && (
          <TrendingDown className="w-5 h-5 text-red-500" />
        )}
        {trend === 'stable' && (
          <Minus className="w-5 h-5 text-gray-500" />
        )}
      </div>

      {/* Current Followers */}
      <div className="mb-3">
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatNumber(growth.current)}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Total Followers
        </div>
      </div>

      {/* Growth Stats */}
      <div className="flex items-center justify-between">
        <div>
          <div className={`
            text-sm font-semibold
            ${isPositive ? 'text-green-600 dark:text-green-400' : ''}
            ${isNegative ? 'text-red-600 dark:text-red-400' : ''}
            ${!isPositive && !isNegative ? 'text-gray-600 dark:text-gray-400' : ''}
          `}>
            {isPositive && '+'}
            {formatNumber(growth.growth)}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Absolute Growth
          </div>
        </div>

        <div>
          <div className={`
            text-sm font-semibold
            ${isPositive ? 'text-green-600 dark:text-green-400' : ''}
            ${isNegative ? 'text-red-600 dark:text-red-400' : ''}
            ${!isPositive && !isNegative ? 'text-gray-600 dark:text-gray-400' : ''}
          `}>
            {isPositive && '+'}
            {formatPercentage(growth.growthRate)}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Growth Rate
          </div>
        </div>
      </div>
    </button>
  );
};

// ============================================================================
// MILESTONE COMPONENT
// ============================================================================

interface MilestoneProps {
  value: number;
  label: string;
  achieved: boolean;
  progress?: number;
}

const Milestone: React.FC<MilestoneProps> = ({
  value,
  label,
  achieved,
  progress = 0,
}) => (
  <div className="relative">
    <div className={`
      p-4 rounded-lg border-2 transition-all
      ${achieved
        ? 'bg-green-50 dark:bg-green-900/20 border-green-500'
        : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
      }
    `}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {achieved ? (
            <Award className="w-5 h-5 text-green-600 dark:text-green-400" />
          ) : (
            <Target className="w-5 h-5 text-gray-400 dark:text-gray-600" />
          )}
          <span className={`
            text-sm font-medium
            ${achieved ? 'text-green-900 dark:text-green-100' : 'text-gray-700 dark:text-gray-300'}
          `}>
            {label}
          </span>
        </div>
        <span className={`
          text-lg font-bold
          ${achieved ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-gray-100'}
        `}>
          {formatNumber(value)}
        </span>
      </div>

      {!achieved && progress > 0 && (
        <>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-500"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">
            {formatPercentage(progress)} complete
          </div>
        </>
      )}
    </div>
  </div>
);

// ============================================================================
// COMPONENT
// ============================================================================

export const GrowthMetrics: React.FC<GrowthMetricsProps> = ({
  audienceInsights,
  showAllPlatforms = true,
  chartHeight = 300,
  loading = false,
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [selectedPlatforms, setSelectedPlatforms] = useState<PlatformType[]>(
    showAllPlatforms
      ? audienceInsights.platforms.map(p => p.platform)
      : audienceInsights.platforms.length > 0
      ? [audienceInsights.platforms[0].platform]
      : []
  );

  // ============================================================================
  // PROCESS CHART DATA
  // ============================================================================

  const chartData = useMemo(() => {
    if (!audienceInsights.platforms || audienceInsights.platforms.length === 0) {
      return [];
    }

    // Collect all unique dates
    const dateSet = new Set<string>();
    selectedPlatforms.forEach(platform => {
      const platformData = audienceInsights.platforms.find(p => p.platform === platform);
      if (platformData) {
        platformData.data.forEach(point => dateSet.add(point.date));
      }
    });

    const dates = Array.from(dateSet).sort();

    // Build chart data
    const data: ChartDataPoint[] = dates.map(date => {
      const dataPoint: ChartDataPoint = { date };

      selectedPlatforms.forEach(platform => {
        const platformData = audienceInsights.platforms.find(p => p.platform === platform);
        if (platformData) {
          const point = platformData.data.find(p => p.date === date);
          if (point) {
            dataPoint[platform] = point.value;
          }
        }
      });

      return dataPoint;
    });

    return data;
  }, [audienceInsights.platforms, selectedPlatforms]);

  // ============================================================================
  // CALCULATE MILESTONES
  // ============================================================================

  const milestones = useMemo(() => {
    const current = audienceInsights.totalFollowers;

    const targets = [
      { value: 1000, label: '1K Followers' },
      { value: 5000, label: '5K Followers' },
      { value: 10000, label: '10K Followers' },
      { value: 50000, label: '50K Followers' },
      { value: 100000, label: '100K Followers' },
    ];

    return targets.map(target => ({
      ...target,
      achieved: current >= target.value,
      progress: current < target.value ? (current / target.value) * 100 : 100,
    }));
  }, [audienceInsights.totalFollowers]);

  const nextMilestone = milestones.find(m => !m.achieved);

  // ============================================================================
  // TOGGLE PLATFORM
  // ============================================================================

  const togglePlatform = (platform: PlatformType) => {
    setSelectedPlatforms(prev => {
      if (prev.includes(platform)) {
        // Keep at least one platform selected
        if (prev.length === 1) return prev;
        return prev.filter(p => p !== platform);
      } else {
        return [...prev, platform];
      }
    });
  };

  // ============================================================================
  // LOADING STATE
  // ============================================================================

  if (loading) {
    return (
      <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // EMPTY STATE
  // ============================================================================

  if (!audienceInsights.platforms || audienceInsights.platforms.length === 0) {
    return (
      <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No follower data available
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Connect your platforms to track follower growth
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  const overallTrend = determineTrend(
    audienceInsights.totalFollowers,
    audienceInsights.totalFollowers - audienceInsights.totalGrowth
  );

  return (
    <div className="w-full space-y-6">
      {/* Overview Stats */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
              Follower Growth
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Track your audience growth across all platforms
            </p>
          </div>

          {/* Overall Trend Badge */}
          {overallTrend === 'up' && (
            <div className="flex items-center gap-2 px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
              <ArrowUp className="w-4 h-4" />
              <span className="font-semibold">Growing</span>
            </div>
          )}
          {overallTrend === 'down' && (
            <div className="flex items-center gap-2 px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full">
              <ArrowDown className="w-4 h-4" />
              <span className="font-semibold">Declining</span>
            </div>
          )}
          {overallTrend === 'stable' && (
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full">
              <Minus className="w-4 h-4" />
              <span className="font-semibold">Stable</span>
            </div>
          )}
        </div>

        {/* Total Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-3 mb-2">
              <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Total Followers
              </span>
            </div>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {formatNumber(audienceInsights.totalFollowers)}
            </div>
          </div>

          <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-green-900 dark:text-green-100">
                Total Growth
              </span>
            </div>
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">
              +{formatNumber(audienceInsights.totalGrowth)}
            </div>
          </div>

          <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <div className="flex items-center gap-3 mb-2">
              <Calendar className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
                Growth Rate
              </span>
            </div>
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              {formatPercentage(audienceInsights.growthRate)}
            </div>
          </div>
        </div>

        {/* Platform Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {audienceInsights.platforms.map(growth => (
            <GrowthCard
              key={growth.platform}
              growth={growth}
              isSelected={selectedPlatforms.includes(growth.platform)}
              onClick={() => togglePlatform(growth.platform)}
            />
          ))}
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Growth Over Time
            </h4>
            <ResponsiveContainer width="100%" height={chartHeight}>
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-700" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  tickFormatter={formatNumber}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  formatter={(value) => (
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {PLATFORM_NAMES[value as PlatformType]}
                    </span>
                  )}
                />

                {selectedPlatforms.map(platform => (
                  <Line
                    key={platform}
                    type="monotone"
                    dataKey={platform}
                    stroke={PLATFORM_COLORS[platform]}
                    strokeWidth={2}
                    dot={{ r: 3, fill: PLATFORM_COLORS[platform] }}
                    activeDot={{ r: 5 }}
                    name={platform}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Milestones */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Milestones
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {milestones.map((milestone, index) => (
            <Milestone key={index} {...milestone} />
          ))}
        </div>

        {/* Next Milestone Message */}
        {nextMilestone && (
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-start gap-2">
              <Target className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900 dark:text-blue-100">
                <p className="font-medium">Next Milestone: {nextMilestone.label}</p>
                <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                  You need {formatNumber(nextMilestone.value - audienceInsights.totalFollowers)} more
                  followers to reach this milestone. Keep growing!
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default GrowthMetrics;
