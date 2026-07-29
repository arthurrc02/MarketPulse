import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Button } from '@/components/ui/Button'

describe('Button', () => {
  it('renders its label and responds to clicks', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(<Button onClick={onClick}>Salvar</Button>)

    await user.click(screen.getByRole('button', { name: 'Salvar' }))

    expect(onClick).toHaveBeenCalledOnce()
  })

  it('disables the button and shows a spinner while loading', () => {
    render(<Button isLoading>Salvar</Button>)

    const button = screen.getByRole('button', { name: /Salvar/ })
    expect(button).toBeDisabled()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it.each(['primary', 'secondary', 'ghost', 'danger'] as const)(
    'renders without crashing for the %s variant',
    (variant) => {
      render(<Button variant={variant}>Ação</Button>)

      expect(screen.getByRole('button', { name: 'Ação' })).toBeInTheDocument()
    },
  )
})
