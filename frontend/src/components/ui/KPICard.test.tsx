import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { KPICard } from '@/components/ui/KPICard'

describe('KPICard', () => {
  it('renders the label and value', () => {
    render(<KPICard label="Faturamento" value="R$ 12.345" />)

    expect(screen.getByText('Faturamento')).toBeInTheDocument()
    expect(screen.getByText('R$ 12.345')).toBeInTheDocument()
  })

  it('shows a skeleton instead of the value while loading', () => {
    render(<KPICard label="Faturamento" value="R$ 12.345" isLoading />)

    expect(screen.queryByText('R$ 12.345')).not.toBeInTheDocument()
  })

  it('renders the delta badge with the right tone per direction', () => {
    const { rerender } = render(
      <KPICard label="Pedidos" value="128" delta={{ value: '+12%', direction: 'up' }} />,
    )
    expect(screen.getByText('+12%')).toBeInTheDocument()

    rerender(<KPICard label="Pedidos" value="128" delta={{ value: '-4%', direction: 'down' }} />)
    expect(screen.getByText('-4%')).toBeInTheDocument()
  })

  it('shows the hint as a tooltip trigger with an accessible name', () => {
    render(<KPICard label="Faturamento" value="—" hint="Disponível em breve." />)

    expect(screen.getByRole('button', { name: 'Disponível em breve.' })).toBeInTheDocument()
  })

  it('does not show the delta badge while loading', () => {
    render(
      <KPICard label="Pedidos" value="128" isLoading delta={{ value: '+12%', direction: 'up' }} />,
    )

    expect(screen.queryByText('+12%')).not.toBeInTheDocument()
  })
})
