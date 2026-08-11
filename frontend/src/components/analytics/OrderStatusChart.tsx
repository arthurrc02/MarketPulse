import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import type { OrderStatusBreakdown } from '@/lib/analytics/api'
import { ORDER_STATUS_COLORS, ORDER_STATUS_LABELS } from './orderStatusMeta'

interface OrderStatusChartProps {
  data: OrderStatusBreakdown[]
  isLoading: boolean
}

/** Distribuição de pedidos por status — todos os status, não só `completed`. */
export function OrderStatusChart({ data, isLoading }: OrderStatusChartProps) {
  return (
    <Card className="p-6">
      <h3 className="text-content mb-4 text-sm font-semibold">Pedidos por status</h3>
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <ResponsiveContainer width="100%" height={256}>
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="status"
              innerRadius={56}
              outerRadius={88}
              paddingAngle={2}
            >
              {data.map((entry) => (
                // `Cell` está deprecado desde o Recharts 3 (a favor da prop `shape`),
                // mas continua totalmente suportado até a 4.0 — migrar exigiria uma
                // função de sector customizada só para pintar cada fatia, o que não
                // compensa nesta sprint.
                // eslint-disable-next-line @typescript-eslint/no-deprecated
                <Cell key={entry.status} fill={ORDER_STATUS_COLORS[entry.status]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: '0.75rem',
                color: 'var(--color-content)',
              }}
              formatter={(value, _name, item) => {
                const payload = item.payload as OrderStatusBreakdown | undefined
                return [
                  `${String(Number(value))} (${String(payload?.percentage ?? 0)}%)`,
                  payload ? ORDER_STATUS_LABELS[payload.status] : '',
                ]
              }}
            />
            <Legend
              formatter={(_value, entry) => {
                const status = (entry.payload as { status?: OrderStatusBreakdown['status'] }).status
                return (
                  <span className="text-content-muted text-xs">
                    {status ? ORDER_STATUS_LABELS[status] : ''}
                  </span>
                )
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
