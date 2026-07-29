import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { AuthStatus } from '@/context/authContextDefinition'
import { AppRoutes } from '@/routes/AppRoutes'
import { SAMPLE_USER, renderWithProviders } from '@/test/renderWithProviders'

function renderAppRoutes(status: AuthStatus, initialEntries: string[]) {
  return renderWithProviders(<AppRoutes />, {
    authValue: {
      status,
      user: status === 'authenticated' ? SAMPLE_USER : null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    },
    initialEntries,
  })
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

  it('redirects an authenticated user from "/" to the dashboard, inside the app layout', async () => {
    renderAppRoutes('authenticated', ['/'])

    expect(await screen.findByText('Bem-vindo ao MarketPulse.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Dashboard/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Uploads/ })).toBeInTheDocument()
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

  it('navigates to a nested page via the sidebar', async () => {
    const user = userEvent.setup()
    renderAppRoutes('authenticated', ['/app'])

    await user.click(await screen.findByRole('link', { name: /Uploads/ }))

    expect(
      await screen.findByText('Upload de arquivos ainda não está disponível'),
    ).toBeInTheDocument()
  })
})
