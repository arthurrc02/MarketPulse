import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderResult } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

import { AuthContext, type AuthContextValue } from '@/context/authContextDefinition'
import { ToastProvider } from '@/context/ToastContext'
import type { AuthUser } from '@/lib/auth/api'

export const SAMPLE_USER: AuthUser = {
  id: '1',
  email: 'user@example.com',
  isActive: true,
  createdAt: '2026-01-01T00:00:00Z',
}

interface RenderWithProvidersOptions {
  authValue?: Partial<AuthContextValue>
  initialEntries?: string[]
}

/**
 * Envolve `ui` com os providers reais que a árvore de rotas espera:
 * `MemoryRouter` (para `useNavigate`/`useLocation`/`NavLink`), um
 * `QueryClient` novo por teste (sem retry — uma falha simulada não deve
 * ficar tentando de novo e estourar o timeout do teste), `ToastProvider`
 * (real — não há bootstrap assíncrono a mockar) e um `AuthContext.Provider`
 * com valor controlável por teste (mocka apenas a autenticação, que tem
 * efeitos colaterais reais de rede).
 */
export function renderWithProviders(
  ui: ReactElement,
  { authValue, initialEntries = ['/'] }: RenderWithProvidersOptions = {},
): RenderResult {
  const value: AuthContextValue = {
    status: 'authenticated',
    user: SAMPLE_USER,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...authValue,
  }

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AuthContext.Provider value={value}>{ui}</AuthContext.Provider>
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}
