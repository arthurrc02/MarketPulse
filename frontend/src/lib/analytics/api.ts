/**
 * Chamadas HTTP de Analytics, tipadas em camelCase para o resto da app.
 *
 * O backend responde em snake_case (convenção Python); os `map*` são o
 * único lugar onde esse formato de wire aparece — mesmo padrão de
 * `lib/uploads/api.ts`.
 */

import { apiRequest } from '@/lib/apiClient'

/** Mesmos valores de `etl.types.Marketplace` no backend — não recriar um enum à parte. */
export type Marketplace = 'shopee' | 'mercado_livre' | 'amazon' | 'magalu'

/** Mesmos valores de `etl.types.OrderStatus` no backend. */
export type OrderStatus = 'completed' | 'pending' | 'cancelled' | 'refunded' | 'unknown'

export interface AnalyticsFilters {
  from?: string
  to?: string
  marketplace?: Marketplace
}

export interface AnalyticsOverview {
  revenue: number
  orders: number
  averageOrderValue: number
  activeProducts: number
  hasData: boolean
}

export interface SalesOverTimePoint {
  date: string
  revenue: number
  orders: number
}

export interface OrderStatusBreakdown {
  status: OrderStatus
  count: number
  percentage: number
}

export interface TopProduct {
  productName: string
  sku: string
  quantity: number
  revenue: number
  orders: number
}

interface OverviewResponseBody {
  revenue: number
  orders: number
  average_order_value: number
  active_products: number
  has_data: boolean
}

interface SalesOverTimePointBody {
  date: string
  revenue: number
  orders: number
}

interface OrderStatusBreakdownBody {
  status: OrderStatus
  count: number
  percentage: number
}

interface TopProductBody {
  product_name: string
  sku: string
  quantity: number
  revenue: number
  orders: number
}

function buildQueryString(
  filters: AnalyticsFilters,
  extra?: Record<string, string | number>,
): string {
  const params = new URLSearchParams()
  if (filters.from) params.set('from', filters.from)
  if (filters.to) params.set('to', filters.to)
  if (filters.marketplace) params.set('marketplace', filters.marketplace)
  for (const [key, value] of Object.entries(extra ?? {})) {
    params.set(key, String(value))
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export async function getOverview(filters: AnalyticsFilters = {}): Promise<AnalyticsOverview> {
  const body = await apiRequest<OverviewResponseBody>(
    `/api/v1/analytics/overview${buildQueryString(filters)}`,
  )
  return {
    revenue: body.revenue,
    orders: body.orders,
    averageOrderValue: body.average_order_value,
    activeProducts: body.active_products,
    hasData: body.has_data,
  }
}

export async function getSalesOverTime(
  filters: AnalyticsFilters = {},
): Promise<SalesOverTimePoint[]> {
  const body = await apiRequest<SalesOverTimePointBody[]>(
    `/api/v1/analytics/sales-over-time${buildQueryString(filters)}`,
  )
  return body.map((point) => ({ date: point.date, revenue: point.revenue, orders: point.orders }))
}

export async function getOrdersByStatus(
  filters: AnalyticsFilters = {},
): Promise<OrderStatusBreakdown[]> {
  const body = await apiRequest<OrderStatusBreakdownBody[]>(
    `/api/v1/analytics/orders-by-status${buildQueryString(filters)}`,
  )
  return body.map((row) => ({ status: row.status, count: row.count, percentage: row.percentage }))
}

export async function getTopProducts(
  filters: AnalyticsFilters = {},
  limit = 10,
): Promise<TopProduct[]> {
  const body = await apiRequest<TopProductBody[]>(
    `/api/v1/analytics/top-products${buildQueryString(filters, { limit })}`,
  )
  return body.map((row) => ({
    productName: row.product_name,
    sku: row.sku,
    quantity: row.quantity,
    revenue: row.revenue,
    orders: row.orders,
  }))
}
