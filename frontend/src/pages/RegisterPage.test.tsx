import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextValue } from '@/context/authContextDefinition'
import { ApiError } from '@/lib/apiClient'
import { RegisterPage } from '@/pages/RegisterPage'

function renderRegisterPage(register: AuthContextValue['register']) {
  const value: AuthContextValue = {
    status: 'unauthenticated',
    user: null,
    login: vi.fn(),
    register,
    logout: vi.fn(),
  }

  return render(
    <MemoryRouter initialEntries={['/register']}>
      <AuthContext.Provider value={value}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/app" element={<div>DASHBOARD_MARKER</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('RegisterPage', () => {
  it('blocks submission when passwords do not match', async () => {
    const register = vi.fn()
    const user = userEvent.setup()
    renderRegisterPage(register)

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com')
    await user.type(screen.getByLabelText('Senha'), 'Sup3rSecret!')
    await user.type(screen.getByLabelText('Confirmar senha'), 'DifferentPass1')
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('As senhas não coincidem.')
    expect(register).not.toHaveBeenCalled()
  })

  it('registers and navigates to /app on success', async () => {
    const register = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderRegisterPage(register)

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com')
    await user.type(screen.getByLabelText('Senha'), 'Sup3rSecret!')
    await user.type(screen.getByLabelText('Confirmar senha'), 'Sup3rSecret!')
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(register).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Sup3rSecret!' })
    expect(await screen.findByText('DASHBOARD_MARKER')).toBeInTheDocument()
  })

  it('shows a server error message when registration fails', async () => {
    const register = vi.fn().mockRejectedValue(new ApiError(409, 'Este e-mail já está cadastrado.'))
    const user = userEvent.setup()
    renderRegisterPage(register)

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com')
    await user.type(screen.getByLabelText('Senha'), 'Sup3rSecret!')
    await user.type(screen.getByLabelText('Confirmar senha'), 'Sup3rSecret!')
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Este e-mail já está cadastrado.')
  })
})
