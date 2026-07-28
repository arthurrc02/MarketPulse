import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AppRoutes } from '@/routes/AppRoutes'

describe('AppRoutes', () => {
  it('redireciona rotas desconhecidas para a página temporária', () => {
    render(
      <MemoryRouter initialEntries={['/rota-inexistente']}>
        <AppRoutes />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { level: 1, name: 'MarketPulse' })).toBeInTheDocument()
  })
})
