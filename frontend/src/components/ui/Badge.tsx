import type { ReactNode } from 'react'

export type BadgeVariant = 'neutral' | 'primary' | 'success' | 'danger'

interface BadgeProps {
  variant?: BadgeVariant
  children: ReactNode
  className?: string
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral: 'bg-surface-elevated text-content-muted border-border',
  primary: 'bg-primary/10 text-primary border-primary/20',
  success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  danger: 'bg-danger/10 text-danger border-danger/20',
}

export function Badge({ variant = 'neutral', children, className = '' }: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        VARIANT_CLASSES[variant],
        className,
      ].join(' ')}
    >
      {children}
    </span>
  )
}
