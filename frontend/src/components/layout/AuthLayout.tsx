import type { ReactNode } from 'react'

import { Card } from '@/components/ui/Card'
import { Logo } from '@/components/ui/Logo'

interface AuthLayoutProps {
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
}

/** Layout compartilhado pelas telas de login e cadastro. */
export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div className="from-surface to-surface-elevated flex min-h-dvh items-center justify-center bg-gradient-to-b px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <Card>
          <div className="mb-6 space-y-1 text-center">
            <h1 className="text-content text-xl font-semibold tracking-tight">{title}</h1>
            {subtitle && <p className="text-content-muted text-sm">{subtitle}</p>}
          </div>
          {children}
        </Card>
        {footer && <div className="text-content-muted mt-6 text-center text-sm">{footer}</div>}
      </div>
    </div>
  )
}
