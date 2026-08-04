import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { InsightsPage } from '@/pages/InsightsPage'
import { renderWithProviders } from '@/test/renderWithProviders'

describe('Placeholder pages', () => {
  it('AnalyticsPage points to Sprint 5', () => {
    renderWithProviders(<AnalyticsPage />)

    expect(screen.getByRole('heading', { name: 'Analytics' })).toBeInTheDocument()
    expect(screen.getByText('Sprint 5')).toBeInTheDocument()
  })

  it('InsightsPage points to Sprint 6', () => {
    renderWithProviders(<InsightsPage />)

    expect(screen.getByRole('heading', { name: 'Insights' })).toBeInTheDocument()
    expect(screen.getByText('Sprint 6')).toBeInTheDocument()
  })
})
