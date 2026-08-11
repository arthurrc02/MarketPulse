import { useQuery } from '@tanstack/react-query'

import {
  type AnalyticsFilters,
  getOrdersByStatus,
  getOverview,
  getSalesOverTime,
  getTopProducts,
} from '@/lib/analytics/api'

/** `filters` entra na chave — trocar o filtro dispara uma nova busca (nunca filtra em memória). */
const ANALYTICS_QUERY_KEY = ['analytics'] as const

export function useOverviewQuery(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: [...ANALYTICS_QUERY_KEY, 'overview', filters],
    queryFn: () => getOverview(filters),
  })
}

export function useSalesOverTimeQuery(filters: AnalyticsFilters, enabled = true) {
  return useQuery({
    queryKey: [...ANALYTICS_QUERY_KEY, 'sales-over-time', filters],
    queryFn: () => getSalesOverTime(filters),
    enabled,
  })
}

export function useOrdersByStatusQuery(filters: AnalyticsFilters, enabled = true) {
  return useQuery({
    queryKey: [...ANALYTICS_QUERY_KEY, 'orders-by-status', filters],
    queryFn: () => getOrdersByStatus(filters),
    enabled,
  })
}

export function useTopProductsQuery(filters: AnalyticsFilters, limit = 10, enabled = true) {
  return useQuery({
    queryKey: [...ANALYTICS_QUERY_KEY, 'top-products', filters, limit],
    queryFn: () => getTopProducts(filters, limit),
    enabled,
  })
}
