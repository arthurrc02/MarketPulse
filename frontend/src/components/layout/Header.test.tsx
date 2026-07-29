import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Header } from '@/components/layout/Header'
import type { AuthContextValue } from '@/context/authContextDefinition'
import { renderWithProviders } from '@/test/renderWithProviders'

function renderHeader(logout: AuthContextValue['logout'], onMenuClick = vi.fn()) {
  renderWithProviders(<Header onMenuClick={onMenuClick} />, { authValue: { logout } })
  return { onMenuClick }
}

describe('Header', () => {
  it('shows the authenticated user email', () => {
    renderHeader(vi.fn())

    expect(screen.getByText('user@example.com')).toBeInTheDocument()
  })

  it('calls onMenuClick when the mobile menu button is pressed', async () => {
    const user = userEvent.setup()
    const { onMenuClick } = renderHeader(vi.fn())

    await user.click(screen.getByRole('button', { name: 'Abrir menu de navegação' }))

    expect(onMenuClick).toHaveBeenCalledOnce()
  })

  it('opens the account menu with Configurações and Sair', async () => {
    const user = userEvent.setup()
    renderHeader(vi.fn())

    await user.click(screen.getByRole('button', { name: /user@example\.com/ }))

    expect(screen.getByRole('menuitem', { name: 'Configurações' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Sair' })).toBeInTheDocument()
  })

  it('asks for confirmation before logging out and completes on confirm', async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderHeader(logout)

    await user.click(screen.getByRole('button', { name: /user@example\.com/ }))
    await user.click(screen.getByRole('menuitem', { name: 'Sair' }))

    expect(screen.getByRole('dialog', { name: 'Encerrar sessão' })).toBeInTheDocument()
    expect(logout).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Sair' }))

    await waitFor(() => {
      expect(logout).toHaveBeenCalledOnce()
    })
    expect(await screen.findByText('Sessão encerrada com sucesso.')).toBeInTheDocument()
  })

  it('cancels the logout confirmation without calling logout', async () => {
    const logout = vi.fn()
    const user = userEvent.setup()
    renderHeader(logout)

    await user.click(screen.getByRole('button', { name: /user@example\.com/ }))
    await user.click(screen.getByRole('menuitem', { name: 'Sair' }))
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(logout).not.toHaveBeenCalled()
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})
