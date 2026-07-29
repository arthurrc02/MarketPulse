import { UploadsIcon } from '@/components/icons/Icons'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'

/** Placeholder — o upload de arquivos é implementado na Sprint 3 (File Import). */
export function UploadsPage() {
  return (
    <PageContainer>
      <Section
        title="Uploads"
        description="Importe relatórios de Shopee, Mercado Livre, Amazon e Magalu."
      >
        <EmptyState
          icon={<UploadsIcon className="h-8 w-8" />}
          title="Upload de arquivos ainda não está disponível"
          description="Esta funcionalidade chega na Sprint 3 (File Import)."
          badge={<Badge variant="primary">Sprint 3</Badge>}
        />
      </Section>
    </PageContainer>
  )
}
