import { AnimatePresence } from 'framer-motion'

import { InsightsIcon } from '@/components/icons/Icons'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { Section } from '@/components/layout/Section'
import { InsightCard } from '@/components/insights/InsightCard'
import { useInsightsQuery } from '@/hooks/useInsights'
import { ApiError } from '@/lib/apiClient'
import type { AnalyticsFilters } from '@/lib/insights/api'

function InsightsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
      {[0, 1, 2].map((index) => (
        <div key={index} className="border-border rounded-2xl border p-5">
          <Skeleton className="h-9 w-9 rounded-full" />
          <Skeleton className="mt-4 h-4 w-2/3" />
          <Skeleton className="mt-2 h-4 w-full" />
        </div>
      ))}
    </div>
  )
}

/**
 * Observações determinísticas sobre o desempenho do usuário (Sprint 6).
 * Busca própria (`useInsightsQuery`) — não deriva de `useOverviewQuery` — para
 * ter seus próprios estados de carregamento/erro/vazio, distintos dos KPIs.
 */
export function InsightsSection({ filters }: { filters: AnalyticsFilters }) {
  const query = useInsightsQuery(filters)

  const errorMessage =
    query.error instanceof ApiError
      ? query.error.message
      : 'Não foi possível carregar os insights. Tente novamente.'

  return (
    <Section
      title="Insights"
      description="Observações automáticas sobre o seu desempenho."
      className="mt-8"
    >
      {query.isLoading ? (
        <InsightsSkeleton />
      ) : query.isError ? (
        <div className="border-danger/30 bg-danger/5 flex flex-col items-start gap-3 rounded-2xl border p-6">
          <p className="text-content font-medium">Não foi possível carregar os insights.</p>
          <p className="text-content-muted text-sm">{errorMessage}</p>
          <Button
            variant="secondary"
            onClick={() => {
              void query.refetch()
            }}
          >
            Tentar novamente
          </Button>
        </div>
      ) : !query.data?.hasData ? null : query.data.insights.length === 0 ? (
        <EmptyState
          icon={<InsightsIcon className="h-8 w-8" />}
          title="Nenhum insight disponível para este período"
          description="Não há dados suficientes para gerar observações — tente ampliar o período ou remover filtros."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {query.data.insights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </Section>
  )
}
