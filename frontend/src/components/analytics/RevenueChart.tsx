import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatCurrency, formatDateOnly } from '@/lib/format'
import type { SalesOverTimePoint } from '@/lib/analytics/api'

interface RevenueChartProps {
  data: SalesOverTimePoint[]
  isLoading: boolean
}

/** Faturamento por dia (só pedidos `completed` — ver `AnalyticsOverview` no backend). */
export function RevenueChart({ data, isLoading }: RevenueChartProps) {
  return (
    <Card className="p-6">
      <h3 className="text-content mb-4 text-sm font-semibold">Faturamento ao longo do tempo</h3>
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <ResponsiveContainer width="100%" height={256}>
          <AreaChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.35} />
                <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={(value: string) => formatDateOnly(value)}
              stroke="var(--color-content-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="var(--color-content-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              width={72}
              tickFormatter={(value: number) => formatCurrency(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: '0.75rem',
                color: 'var(--color-content)',
              }}
              formatter={(value) => [formatCurrency(Number(value)), 'Faturamento']}
              labelFormatter={(label: unknown) => formatDateOnly(String(label))}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="var(--color-primary)"
              strokeWidth={2}
              fill="url(#revenueGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
