import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

import { CloseIcon } from '@/components/icons/Icons'
import { ToastContext, type ToastInput, type ToastVariant } from '@/context/toastContextDefinition'

interface ActiveToast {
  id: number
  variant: ToastVariant
  title: string | undefined
  message: string
}

const DEFAULT_DURATION_MS = 5000

const VARIANT_BORDER_CLASSES: Record<ToastVariant, string> = {
  success: 'border-l-emerald-500',
  error: 'border-l-danger',
  info: 'border-l-primary',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ActiveToast[]>([])
  const nextId = useRef(0)

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const showToast = useCallback(
    (input: ToastInput) => {
      const id = nextId.current
      nextId.current += 1
      setToasts((current) => [
        ...current,
        { id, variant: input.variant ?? 'info', title: input.title, message: input.message },
      ])
      window.setTimeout(() => {
        dismiss(id)
      }, input.durationMs ?? DEFAULT_DURATION_MS)
    },
    [dismiss],
  )

  const value = useMemo(() => ({ showToast }), [showToast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4 sm:right-4 sm:left-auto sm:items-end">
          <AnimatePresence>
            {toasts.map((toast) => (
              <motion.div
                key={toast.id}
                layout
                initial={{ opacity: 0, y: -12, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.18 }}
                role={toast.variant === 'error' ? 'alert' : 'status'}
                className={[
                  'bg-surface-elevated/90 border-border pointer-events-auto w-full max-w-sm rounded-xl border border-l-4 p-4 shadow-2xl shadow-black/20 backdrop-blur-xl',
                  VARIANT_BORDER_CLASSES[toast.variant],
                ].join(' ')}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    {toast.title && (
                      <p className="text-content text-sm font-semibold">{toast.title}</p>
                    )}
                    <p className="text-content-muted text-sm">{toast.message}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      dismiss(toast.id)
                    }}
                    aria-label="Fechar notificação"
                    className="text-content-muted hover:text-content"
                  >
                    <CloseIcon className="h-4 w-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>,
        document.body,
      )}
    </ToastContext.Provider>
  )
}
