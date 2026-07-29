import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'

describe('EmptyState', () => {
  it('renders the title and description', () => {
    render(<EmptyState title="Nada por aqui" description="Ainda não há dados." />)

    expect(screen.getByRole('heading', { name: 'Nada por aqui' })).toBeInTheDocument()
    expect(screen.getByText('Ainda não há dados.')).toBeInTheDocument()
  })

  it('renders optional icon, badge and action slots', () => {
    render(
      <EmptyState
        title="Nada por aqui"
        icon={<span data-testid="icon">icon</span>}
        badge={<Badge variant="primary">Sprint 3</Badge>}
        action={<button type="button">Ação</button>}
      />,
    )

    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('Sprint 3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ação' })).toBeInTheDocument()
  })
})
