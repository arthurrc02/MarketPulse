import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { AnalyticsFilters } from '@/components/analytics/AnalyticsFilters'

describe('AnalyticsFilters', () => {
  it('calls onChange with the new "from" date, keeping other fields', () => {
    const onChange = vi.fn()
    render(<AnalyticsFilters value={{ marketplace: 'shopee' }} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('De'), { target: { value: '2026-07-01' } })

    expect(onChange).toHaveBeenCalledWith({ marketplace: 'shopee', from: '2026-07-01' })
  })

  it('calls onChange with the new "to" date', () => {
    const onChange = vi.fn()
    render(<AnalyticsFilters value={{}} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Até'), { target: { value: '2026-07-31' } })

    expect(onChange).toHaveBeenCalledWith({ to: '2026-07-31' })
  })

  it('calls onChange with the selected marketplace', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<AnalyticsFilters value={{}} onChange={onChange} />)

    await user.selectOptions(screen.getByLabelText('Marketplace'), 'mercado_livre')

    expect(onChange).toHaveBeenCalledWith({ marketplace: 'mercado_livre' })
  })

  it('omits the field entirely when a date is cleared', () => {
    const onChange = vi.fn()
    render(<AnalyticsFilters value={{ from: '2026-07-01' }} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('De'), { target: { value: '' } })

    const call = onChange.mock.calls[0]?.[0] as Record<string, unknown> | undefined
    expect(call).toBeDefined()
    expect(Object.hasOwn(call ?? {}, 'from')).toBe(false)
  })
})
