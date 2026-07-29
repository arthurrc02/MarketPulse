import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DashboardPage } from '@/pages/DashboardPage'
import { renderWithProviders } from '@/test/renderWithProviders'

describe('DashboardPage', () => {
  it('greets the authenticated user', () => {
    renderWithProviders(<DashboardPage />)

    expect(screen.getByText('Bem-vindo ao MarketPulse.')).toBeInTheDocument()
    expect(screen.getByText(/user@example\.com/)).toBeInTheDocument()
  })

  it('shows placeholder KPI cards with no real data', () => {
    renderWithProviders(<DashboardPage />)

    expect(screen.getByText('Faturamento')).toBeInTheDocument()
    expect(screen.getByText('Pedidos')).toBeInTheDocument()
    expect(screen.getByText('Ticket médio')).toBeInTheDocument()
    expect(screen.getByText('Produtos ativos')).toBeInTheDocument()
    expect(screen.getAllByText('—')).toHaveLength(4)
  })

  it('shows an empty state for recent activity', () => {
    renderWithProviders(<DashboardPage />)

    expect(screen.getByText('Nenhuma atividade ainda')).toBeInTheDocument()
    expect(screen.getByText('Disponível na Sprint 3')).toBeInTheDocument()
  })
})
