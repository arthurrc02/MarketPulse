import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Badge } from '@/components/ui/Badge'

describe('Badge', () => {
  it('renders its content', () => {
    render(<Badge>Novo</Badge>)

    expect(screen.getByText('Novo')).toBeInTheDocument()
  })

  it.each(['neutral', 'primary', 'success', 'danger'] as const)(
    'renders without crashing for the %s variant',
    (variant) => {
      render(<Badge variant={variant}>Rótulo</Badge>)

      expect(screen.getByText('Rótulo')).toBeInTheDocument()
    },
  )
})
