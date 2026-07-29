import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { MenuIcon } from '@/components/icons/Icons'
import { Dialog } from '@/components/ui/Dialog'
import { Dropdown } from '@/components/ui/Dropdown'
import { IconButton } from '@/components/ui/IconButton'
import { SearchInput } from '@/components/ui/SearchInput'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'

interface HeaderProps {
  onMenuClick: () => void
}

/** Barra superior: abre a sidebar no mobile, e concentra a conta do usuário. */
export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [isLogoutDialogOpen, setLogoutDialogOpen] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  async function handleConfirmLogout(): Promise<void> {
    setIsLoggingOut(true)
    try {
      await logout()
      showToast({ variant: 'success', message: 'Sessão encerrada com sucesso.' })
    } finally {
      setIsLoggingOut(false)
      setLogoutDialogOpen(false)
    }
  }

  const initials = user ? user.email.slice(0, 2).toUpperCase() : '··'

  return (
    <header className="border-border bg-surface/80 sticky top-0 z-30 flex h-16 shrink-0 items-center gap-4 border-b px-4 backdrop-blur-xl sm:px-6">
      <IconButton
        icon={<MenuIcon className="h-5 w-5" />}
        aria-label="Abrir menu de navegação"
        variant="ghost"
        className="lg:hidden"
        onClick={onMenuClick}
      />

      <div className="hidden max-w-sm flex-1 sm:block">
        <SearchInput aria-label="Buscar" placeholder="Buscar (em breve)" disabled />
      </div>
      <div className="flex-1 sm:hidden" />

      <Dropdown
        align="end"
        trigger={
          <button
            type="button"
            className="border-border bg-surface-elevated hover:border-border-focus flex items-center gap-2 rounded-full border py-1 pr-3 pl-1 text-sm transition-colors"
          >
            <span className="bg-primary text-primary-foreground flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold">
              {initials}
            </span>
            <span className="text-content hidden max-w-[10rem] truncate sm:inline">
              {user?.email}
            </span>
          </button>
        }
        items={[
          { label: 'Configurações', onSelect: () => void navigate('/app/settings') },
          {
            label: 'Sair',
            variant: 'danger',
            onSelect: () => {
              setLogoutDialogOpen(true)
            },
          },
        ]}
      />

      <Dialog
        isOpen={isLogoutDialogOpen}
        onClose={() => {
          setLogoutDialogOpen(false)
        }}
        title="Encerrar sessão"
        description="Você precisará entrar novamente para acessar sua conta."
        confirmLabel="Sair"
        cancelLabel="Cancelar"
        onConfirm={() => void handleConfirmLogout()}
        isConfirming={isLoggingOut}
      />
    </header>
  )
}
