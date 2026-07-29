import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'

interface DialogProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  isConfirming?: boolean
  variant?: 'default' | 'danger'
}

/** `Modal` com o par de ações padronizado de uma confirmação (confirmar/cancelar). */
export function Dialog({
  isOpen,
  onClose,
  title,
  description,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  onConfirm,
  isConfirming = false,
  variant = 'default',
}: DialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      {description && <p className="text-content-muted mb-6 text-sm">{description}</p>}
      <div className="flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onClose} disabled={isConfirming}>
          {cancelLabel}
        </Button>
        <Button
          type="button"
          variant={variant === 'danger' ? 'danger' : 'primary'}
          onClick={onConfirm}
          isLoading={isConfirming}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}
