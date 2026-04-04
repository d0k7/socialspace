// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\analytics\PlatformBreakdown.tsx

/**
 * PlatformBreakdown Component - Pie/Donut Chart for Platform Distribution
 * 
 * FAANG++++ Standards:
 * - Interactive pie/donut chart with Recharts
 * - Platform distribution visualization
 * - Multiple metric views (posts, engagement, followers)
 * - Color-coded by platform
 * - Percentage and value display
 * - Responsive design
 * - Tooltip with detailed info
 * - Loading and empty states
 * - Dark mode support
 * 
 * Features:
 * - Toggle between pie and donut chart
 * - Metric selector (posts/engagement/followers)
 * - Interactive legend
 * - Hover effects
 * - Percentage calculations
 * - Top platforms highlight
 */

import React, { useState, useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  TooltipProps,
} from 'recharts';
import {
  PieChart as PieChartIcon,
  TrendingUp,
  Users,
  FileText,
  Activity,
} from 'lucide-react';
import {
  PlatformAnalytics,
  formatNumber,
  formatPercentage,
} from '../../types/analytics.types';
import { PlatformType, PLATFORM_COLORS, PLATFORM_NAMES } from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface PlatformBreakdownProps {
  data: PlatformAnalytics[];
  metricType?: 'posts' | 'engagement' | 'followers';
  chartType?: 'pie' | 'donut';
  showPercentages?: boolean;
  showLegend?: boolean;
  size?: number;
  loading?: boolean;
}

interface ChartDataPoint {
  name: string;
  value: number;
  color: string;
  percentage: number;
  platform: PlatformType;
}

// ============================================================================
// METRIC OPTIONS
// ============================================================================

const METRIC_OPTIONS = [
  {
    value: 'posts' as const,
    label: 'Posts',
    icon: <FileText className="w-4 h-4" />,
  },
  {
    value: 'engagement' as const,
    label: 'Engagement',
    icon: <Activity className="w-4 h-4" />,
  },
  {
    value: 'followers' as const,
    label: 'Followers',
    icon: <Users className="w-4 h-4" />,
  },
];

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({
  active,
  payload,
}) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload as ChartDataPoint;

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: data.color }}
        />
        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          {data.name}
        </span>
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4">
          <span className="text-xs text-gray-600 dark:text-gray-400">
            Value:
          </span>
          <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
            {formatNumber(data.value)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-xs text-gray-600 dark:text-gray-400">
            Percentage:
          </span>
          <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
            {formatPercentage(data.percentage)}
          </span>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// CUSTOM LABEL
// ============================================================================

interface CustomLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percentage: number;
  name: string;
}

const CustomLabel: React.FC<CustomLabelProps> = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percentage,
  name,
}) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  // Only show label if percentage is > 5%
  if (percentage < 5) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="text-xs font-semibold"
    >
      {formatPercentage(percentage, 0)}
    </text>
  );
};

// ============================================================================
// COMPONENT
// ============================================================================

