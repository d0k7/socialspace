/**
 * Message Chart Component
 * 
 * Shows message activity over time
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface MessageChartProps {
  data?: Array<{
    date: string
    sent: number
    received: number
  }>
}

export default function MessageChart({ data }: MessageChartProps) {
  // Mock data if none provided
  const chartData = data || [
    { date: 'Mon', sent: 12, received: 18 },
    { date: 'Tue', sent: 19, received: 25 },
    { date: 'Wed', sent: 15, received: 22 },
    { date: 'Thu', sent: 25, received: 30 },
    { date: 'Fri', sent: 22, received: 28 },
    { date: 'Sat', sent: 18, received: 20 },
    { date: 'Sun', sent: 15, received: 16 },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Message Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="date" 
                className="text-xs text-gray-600 dark:text-gray-400"
              />
              <YAxis className="text-xs text-gray-600 dark:text-gray-400" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#374151' }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="sent"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="received"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}