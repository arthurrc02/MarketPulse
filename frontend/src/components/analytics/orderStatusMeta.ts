import type { OrderStatus } from '@/lib/analytics/api'

/**
 * Rótulo em português + cor de cada `OrderStatus` canônico (mesmos valores
 * do backend, `etl.types.OrderStatus` — não um enum novo no frontend).
 *
 * As cores reaproveitam tokens já existentes no Design System (`Badge`
 * usa `emerald`/`danger` do mesmo jeito) — nenhuma cor nova foi introduzida
 * só para os gráficos.
 */
export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  completed: 'Concluído',
  pending: 'Pendente',
  cancelled: 'Cancelado',
  refunded: 'Reembolsado',
  unknown: 'Desconhecido',
}

export const ORDER_STATUS_COLORS: Record<OrderStatus, string> = {
  completed: 'var(--color-emerald-400)',
  pending: 'var(--color-primary)',
  cancelled: 'var(--color-danger)',
  refunded: 'var(--color-amber-400)',
  unknown: 'var(--color-content-muted)',
}
