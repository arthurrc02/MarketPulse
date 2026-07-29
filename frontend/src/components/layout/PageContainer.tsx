import type { ReactNode } from 'react'

interface PageContainerProps {
  children: ReactNode
  className?: string
}

/** Largura máxima e espaçamento padrão do conteúdo de uma página protegida. */
export function PageContainer({ children, className = '' }: PageContainerProps) {
  return (
    <div className={['mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-10', className].join(' ')}>
      {children}
    </div>
  )
}
