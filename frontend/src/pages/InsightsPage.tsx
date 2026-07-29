import { InsightsIcon } from '@/components/icons/Icons'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'

/** Placeholder — o motor de insights chega na Sprint 6 (Business Insights). */
export function InsightsPage() {
  return (
    <PageContainer>
      <Section
        title="Insights"
        description="Observações automáticas sobre o desempenho do seu negócio."
      >
        <EmptyState
          icon={<InsightsIcon className="h-8 w-8" />}
          title="Insights ainda não estão disponíveis"
          description="Esta funcionalidade chega na Sprint 6 (Business Insights)."
          badge={<Badge variant="primary">Sprint 6</Badge>}
        />
      </Section>
    </PageContainer>
  )
}
