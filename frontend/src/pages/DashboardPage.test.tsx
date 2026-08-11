import { fireEvent, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as analyticsApi from '@/lib/analytics/api'
import type { AnalyticsOverview, TopProduct } from '@/lib/analytics/api'
import { ApiError } from '@/lib/apiClient'
import { DashboardPage } from '@/pages/DashboardPage'
import { renderWithProviders } from '@/test/renderWithProviders'

vi.mock('@/lib/analytics/api')

const mockedApi = vi.mocked(analyticsApi)

function makeOverview(overrides: Partial<AnalyticsOverview> = {}): AnalyticsOverview {
  return {
    revenue: 6500,
    orders: 3,
    averageOrderValue: 2166.67,
    activeProducts: 5,
    hasData: true,
    ...overrides,
  }
}

function makeTopProduct(overrides: Partial<TopProduct> = {}): TopProduct {
  return {
    productName: 'Camiseta Azul',
    sku: 'SKU-A',
    quantity: 4,
    revenue: 4000,
    orders: 2,
    ...overrides,
  }
}

function renderDashboard() {
  return renderWithProviders(
    <Routes>
      <Route path="/app" element={<DashboardPage />} />
      <Route path="/app/uploads" element={<div>UPLOADS_MARKER</div>} />
    </Routes>,
    { initialEntries: ['/app'] },
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedApi.getSalesOverTime.mockResolvedValue([])
  mockedApi.getOrdersByStatus.mockResolvedValue([])
  mockedApi.getTopProducts.mockResolvedValue([])
})

describe('DashboardPage', () => {
  it('greets the authenticated user', async () => {
    mockedApi.getOverview.mockResolvedValue(makeOverview())

    renderDashboard()

    expect(screen.getByText('Bem-vindo ao MarketPulse.')).toBeInTheDocument()
    expect(screen.getByText(/user@example\.com/)).toBeInTheDocument()
    await screen.findByText('R$ 6.500,00')
  })

  it('shows loading skeletons while the overview is pending, never a bare dash', () => {
    mockedApi.getOverview.mockReturnValue(new Promise(() => undefined))

    renderDashboard()

    expect(screen.getByText('Faturamento')).toBeInTheDocument()
    expect(screen.queryByText('—')).not.toBeInTheDocument()
  })

  it('shows the real KPI values once the overview resolves', async () => {
    mockedApi.getOverview.mockResolvedValue(makeOverview())

    renderDashboard()

    expect(await screen.findByText('R$ 6.500,00')).toBeInTheDocument()
    expect(screen.getByText('R$ 2.166,67')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('shows a distinct error message and never a silent dash when the request fails', async () => {
    mockedApi.getOverview.mockRejectedValue(new ApiError(500, 'Erro interno do servidor.'))

    renderDashboard()

    expect(await screen.findByText('Não foi possível carregar os indicadores.')).toBeInTheDocument()
    expect(screen.getByText('Erro interno do servidor.')).toBeInTheDocument()
    expect(screen.queryByText('—')).not.toBeInTheDocument()
    expect(screen.queryByText('Faturamento')).not.toBeInTheDocument()
  })

  it('retries the overview request when "Tentar novamente" is clicked', async () => {
    mockedApi.getOverview.mockRejectedValueOnce(new ApiError(500, 'Erro interno.'))
    mockedApi.getOverview.mockResolvedValueOnce(makeOverview())
    const user = userEvent.setup()

    renderDashboard()
    await screen.findByText('Tentar novamente')

    await user.click(screen.getByRole('button', { name: 'Tentar novamente' }))

    expect(await screen.findByText('R$ 6.500,00')).toBeInTheDocument()
    expect(mockedApi.getOverview).toHaveBeenCalledTimes(2)
  })

  it('shows the onboarding empty state when the user never imported anything', async () => {
    mockedApi.getOverview.mockResolvedValue(
      makeOverview({
        hasData: false,
        revenue: 0,
        orders: 0,
        averageOrderValue: 0,
        activeProducts: 0,
      }),
    )
    const user = userEvent.setup()

    renderDashboard()

    expect(await screen.findByText('Nenhum dado para exibir ainda')).toBeInTheDocument()
    expect(screen.queryByText('Faturamento')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Importar relatório' }))

    expect(await screen.findByText('UPLOADS_MARKER')).toBeInTheDocument()
  })

  it('shows real zero KPIs (not the onboarding empty state) when a filter matches no data', async () => {
    mockedApi.getOverview.mockResolvedValue(
      makeOverview({
        hasData: true,
        revenue: 0,
        orders: 0,
        averageOrderValue: 0,
        activeProducts: 0,
      }),
    )

    renderDashboard()

    // Aguarda o valor real (não só o rótulo, que aparece mesmo durante o loading).
    expect((await screen.findAllByText(/R\$\s*0,00/)).length).toBeGreaterThan(0)
    expect(screen.queryByText('Nenhum dado para exibir ainda')).not.toBeInTheDocument()
  })

  it('refetches with the new filter when the period changes', async () => {
    mockedApi.getOverview.mockResolvedValue(makeOverview())

    renderDashboard()
    await screen.findByText('R$ 6.500,00')

    fireEvent.change(screen.getByLabelText('De'), { target: { value: '2026-07-01' } })

    await screen.findByText('R$ 6.500,00')
    expect(mockedApi.getOverview).toHaveBeenLastCalledWith({ from: '2026-07-01' })
    expect(mockedApi.getSalesOverTime).toHaveBeenLastCalledWith({ from: '2026-07-01' })
  })

  it('refetches with the new filter when the marketplace changes', async () => {
    mockedApi.getOverview.mockResolvedValue(makeOverview())
    const user = userEvent.setup()

    renderDashboard()
    await screen.findByText('R$ 6.500,00')

    await user.selectOptions(screen.getByLabelText('Marketplace'), 'shopee')

    expect(mockedApi.getOverview).toHaveBeenLastCalledWith({ marketplace: 'shopee' })
  })

  it('renders the top products table with the data returned by the API', async () => {
    mockedApi.getOverview.mockResolvedValue(makeOverview())
    mockedApi.getTopProducts.mockResolvedValue([
      makeTopProduct({ sku: 'SKU-A', productName: 'Camiseta Azul' }),
      makeTopProduct({ sku: 'SKU-B', productName: 'Boné Preto' }),
    ])

    renderDashboard()

    expect(await screen.findByText('Camiseta Azul')).toBeInTheDocument()
    expect(screen.getByText('Boné Preto')).toBeInTheDocument()
  })

  it('renders chart section headings without asserting on Recharts internals', async () => {
    mockedApi.getOverview.mockResolvedValue(makeOverview())

    renderDashboard()

    expect(await screen.findByText('Faturamento ao longo do tempo')).toBeInTheDocument()
    expect(screen.getByText('Pedidos ao longo do tempo')).toBeInTheDocument()
    expect(screen.getByText('Pedidos por status')).toBeInTheDocument()
  })
})
