/**
 * Chamadas HTTP de Business Insights, tipadas em camelCase para o resto da app.
 *
 * Reaproveita o tipo `AnalyticsFilters` de `lib/analytics/api.ts` — Insights
 * aceita exatamente os mesmos filtros (período + marketplace), então não
 * faz sentido duplicar a interface.
 */

import { apiRequest } from '@/lib/apiClient'
import type { AnalyticsFilters, Marketplace } from '@/lib/analytics/api'

export type { AnalyticsFilters }

export type InsightSeverity = 'positive' | 'negative' | 'neutral'

/** Mesmos valores de `app.schemas.insights.InsightType` no backend. */
export type InsightType =
  | 'revenue_trend'
  | 'orders_trend'
  | 'average_order_value_trend'
  | 'top_product'
  | 'product_decline'
  | 'best_marketplace'

export interface Insight {
  id: string
  type: InsightType
  title: string
  description: string
  severity: InsightSeverity
  value: number
  currentValue: number | null
  previousValue: number | null
  productName: string | null
  sku: string | null
  marketplace: Marketplace | null
}

export interface InsightsResponse {
  hasData: boolean
  insights: Insight[]
}

interface InsightBody {
  id: string
  type: InsightType
  title: string
  description: string
  severity: InsightSeverity
  value: number
  current_value: number | null
  previous_value: number | null
  product_name: string | null
  sku: string | null
  marketplace: Marketplace | null
}

interface InsightsResponseBody {
  has_data: boolean
  insights: InsightBody[]
}

function buildQueryString(filters: AnalyticsFilters): string {
  const params = new URLSearchParams()
  if (filters.from) params.set('from', filters.from)
  if (filters.to) params.set('to', filters.to)
  if (filters.marketplace) params.set('marketplace', filters.marketplace)
  const query = params.toString()
  return query ? `?${query}` : ''
}

function mapInsight(body: InsightBody): Insight {
  return {
    id: body.id,
    type: body.type,
    title: body.title,
    description: body.description,
    severity: body.severity,
    value: body.value,
    currentValue: body.current_value,
    previousValue: body.previous_value,
    productName: body.product_name,
    sku: body.sku,
    marketplace: body.marketplace,
  }
}

export async function getInsights(filters: AnalyticsFilters = {}): Promise<InsightsResponse> {
  const body = await apiRequest<InsightsResponseBody>(
    `/api/v1/insights${buildQueryString(filters)}`,
  )
  return { hasData: body.has_data, insights: body.insights.map(mapInsight) }
}
