import { useQuery } from '@tanstack/react-query'

import { type AnalyticsFilters, getInsights } from '@/lib/insights/api'

/** `filters` entra na chave — trocar o filtro dispara uma nova busca (nunca filtra em memória). */
export function useInsightsQuery(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: ['insights', filters],
    queryFn: () => getInsights(filters),
  })
}
