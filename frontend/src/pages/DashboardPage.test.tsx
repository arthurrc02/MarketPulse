import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextValue } from '@/context/authContextDefinition'
import { DashboardPage } from '@/pages/DashboardPage'

function renderDashboard(logout: AuthContextValue['logout']) {
  const value: AuthContextValue = {
    status: 'authenticated',
    user: {
      id: '1',
      email: 'user@example.com',
      isActive: true,
      createdAt: '2026-01-01T00:00:00Z',
    },
    login: vi.fn(),
    register: vi.fn(),
    logout,
  }

  return render(
    <MemoryRouter>
      <AuthContext.Provider value={value}>
        <DashboardPage />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('DashboardPage', () => {
  it('greets the authenticated user', () => {
    renderDashboard(vi.fn())

    expect(screen.getByText('Bem-vindo ao MarketPulse.')).toBeInTheDocument()
    expect(screen.getByText(/user@example\.com/)).toBeInTheDocument()
  })

  it('calls logout when clicking "Sair"', async () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderDashboard(logout)

    await user.click(screen.getByRole('button', { name: 'Sair' }))

    expect(logout).toHaveBeenCalledOnce()
  })
})
