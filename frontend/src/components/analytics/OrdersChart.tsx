import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDateOnly } from '@/lib/format'
import type { SalesOverTimePoint } from '@/lib/analytics/api'

interface OrdersChartProps {
  data: SalesOverTimePoint[]
  isLoading: boolean
}

/** Quantidade de pedidos por dia (só pedidos `completed`). */
export function OrdersChart({ data, isLoading }: OrdersChartProps) {
  return (
    <Card className="p-6">
      <h3 className="text-content mb-4 text-sm font-semibold">Pedidos ao longo do tempo</h3>
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <ResponsiveContainer width="100%" height={256}>
          <BarChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
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
              width={32}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: '0.75rem',
                color: 'var(--color-content)',
              }}
              formatter={(value) => [Number(value), 'Pedidos']}
              labelFormatter={(label: unknown) => formatDateOnly(String(label))}
            />
            <Bar dataKey="orders" fill="var(--color-primary)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
