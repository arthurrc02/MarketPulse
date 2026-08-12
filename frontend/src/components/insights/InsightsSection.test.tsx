import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { InsightsSection } from '@/components/insights/InsightsSection'
import * as insightsApi from '@/lib/insights/api'
import type { Insight } from '@/lib/insights/api'
import { ApiError } from '@/lib/apiClient'
import { renderWithProviders } from '@/test/renderWithProviders'

vi.mock('@/lib/insights/api')

const mockedApi = vi.mocked(insightsApi)

function makeInsight(overrides: Partial<Insight> = {}): Insight {
  return {
    id: 'revenue_trend',
    type: 'revenue_trend',
    title: 'Faturamento em alta',
    description: 'Seu faturamento cresceu 25,9% em relação ao período anterior.',
    severity: 'positive',
    value: 25.9,
    currentValue: 100,
    previousValue: 79.4,
    productName: null,
    sku: null,
    marketplace: null,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('InsightsSection', () => {
  it('shows loading skeletons while the request is pending', () => {
    mockedApi.getInsights.mockReturnValue(new Promise(() => undefined))

    renderWithProviders(<InsightsSection filters={{}} />)

    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.queryByText('Faturamento em alta')).not.toBeInTheDocument()
  })

  it('shows a distinct error message with a retry action', async () => {
    mockedApi.getInsights.mockRejectedValue(new ApiError(500, 'Erro interno.'))

    renderWithProviders(<InsightsSection filters={{}} />)

    expect(await screen.findByText('Não foi possível carregar os insights.')).toBeInTheDocument()
    expect(screen.getByText('Erro interno.')).toBeInTheDocument()
  })

  it('retries the request when "Tentar novamente" is clicked', async () => {
    mockedApi.getInsights.mockRejectedValueOnce(new ApiError(500, 'Erro interno.'))
    mockedApi.getInsights.mockResolvedValueOnce({ hasData: true, insights: [makeInsight()] })
    const user = userEvent.setup()

    renderWithProviders(<InsightsSection filters={{}} />)
    await screen.findByText('Tentar novamente')

    await user.click(screen.getByRole('button', { name: 'Tentar novamente' }))

    expect(await screen.findByText('Faturamento em alta')).toBeInTheDocument()
    expect(mockedApi.getInsights).toHaveBeenCalledTimes(2)
  })

  it('renders nothing extra when the user has no data at all', async () => {
    mockedApi.getInsights.mockResolvedValue({ hasData: false, insights: [] })

    renderWithProviders(<InsightsSection filters={{}} />)

    await vi.waitFor(() => {
      expect(mockedApi.getInsights).toHaveBeenCalled()
    })
    expect(
      screen.queryByText('Nenhum insight disponível para este período'),
    ).not.toBeInTheDocument()
  })

  it('shows the insufficient-data state when the user has data but no rule matched', async () => {
    mockedApi.getInsights.mockResolvedValue({ hasData: true, insights: [] })

    renderWithProviders(<InsightsSection filters={{}} />)

    expect(
      await screen.findByText('Nenhum insight disponível para este período'),
    ).toBeInTheDocument()
  })

  it('renders a card per insight with title, description and formatted value', async () => {
    mockedApi.getInsights.mockResolvedValue({
      hasData: true,
      insights: [
        makeInsight({
          id: 'revenue_trend',
          type: 'revenue_trend',
          title: 'Faturamento em alta',
          value: 25.9,
          severity: 'positive',
        }),
      ],
    })

    renderWithProviders(<InsightsSection filters={{}} />)

    expect(await screen.findByText('Faturamento em alta')).toBeInTheDocument()
    expect(
      screen.getByText('Seu faturamento cresceu 25,9% em relação ao período anterior.'),
    ).toBeInTheDocument()
    expect(screen.getByText('+25,9%')).toBeInTheDocument()
  })

  it('formats a negative insight with a minus sign', async () => {
    mockedApi.getInsights.mockResolvedValue({
      hasData: true,
      insights: [
        makeInsight({
          id: 'product_decline',
          type: 'product_decline',
          title: 'Queda de desempenho em produto',
          description: 'Produto X apresentou queda de 28,5% no faturamento.',
          severity: 'negative',
          value: -28.5,
        }),
      ],
    })

    renderWithProviders(<InsightsSection filters={{}} />)

    expect(await screen.findByText('-28,5%')).toBeInTheDocument()
  })

  it('formats a neutral (informational) insight without a sign', async () => {
    mockedApi.getInsights.mockResolvedValue({
      hasData: true,
      insights: [
        makeInsight({
          id: 'top_product',
          type: 'top_product',
          title: 'Produto em destaque',
          description: 'Produto Y foi responsável por 31,4% do faturamento no período.',
          severity: 'neutral',
          value: 31.4,
          productName: 'Produto Y',
          sku: 'SKU-Y',
        }),
      ],
    })

    renderWithProviders(<InsightsSection filters={{}} />)

    expect(await screen.findByText('31,4%')).toBeInTheDocument()
    expect(screen.queryByText('+31,4%')).not.toBeInTheDocument()
  })

  it('requests insights with the filters it received', () => {
    mockedApi.getInsights.mockResolvedValue({ hasData: true, insights: [] })

    renderWithProviders(
      <InsightsSection filters={{ from: '2026-07-01', to: '2026-07-10', marketplace: 'shopee' }} />,
    )

    expect(mockedApi.getInsights).toHaveBeenCalledWith({
      from: '2026-07-01',
      to: '2026-07-10',
      marketplace: 'shopee',
    })
  })
})
