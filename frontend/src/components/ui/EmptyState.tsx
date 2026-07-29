import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  badge?: ReactNode
  action?: ReactNode
}

/** Bloco reutilizável para telas/seções sem conteúdo ainda (placeholders desta sprint). */
export function EmptyState({ icon, title, description, badge, action }: EmptyStateProps) {
  return (
    <div className="border-border flex flex-col items-center gap-3 rounded-2xl border border-dashed px-6 py-16 text-center">
      {icon && <div className="text-content-muted">{icon}</div>}
      {badge}
      <h3 className="text-content text-base font-semibold tracking-tight">{title}</h3>
      {description && <p className="text-content-muted max-w-sm text-sm">{description}</p>}
      {action}
    </div>
  )
}
