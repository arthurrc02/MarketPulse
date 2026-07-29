import { createContext } from 'react'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastInput {
  variant?: ToastVariant
  title?: string
  message: string
  durationMs?: number
}

export interface ToastContextValue {
  showToast: (toast: ToastInput) => void
}

export const ToastContext = createContext<ToastContextValue | undefined>(undefined)
