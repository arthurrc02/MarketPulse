import { useState } from 'react'

import { Button } from '@/components/ui/Button'
import { Logo } from '@/components/ui/Logo'
import { useAuth } from '@/hooks/useAuth'

/**
 * Página protegida temporária da Sprint 1.
 *
 * Substituída pelo dashboard real na Sprint 5 (Analytics Dashboard) — nenhum
 * gráfico ou indicador pertence a esta sprint.
 */
export function DashboardPage() {
  const { user, logout } = useAuth()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  async function handleLogout(): Promise<void> {
    setIsLoggingOut(true)
    try {
      await logout()
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-border flex items-center justify-between border-b px-6 py-4">
        <Logo />
        <Button variant="secondary" onClick={() => void handleLogout()} isLoading={isLoggingOut}>
          Sair
        </Button>
      </header>
      <main className="flex flex-1 flex-col items-center justify-center gap-2 px-6 text-center">
        <h1 className="text-content text-3xl font-semibold tracking-tight">
          Bem-vindo ao MarketPulse.
        </h1>
        {user && <p className="text-content-muted text-sm">Conectado como {user.email}</p>}
      </main>
    </div>
  )
}
