import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { AuthContextValue } from '@/context/authContextDefinition'
import { ApiError } from '@/lib/apiClient'
import { LoginPage } from '@/pages/LoginPage'
import { renderWithProviders } from '@/test/renderWithProviders'

function renderLoginPage(login: AuthContextValue['login']) {
  return renderWithProviders(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/app" element={<div>DASHBOARD_MARKER</div>} />
    </Routes>,
    {
      authValue: { status: 'unauthenticated', user: null, login },
      initialEntries: ['/login'],
    },
  )
}

describe('LoginPage', () => {
  it('renders the login form', () => {
    renderLoginPage(vi.fn())

    expect(screen.getByRole('heading', { name: 'Entrar no MarketPulse' })).toBeInTheDocument()
    expect(screen.getByLabelText('E-mail')).toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
  })

  it('logs in, shows a success toast and navigates to /app on success', async () => {
    const login = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderLoginPage(login)

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com')
    await user.type(screen.getByLabelText('Senha'), 'Sup3rSecret!')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(login).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Sup3rSecret!' })
    expect(await screen.findByText('Bem-vindo de volta!')).toBeInTheDocument()
    expect(await screen.findByText('DASHBOARD_MARKER')).toBeInTheDocument()
  })

  it('shows an error message when login fails', async () => {
    const login = vi.fn().mockRejectedValue(new ApiError(401, 'E-mail ou senha inválidos.'))
    const user = userEvent.setup()
    renderLoginPage(login)

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com')
    await user.type(screen.getByLabelText('Senha'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha inválidos.')
    expect(screen.queryByText('DASHBOARD_MARKER')).not.toBeInTheDocument()
  })
})
