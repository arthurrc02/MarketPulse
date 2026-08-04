import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'

import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'
import { UploadStatusBadge } from '@/components/uploads/UploadStatusBadge'
import { useUploadQuery } from '@/hooks/useUploads'
import { ApiError } from '@/lib/apiClient'
import { formatDateTime, formatFileSize } from '@/lib/format'

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="border-border flex items-center justify-between gap-4 border-b py-3 last:border-b-0">
      <dt className="text-content-muted text-sm">{label}</dt>
      <dd className="text-content text-sm font-medium">{value}</dd>
    </div>
  )
}

/** Mostra apenas metadados do upload — nenhum dado de ETL (ver docs/roadmap.md, Sprint 3). */
export function UploadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: upload, isLoading, error } = useUploadQuery(id ?? '')

  const backLink = (
    <Link to="/app/uploads" className="text-primary text-sm font-medium hover:underline">
      ← Voltar para uploads
    </Link>
  )

  if (isLoading) {
    return (
      <PageContainer>
        <Section title="Detalhes do upload">
          {backLink}
          <div className="border-border mt-6 max-w-md space-y-4 rounded-2xl border p-6">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </Section>
      </PageContainer>
    )
  }

  if (error || !upload) {
    const message =
      error instanceof ApiError ? error.message : 'Não foi possível carregar este upload.'
    return (
      <PageContainer>
        <Section title="Detalhes do upload">
          {backLink}
          <div className="mt-6">
            <EmptyState title="Upload não encontrado" description={message} />
          </div>
        </Section>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <Section title="Detalhes do upload">
        {backLink}
        <div className="border-border bg-surface-elevated/50 mt-6 max-w-md rounded-2xl border p-6">
          <h2 className="text-content mb-4 text-lg font-semibold tracking-tight break-all">
            {upload.originalFilename}
          </h2>
          <dl>
            <DetailRow label="Tamanho" value={formatFileSize(upload.fileSize)} />
            <DetailRow label="Tipo" value={upload.mimeType} />
            <DetailRow label="Enviado em" value={formatDateTime(upload.uploadedAt)} />
            <DetailRow label="Status" value={<UploadStatusBadge status={upload.status} />} />
          </dl>
        </div>
      </Section>
    </PageContainer>
  )
}
