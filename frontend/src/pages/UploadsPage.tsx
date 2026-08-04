import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { UploadsIcon } from '@/components/icons/Icons'
import { Dialog } from '@/components/ui/Dialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { FileUpload } from '@/components/ui/FileUpload'
import { IconButton } from '@/components/ui/IconButton'
import { SearchInput } from '@/components/ui/SearchInput'
import { Skeleton } from '@/components/ui/Skeleton'
import { Table, type SortDirection, type TableColumn } from '@/components/ui/Table'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'
import { UploadStatusBadge } from '@/components/uploads/UploadStatusBadge'
import { TrashIcon } from '@/components/icons/Icons'
import {
  useCreateUploadMutation,
  useDeleteUploadMutation,
  useUploadsQuery,
} from '@/hooks/useUploads'
import { useToast } from '@/hooks/useToast'
import { ApiError } from '@/lib/apiClient'
import { formatDateTime, formatFileSize } from '@/lib/format'
import type { UploadRecord } from '@/lib/uploads/api'

interface QueueItem {
  id: number
  name: string
  progress: number
  status: 'uploading' | 'success' | 'error'
  errorMessage?: string
}

const PROGRESS_INTERVAL_MS = 150
const PROGRESS_STEP = 8
const PROGRESS_CEILING_WHILE_WAITING = 90

