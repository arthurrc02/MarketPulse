import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { InsightsPage } from '@/pages/InsightsPage'
import { UploadsPage } from '@/pages/UploadsPage'
import { renderWithProviders } from '@/test/renderWithProviders'

describe('Placeholder pages', () => {
  it('UploadsPage points to Sprint 3', () => {
    renderWithProviders(<UploadsPage />)

    expect(screen.getByRole('heading', { name: 'Uploads' })).toBeInTheDocument()
    expect(screen.getByText('Sprint 3')).toBeInTheDocument()
  })

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
