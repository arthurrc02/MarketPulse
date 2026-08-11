import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { AnalyticsIcon } from '@/components/icons/Icons'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { KPICard } from '@/components/ui/KPICard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'
import { AnalyticsFilters } from '@/components/analytics/AnalyticsFilters'
import { OrderStatusChart } from '@/components/analytics/OrderStatusChart'
import { OrdersChart } from '@/components/analytics/OrdersChart'
import { RevenueChart } from '@/components/analytics/RevenueChart'
import { TopProductsTable } from '@/components/analytics/TopProductsTable'
import { useAuth } from '@/hooks/useAuth'
import {
  useOrdersByStatusQuery,
  useOverviewQuery,
  useSalesOverTimeQuery,
  useTopProductsQuery,
} from '@/hooks/useAnalytics'
import { ApiError } from '@/lib/apiClient'
import { formatCurrency } from '@/lib/format'
import type { AnalyticsFilters as Filters } from '@/lib/analytics/api'

/**
 * Dashboard real (Sprint 5): KPIs, gráficos e top produtos vêm de
 * `GET /api/v1/analytics/*`, agregados no PostgreSQL a partir dos
 * `OrderItem` do usuário. Nenhum cálculo acontece no cliente — trocar um
 * filtro dispara novas chamadas (React Query), nunca refiltra dados já
 * carregados.
 */
export function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState<Filters>({})

  const overviewQuery = useOverviewQuery(filters)
  const hasData = overviewQuery.data?.hasData ?? false
  const chartsEnabled = overviewQuery.isSuccess && hasData

  const salesOverTimeQuery = useSalesOverTimeQuery(filters, chartsEnabled)
  const ordersByStatusQuery = useOrdersByStatusQuery(filters, chartsEnabled)
  const topProductsQuery = useTopProductsQuery(filters, 10, chartsEnabled)

  const isTrulyEmpty = overviewQuery.isSuccess && !hasData

  const errorMessage =
    overviewQuery.error instanceof ApiError
      ? overviewQuery.error.message
      : 'Não foi possível carregar os indicadores. Tente novamente.'

  return (
    <PageContainer>
      <Section
        title="Bem-vindo ao MarketPulse."
        description={user ? `Conectado como ${user.email}` : ''}
      >
        {!isTrulyEmpty && (
          <div className="mb-6">
            <AnalyticsFilters value={filters} onChange={setFilters} />
          </div>
        )}

        {overviewQuery.isError ? (
          <div className="border-danger/30 bg-danger/5 flex flex-col items-start gap-3 rounded-2xl border p-6">
            <p className="text-content font-medium">Não foi possível carregar os indicadores.</p>
            <p className="text-content-muted text-sm">{errorMessage}</p>
            <Button
              variant="secondary"
              onClick={() => {
                void overviewQuery.refetch()
              }}
            >
              Tentar novamente
            </Button>
          </div>
        ) : isTrulyEmpty ? (
          <EmptyState
            icon={<AnalyticsIcon className="h-8 w-8" />}
            title="Nenhum dado para exibir ainda"
            description="Importe e processe um relatório de vendas para ver seus indicadores aqui."
            action={
              <Button
                onClick={() => {
                  void navigate('/app/uploads')
                }}
              >
                Importar relatório
              </Button>
            }
          />
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KPICard
                label="Faturamento"
                value={overviewQuery.data ? formatCurrency(overviewQuery.data.revenue) : ''}
                hint="Soma do faturamento dos pedidos concluídos no período selecionado."
                isLoading={overviewQuery.isLoading}
              />
              <KPICard
                label="Pedidos"
                value={overviewQuery.data ? String(overviewQuery.data.orders) : ''}
                hint="Quantidade de pedidos distintos concluídos — não a quantidade de itens."
                isLoading={overviewQuery.isLoading}
              />
              <KPICard
                label="Ticket médio"
                value={
                  overviewQuery.data ? formatCurrency(overviewQuery.data.averageOrderValue) : ''
                }
                hint="Faturamento dividido pela quantidade de pedidos concluídos."
                isLoading={overviewQuery.isLoading}
              />
              <KPICard
                label="Produtos ativos"
                value={overviewQuery.data ? String(overviewQuery.data.activeProducts) : ''}
                hint="Quantidade de SKUs distintos com pelo menos um pedido concluído."
                isLoading={overviewQuery.isLoading}
              />
            </div>

            <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
              <RevenueChart
                data={salesOverTimeQuery.data ?? []}
                isLoading={salesOverTimeQuery.isLoading}
              />
              <OrdersChart
                data={salesOverTimeQuery.data ?? []}
                isLoading={salesOverTimeQuery.isLoading}
              />
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
              <OrderStatusChart
                data={ordersByStatusQuery.data ?? []}
                isLoading={ordersByStatusQuery.isLoading}
              />
              <Card className="p-6">
                <h3 className="text-content mb-4 text-sm font-semibold">
                  Produtos com maior faturamento
                </h3>
                <TopProductsTable
                  data={topProductsQuery.data ?? []}
                  isLoading={topProductsQuery.isLoading}
                />
              </Card>
            </div>
          </>
        )}
      </Section>
    </PageContainer>
  )
}
