import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { Tabs } from '@/components/ui/Tabs'

const TABS = [
  { id: 'profile', label: 'Perfil', content: <p>Conteúdo do perfil</p> },
  { id: 'security', label: 'Segurança', content: <p>Conteúdo de segurança</p> },
  { id: 'billing', label: 'Cobrança', content: <p>Conteúdo de cobrança</p> },
]

describe('Tabs', () => {
  it('shows the first tab selected by default', () => {
    render(<Tabs tabs={TABS} />)

    expect(screen.getByRole('tab', { name: 'Perfil' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('Conteúdo do perfil')).toBeVisible()
  })

  it('switches tabs on click', async () => {
    const user = userEvent.setup()
    render(<Tabs tabs={TABS} />)

    await user.click(screen.getByRole('tab', { name: 'Segurança' }))

    expect(screen.getByRole('tab', { name: 'Segurança' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Perfil' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByText('Conteúdo de segurança')).toBeVisible()
  })

  it('moves focus and selection with the arrow keys', async () => {
    const user = userEvent.setup()
    render(<Tabs tabs={TABS} />)

    screen.getByRole('tab', { name: 'Perfil' }).focus()
    await user.keyboard('{ArrowRight}')

    expect(screen.getByRole('tab', { name: 'Segurança' })).toHaveFocus()
    expect(screen.getByRole('tab', { name: 'Segurança' })).toHaveAttribute('aria-selected', 'true')

    await user.keyboard('{ArrowLeft}')
    expect(screen.getByRole('tab', { name: 'Perfil' })).toHaveFocus()
  })

  it('wraps around when moving past the last tab', async () => {
    const user = userEvent.setup()
    render(<Tabs tabs={TABS} />)

    screen.getByRole('tab', { name: 'Cobrança' }).focus()
    await user.keyboard('{ArrowRight}')

    expect(screen.getByRole('tab', { name: 'Perfil' })).toHaveFocus()
  })

  it('hides the panels of inactive tabs from the accessibility tree', () => {
    render(<Tabs tabs={TABS} />)

    expect(screen.getByText('Conteúdo do perfil')).toBeVisible()
    expect(screen.queryByText('Conteúdo de segurança')).not.toBeInTheDocument()
  })
})
