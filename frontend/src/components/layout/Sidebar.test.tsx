import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { Sidebar } from '@/components/layout/Sidebar'

function renderSidebar(isOpen: boolean, onClose = vi.fn(), initialEntries = ['/app']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Sidebar isOpen={isOpen} onClose={onClose} />
    </MemoryRouter>,
  )
}

describe('Sidebar', () => {
  it('renders every navigation item', () => {
    renderSidebar(false)

    expect(screen.getByRole('link', { name: /Dashboard/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Uploads/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Analytics/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Insights/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Configurações/ })).toBeInTheDocument()
  })

  it('marks the current route as the active nav item', () => {
    renderSidebar(false, vi.fn(), ['/app/uploads'])

    expect(screen.getByRole('link', { name: /Uploads/ })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: /Dashboard/ })).not.toHaveAttribute('aria-current')
  })

  it('does not show the mobile backdrop when closed', () => {
    renderSidebar(false)

    expect(screen.queryByTestId('sidebar-backdrop')).not.toBeInTheDocument()
  })

  it('closes when a nav link is clicked (mobile drawer behavior)', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    renderSidebar(true, onClose)

    await user.click(screen.getByRole('link', { name: /Uploads/ }))

    expect(onClose).toHaveBeenCalledOnce()
  })

  it('closes when the backdrop is clicked', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    renderSidebar(true, onClose)

    await user.click(screen.getByTestId('sidebar-backdrop'))

    expect(onClose).toHaveBeenCalledOnce()
  })
})