function UploadsTableSkeleton() {
  return (
    <div
      className="border-border overflow-hidden rounded-2xl border"
      aria-hidden="true"
      data-testid="uploads-skeleton"
    >
      {[0, 1, 2, 3].map((row) => (
        <div
          key={row}
          className="border-border/60 flex items-center gap-6 border-b px-4 py-4 last:border-b-0"
        >
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  )
}

function UploadQueueList({ items }: { items: QueueItem[] }) {
  if (items.length === 0) return null

  return (
    <ul className="flex flex-col gap-3">
      {items.map((item) => (
        <li key={item.id} className="border-border bg-surface-elevated rounded-xl border p-4">
          <div className="flex items-center justify-between gap-4">
            <span className="text-content truncate text-sm font-medium">{item.name}</span>
            <span className="text-content-muted text-xs">
              {item.status === 'error'
                ? 'Erro'
                : item.status === 'success'
                  ? 'Concluído'
                  : `${String(item.progress)}%`}
            </span>
          </div>
          <div className="bg-surface mt-2 h-1.5 w-full overflow-hidden rounded-full">
            <div
              className={[
                'h-full rounded-full transition-all duration-150',
                item.status === 'error' ? 'bg-danger' : 'bg-primary',
              ].join(' ')}
              style={{ width: `${String(item.progress)}%` }}
            />
          </div>
          {item.errorMessage && <p className="text-danger mt-1.5 text-xs">{item.errorMessage}</p>}
        </li>
      ))}
    </ul>
  )
}

/**
 * Fluxo completo de upload: drag & drop / seleção manual, progresso
 * simulado enquanto o backend responde, histórico com busca e ordenação, e
 * exclusão com confirmação. Nenhum dado de ETL — os arquivos só são
 * armazenados (ver docs/roadmap.md, Sprint 3).
 */
export function UploadsPage() {
  const { data: uploads, isLoading } = useUploadsQuery()
  const createMutation = useCreateUploadMutation()
  const deleteMutation = useDeleteUploadMutation()
  const { showToast } = useToast()

  const [searchTerm, setSearchTerm] = useState('')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [uploadToDelete, setUploadToDelete] = useState<UploadRecord | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const nextQueueId = useRef(0)

  function handleFilesSelected(files: File[]) {
    for (const file of files) {
      const queueId = nextQueueId.current
      nextQueueId.current += 1

      setQueue((current) => [
        ...current,
        { id: queueId, name: file.name, progress: 0, status: 'uploading' },
      ])

      const intervalId = window.setInterval(() => {
        setQueue((current) =>
          current.map((item) =>
            item.id === queueId &&
            item.status === 'uploading' &&
            item.progress < PROGRESS_CEILING_WHILE_WAITING
              ? {
                  ...item,
                  progress: Math.min(item.progress + PROGRESS_STEP, PROGRESS_CEILING_WHILE_WAITING),
                }
              : item,
          ),
        )
      }, PROGRESS_INTERVAL_MS)

      createMutation.mutate(file, {
        onSuccess: () => {
          window.clearInterval(intervalId)
          setQueue((current) =>
            current.map((item) =>
              item.id === queueId ? { ...item, progress: 100, status: 'success' } : item,
            ),
          )
          showToast({ variant: 'success', message: `${file.name} enviado com sucesso.` })
          window.setTimeout(() => {
            setQueue((current) => current.filter((item) => item.id !== queueId))
          }, 1500)
        },
        onError: (error: unknown) => {
          window.clearInterval(intervalId)
          // Mensagens distintas de propósito: o toast é uma notificação
          // rápida (some em alguns segundos); o motivo detalhado fica junto
          // do item na fila, visível até o usuário reparar nele.
          const detail =
            error instanceof ApiError ? error.message : 'Não foi possível enviar o arquivo.'
          setQueue((current) =>
            current.map((item) =>
              item.id === queueId ? { ...item, status: 'error', errorMessage: detail } : item,
            ),
          )
          showToast({ variant: 'error', message: `Falha ao enviar ${file.name}.` })
        },
      })
    }
  }

  const visibleUploads = useMemo(() => {
    const list = uploads ?? []
    const term = searchTerm.trim().toLowerCase()
    const filtered = term
      ? list.filter((upload) => upload.originalFilename.toLowerCase().includes(term))
      : list
    return [...filtered].sort((a, b) => {
      const diff = new Date(a.uploadedAt).getTime() - new Date(b.uploadedAt).getTime()
      return sortDirection === 'asc' ? diff : -diff
    })
  }, [uploads, searchTerm, sortDirection])

  async function handleConfirmDelete(): Promise<void> {
    if (!uploadToDelete) return
    setIsDeleting(true)
    try {
      await deleteMutation.mutateAsync(uploadToDelete.id)
      showToast({ variant: 'success', message: `${uploadToDelete.originalFilename} excluído.` })
      setUploadToDelete(null)
    } catch (error) {
      showToast({
        variant: 'error',
        message: error instanceof ApiError ? error.message : 'Não foi possível excluir o arquivo.',
      })
    } finally {
      setIsDeleting(false)
    }
  }

  const columns: TableColumn<UploadRecord>[] = [
    {
      key: 'name',
      header: 'Nome',
      render: (row) => (
        <Link to={`/app/uploads/${row.id}`} className="text-content font-medium hover:underline">
          {row.originalFilename}
        </Link>
      ),
    },
    {
      key: 'date',
      header: 'Data',
      sortable: true,
      render: (row) => <span className="text-content-muted">{formatDateTime(row.uploadedAt)}</span>,
    },
    {
      key: 'size',
      header: 'Tamanho',
      align: 'right',
      render: (row) => <span className="text-content-muted">{formatFileSize(row.fileSize)}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <UploadStatusBadge status={row.status} />,
    },
    {
      key: 'actions',
      header: 'Ações',
      align: 'right',
      render: (row) => (
        <IconButton
          icon={<TrashIcon className="h-4 w-4" />}
          aria-label={`Excluir ${row.originalFilename}`}
          variant="ghost"
          onClick={(event) => {
            event.stopPropagation()
            setUploadToDelete(row)
          }}
        />
      ),
    },
  ]

  return (
    <PageContainer>
      <Section
        title="Uploads"
        description="Importe relatórios de Shopee, Mercado Livre, Amazon e Magalu."
      >
        <FileUpload onFilesSelected={handleFilesSelected} />
        <UploadQueueList items={queue} />
      </Section>

      <Section title="Histórico" className="mt-10">
        <div className="max-w-sm">
          <SearchInput
            aria-label="Buscar por nome do arquivo"
            placeholder="Buscar por nome..."
            value={searchTerm}
            onChange={(event) => {
              setSearchTerm(event.target.value)
            }}
            onClear={() => {
              setSearchTerm('')
            }}
          />
        </div>

        {isLoading ? (
          <UploadsTableSkeleton />
        ) : visibleUploads.length === 0 ? (
          uploads && uploads.length > 0 ? (
            <EmptyState
              title="Nenhum resultado"
              description={`Nenhum arquivo encontrado para "${searchTerm}".`}
            />
          ) : (
            <EmptyState
              icon={<UploadsIcon className="h-8 w-8" />}
              title="Nenhum upload ainda"
              description="Envie seu primeiro arquivo CSV ou XLSX para começar."
            />
          )
        ) : (
          <Table
            columns={columns}
            rows={visibleUploads}
            getRowKey={(row) => row.id}
            sortKey="date"
            sortDirection={sortDirection}
            onSortChange={() => {
              setSortDirection((current) => (current === 'desc' ? 'asc' : 'desc'))
            }}
          />
        )}
      </Section>

      <Dialog
        isOpen={uploadToDelete !== null}
        onClose={() => {
          setUploadToDelete(null)
        }}
        title="Excluir upload"
        description={
          uploadToDelete
            ? `Tem certeza que deseja excluir "${uploadToDelete.originalFilename}"? Essa ação não pode ser desfeita.`
            : ''
        }
        confirmLabel="Excluir"
        cancelLabel="Cancelar"
        variant="danger"
        isConfirming={isDeleting}
        onConfirm={() => void handleConfirmDelete()}
      />
    </PageContainer>
  )
}
