import { AnalyticsIcon } from '@/components/icons/Icons'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'

/** Placeholder — os gráficos e indicadores chegam na Sprint 5 (Analytics Dashboard). */
export function AnalyticsPage() {
  return (
    <PageContainer>
      <Section
        title="Analytics"
        description="Faturamento, ticket médio, produtos mais vendidos e desempenho por canal."
      >
        <EmptyState
          icon={<AnalyticsIcon className="h-8 w-8" />}
          title="Analytics ainda não está disponível"
          description="Esta funcionalidade chega na Sprint 5 (Analytics Dashboard), depois que o motor ETL processar os relatórios importados."
          badge={<Badge variant="primary">Sprint 5</Badge>}
        />
      </Section>
    </PageContainer>
  )
}
