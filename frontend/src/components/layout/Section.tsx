import type { ReactNode } from 'react'

interface SectionProps {
  title?: string
  description?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
}

/** Agrupa um bloco de conteúdo sob um título opcional, com espaço para ações. */
export function Section({ title, description, actions, children, className = '' }: SectionProps) {
  return (
    <section className={['flex flex-col gap-4', className].join(' ')}>
      {(title ?? actions) && (
        <div className="flex items-center justify-between gap-4">
          <div>
            {title && (
              <h2 className="text-content text-lg font-semibold tracking-tight">{title}</h2>
            )}
            {description && <p className="text-content-muted text-sm">{description}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  )
}
