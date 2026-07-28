import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import {
  AuthContext,
  type AuthContextValue,
  type AuthStatus,
} from '@/context/authContextDefinition'
import { AppRoutes } from '@/routes/AppRoutes'

function renderAppRoutes(status: AuthStatus, initialEntries: string[]) {
  const value: AuthContextValue = {
    status,
    user:
      status === 'authenticated'
        ? {
            id: '1',
            email: 'user@example.com',
            isActive: true,
            createdAt: '2026-01-01T00:00:00Z',
          }
        : null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthContext.Provider value={value}>
        <AppRoutes />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('AppRoutes', () => {
  it('shows a loading state while the session is being resolved', () => {
    renderAppRoutes('loading', ['/'])

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('redirects an unauthenticated user from "/" to the login page', async () => {
    renderAppRoutes('unauthenticated', ['/'])

    expect(
      await screen.findByRole('heading', { name: 'Entrar no MarketPulse' }),
    ).toBeInTheDocument()
  })

  it('redirects an authenticated user from "/" to the dashboard', async () => {
    renderAppRoutes('authenticated', ['/'])

    expect(await screen.findByText('Bem-vindo ao MarketPulse.')).toBeInTheDocument()
  })

  it('blocks direct access to /app without a session', async () => {
    renderAppRoutes('unauthenticated', ['/app'])

    expect(
      await screen.findByRole('heading', { name: 'Entrar no MarketPulse' }),
    ).toBeInTheDocument()
  })

  it('keeps an authenticated user away from /login', async () => {
    renderAppRoutes('authenticated', ['/login'])

    expect(await screen.findByText('Bem-vindo ao MarketPulse.')).toBeInTheDocument()
  })

  it('redirects unknown routes', async () => {
    renderAppRoutes('unauthenticated', ['/something-that-does-not-exist'])

    expect(
      await screen.findByRole('heading', { name: 'Entrar no MarketPulse' }),
    ).toBeInTheDocument()
  })
})
