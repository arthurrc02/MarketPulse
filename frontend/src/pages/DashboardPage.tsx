import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { KPICard } from '@/components/ui/KPICard'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'
import { useAuth } from '@/hooks/useAuth'

const IMPORT_HINT = 'Disponível após a primeira importação de relatório (Sprint 3 em diante).'

/**
 * Estrutura real do dashboard (Sprint 2) — apenas placeholders visuais.
 * Os indicadores de negócio chegam com o Analytics Dashboard (Sprint 5).
 */
export function DashboardPage() {
  const { user } = useAuth()

  return (
    <PageContainer>
      <Section
        title="Bem-vindo ao MarketPulse."
        description={user ? `Conectado como ${user.email}` : ''}
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard label="Faturamento" value="—" hint={IMPORT_HINT} />
          <KPICard label="Pedidos" value="—" hint={IMPORT_HINT} />
          <KPICard label="Ticket médio" value="—" hint={IMPORT_HINT} />
          <KPICard label="Produtos ativos" value="—" hint={IMPORT_HINT} />
        </div>
      </Section>

      <Section title="Atividade recente" className="mt-10">
        <EmptyState
          title="Nenhuma atividade ainda"
          description="Assim que você importar seu primeiro relatório, o resumo aparece aqui."
          badge={<Badge variant="primary">Disponível na Sprint 3</Badge>}
        />
      </Section>
    </PageContainer>
  )
}
