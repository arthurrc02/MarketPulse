import { Badge, type BadgeVariant } from '@/components/ui/Badge'
import type { UploadStatus } from '@/lib/uploads/api'

const STATUS_LABELS: Record<UploadStatus, string> = {
  uploaded: 'Enviado',
  queued: 'Na fila',
  processing: 'Processando',
  processed: 'Processado',
  failed: 'Falhou',
}

const STATUS_VARIANTS: Record<UploadStatus, BadgeVariant> = {
  uploaded: 'neutral',
  queued: 'neutral',
  processing: 'primary',
  processed: 'success',
  failed: 'danger',
}

/**
 * Rótulo em português + variante de cor para cada `UploadStatus`.
 *
 * Vive em `components/uploads/`, não em `components/ui/`: é composição de
 * `Badge` com uma regra específica do domínio de uploads, não um primitivo
 * genérico do Design System.
 */
export function UploadStatusBadge({ status }: { status: UploadStatus }) {
  return <Badge variant={STATUS_VARIANTS[status]}>{STATUS_LABELS[status]}</Badge>
}
