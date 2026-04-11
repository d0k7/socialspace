/**
 * Platform Chart Component
 * 
 * Shows message distribution by platform
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { PLATFORM_COLORS, PLATFORM_NAMES, type Platform } from '@/utils/constants'

interface PlatformChartProps {
  data?: Array<{
    platform: string
    messages: number
  }>
}

export default function PlatformChart({ data }: PlatformChartProps) {
  // Mock data if none provided
  const chartData = data || [
    { platform: 'telegram', messages: 45 },
    { platform: 'discord', messages: 38 },
    { platform: 'twitter', messages: 32 },
    { platform: 'reddit', messages: 28 },
    { platform: 'youtube', messages: 25 },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Platform Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="platform"
                tickFormatter={(value) => PLATFORM_NAMES[value as Platform] || value}
                className="text-xs text-gray-600 dark:text-gray-400"
              />
              <YAxis className="text-xs text-gray-600 dark:text-gray-400" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
                labelFormatter={(value) => PLATFORM_NAMES[value as Platform] || value}
              />
              <Bar dataKey="messages" radius={[8, 8, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PLATFORM_COLORS[entry.platform as Platform] || '#6B7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
