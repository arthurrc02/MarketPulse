import type { ReactNode } from 'react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { PlayIcon } from '@/components/icons/Icons'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'
import { UploadStatusBadge } from '@/components/uploads/UploadStatusBadge'
import { useProcessUploadMutation, useUploadQuery } from '@/hooks/useUploads'
import { useToast } from '@/hooks/useToast'
import { ApiError } from '@/lib/apiClient'
import { formatDateTime, formatDuration, formatFileSize } from '@/lib/format'

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="border-border flex items-center justify-between gap-4 border-b py-3 last:border-b-0">
      <dt className="text-content-muted text-sm">{label}</dt>
      <dd className="text-content text-sm font-medium">{value}</dd>
    </div>
  )
}

/**
 * Metadados do upload e resultado do processamento ETL (início, fim,
 * duração, erro). Nunca mostra os dados extraídos — isso fica para a
 * Sprint 5 (Analytics Dashboard).
 */
export function UploadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: upload, isLoading, error } = useUploadQuery(id ?? '')
  const processMutation = useProcessUploadMutation()
  const { showToast } = useToast()
  const [isProcessing, setIsProcessing] = useState(false)

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

  async function handleProcess(): Promise<void> {
    if (!upload) return
    setIsProcessing(true)
    try {
      const result = await processMutation.mutateAsync(upload.id)
      if (result.status === 'processed') {
        showToast({ variant: 'success', message: 'Arquivo processado com sucesso.' })
      } else {
        showToast({
          variant: 'error',
          message: result.errorMessage ?? 'Falha ao processar o arquivo.',
        })
      }
    } catch (processError) {
      showToast({
        variant: 'error',
        message:
          processError instanceof ApiError
            ? processError.message
            : 'Não foi possível processar o arquivo.',
      })
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <PageContainer>
      <Section title="Detalhes do upload">
        {backLink}
        <div className="border-border bg-surface-elevated/50 mt-6 max-w-md rounded-2xl border p-6">
          <div className="mb-4 flex items-start justify-between gap-4">
            <h2 className="text-content text-lg font-semibold tracking-tight break-all">
              {upload.originalFilename}
            </h2>
            <Button
              variant="secondary"
              onClick={() => void handleProcess()}
              isLoading={isProcessing}
              disabled={isProcessing || upload.status === 'processing'}
            >
              <PlayIcon className="h-4 w-4" />
              Processar
            </Button>
          </div>
          <dl>
            <DetailRow label="Tamanho" value={formatFileSize(upload.fileSize)} />
            <DetailRow label="Tipo" value={upload.mimeType} />
            <DetailRow label="Enviado em" value={formatDateTime(upload.uploadedAt)} />
            <DetailRow label="Status" value={<UploadStatusBadge status={upload.status} />} />
            {upload.startedAt && (
              <DetailRow label="Início do processamento" value={formatDateTime(upload.startedAt)} />
            )}
            {upload.finishedAt && (
              <DetailRow label="Fim do processamento" value={formatDateTime(upload.finishedAt)} />
            )}
            {upload.startedAt && upload.finishedAt && (
              <DetailRow
                label="Duração"
                value={formatDuration(upload.startedAt, upload.finishedAt)}
              />
            )}
          </dl>
          {upload.status === 'failed' && upload.errorMessage && (
            <p className="bg-danger/10 text-danger mt-4 rounded-xl p-3 text-sm">
              {upload.errorMessage}
            </p>
          )}
        </div>
      </Section>
    </PageContainer>
  )
}
