/**
 * Line Chart Component
 * 
 * Reusable line chart with Recharts
 */

import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface LineChartProps {
  data: any[]
  xDataKey: string
  yDataKey: string
  title?: string
  color?: string
  height?: number
}

export default function LineChart({
  data,
  xDataKey,
  yDataKey,
  title,
  color = '#3B82F6',
  height = 300,
}: LineChartProps) {
  return (
    <div className="w-full">
      {title && (
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey={xDataKey}
            className="text-xs text-gray-600 dark:text-gray-400"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis
            className="text-xs text-gray-600 dark:text-gray-400"
            tick={{ fill: 'currentColor' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#374151' }}
          />
          <Line
            type="monotone"
            dataKey={yDataKey}
            stroke={color}
            strokeWidth={2}
            dot={{ fill: color, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  )
}