export const PlatformBreakdown: React.FC<PlatformBreakdownProps> = ({
  data,
  metricType = 'engagement',
  chartType = 'donut',
  showPercentages = true,
  showLegend = true,
  size = 300,
  loading = false,
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [selectedMetric, setSelectedMetric] = useState<'posts' | 'engagement' | 'followers'>(metricType);
  const [currentChartType, setCurrentChartType] = useState<'pie' | 'donut'>(chartType);
  const [activeIndex, setActiveIndex] = useState<number | undefined>(undefined);

  // ============================================================================
  // PROCESS DATA
  // ============================================================================

  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    // Calculate total based on selected metric
    const total = data.reduce((sum, platform) => {
      switch (selectedMetric) {
        case 'posts':
          return sum + platform.totalPosts;
        case 'engagement':
          return sum + platform.totalEngagement;
        case 'followers':
          return sum + platform.followers;
        default:
          return sum;
      }
    }, 0);

    // Map to chart data points
    const points: ChartDataPoint[] = data
      .map(platform => {
        let value = 0;
        switch (selectedMetric) {
          case 'posts':
            value = platform.totalPosts;
            break;
          case 'engagement':
            value = platform.totalEngagement;
            break;
          case 'followers':
            value = platform.followers;
            break;
        }

        const percentage = total > 0 ? (value / total) * 100 : 0;

        return {
          name: PLATFORM_NAMES[platform.platform],
          value,
          color: PLATFORM_COLORS[platform.platform],
          percentage,
          platform: platform.platform,
        };
      })
      .filter(point => point.value > 0) // Filter out platforms with 0 value
      .sort((a, b) => b.value - a.value); // Sort by value descending

    return points;
  }, [data, selectedMetric]);

  // ============================================================================
  // CALCULATE STATS
  // ============================================================================

  const stats = useMemo(() => {
    if (chartData.length === 0) {
      return { total: 0, topPlatform: null, platformCount: 0 };
    }

    const total = chartData.reduce((sum, point) => sum + point.value, 0);
    const topPlatform = chartData[0];
    const platformCount = chartData.length;

    return { total, topPlatform, platformCount };
  }, [chartData]);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handlePieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const handlePieLeave = () => {
    setActiveIndex(undefined);
  };

  const toggleChartType = () => {
    setCurrentChartType(prev => prev === 'pie' ? 'donut' : 'pie');
  };

  // ============================================================================
  // LOADING STATE
  // ============================================================================

  if (loading) {
    return (
      <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="flex items-center justify-center">
            <div className="w-64 h-64 bg-gray-200 dark:bg-gray-700 rounded-full" />
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // EMPTY STATE
  // ============================================================================

  if (!chartData || chartData.length === 0) {
    return (
      <div className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="text-center py-12">
          <PieChartIcon className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No data available
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Start posting to see platform distribution
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
            Platform Distribution
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">Total:</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {formatNumber(stats.total)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">Platforms:</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {stats.platformCount}
              </span>
            </div>
          </div>
        </div>

        {/* Chart Type Toggle */}
        <button
          type="button"
          onClick={toggleChartType}
          className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          {currentChartType === 'pie' ? 'Donut Chart' : 'Pie Chart'}
        </button>
      </div>

      {/* Metric Selector */}
      <div className="mb-6 flex gap-2">
        {METRIC_OPTIONS.map(option => (
          <button
            key={option.value}
            type="button"
            onClick={() => setSelectedMetric(option.value)}
            className={`
              flex-1 px-4 py-2 rounded-lg border transition-colors
              ${selectedMetric === option.value
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              {option.icon}
              <span className="font-medium">{option.label}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Top Platform Highlight */}
      {stats.topPlatform && (
        <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: stats.topPlatform.color }}
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Top Platform
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {stats.topPlatform.name}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {formatPercentage(stats.topPlatform.percentage)}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                {formatNumber(stats.topPlatform.value)} {selectedMetric}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="flex items-center justify-center">
        <ResponsiveContainer width="100%" height={size}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={showPercentages ? (props) => (
                <CustomLabel {...props} percentage={props.payload.percentage} name={props.payload.name} />
              ) : false}
              outerRadius={size / 2 - 20}
              innerRadius={currentChartType === 'donut' ? (size / 2 - 20) * 0.6 : 0}
              fill="#8884d8"
              dataKey="value"
              onMouseEnter={handlePieEnter}
              onMouseLeave={handlePieLeave}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  opacity={activeIndex === undefined || activeIndex === index ? 1 : 0.6}
                  style={{
                    cursor: 'pointer',
                    transition: 'opacity 0.3s ease',
                  }}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            {showLegend && (
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {value}
                  </span>
                )}
              />
            )}
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Platform List */}
      <div className="mt-6 space-y-2">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Breakdown by Platform
        </div>
        {chartData.map((point, index) => (
          <div
            key={point.platform}
            className={`
              flex items-center justify-between p-3 rounded-lg border transition-all
              ${activeIndex === index
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
              }
            `}
            onMouseEnter={() => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(undefined)}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-4 h-4 rounded-full flex-shrink-0"
                style={{ backgroundColor: point.color }}
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {point.name}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {formatNumber(point.value)} {selectedMetric}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Progress Bar */}
              <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${point.percentage}%`,
                    backgroundColor: point.color,
                  }}
                />
              </div>

              {/* Percentage */}
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 w-16 text-right">
                {formatPercentage(point.percentage)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Insight */}
      {stats.topPlatform && (
        <div className="mt-6 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-start gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <span className="font-medium">{stats.topPlatform.name}</span> is your top
              performing platform with{' '}
              <span className="font-semibold">
                {formatPercentage(stats.topPlatform.percentage)}
              </span>{' '}
              of total {selectedMetric}.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default PlatformBreakdown;