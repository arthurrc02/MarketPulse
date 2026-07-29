import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { MenuIcon } from '@/components/icons/Icons'
import { IconButton } from '@/components/ui/IconButton'

describe('IconButton', () => {
  it('requires and exposes an accessible name via aria-label', () => {
    render(<IconButton icon={<MenuIcon />} aria-label="Abrir menu" />)

    expect(screen.getByRole('button', { name: 'Abrir menu' })).toBeInTheDocument()
  })

  it('calls onClick when pressed', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(<IconButton icon={<MenuIcon />} aria-label="Abrir menu" onClick={onClick} />)

    await user.click(screen.getByRole('button', { name: 'Abrir menu' }))

    expect(onClick).toHaveBeenCalledOnce()
  })

  it('shows a spinner and disables the button while loading', () => {
    render(<IconButton icon={<MenuIcon />} aria-label="Abrir menu" isLoading />)

    expect(screen.getByRole('button', { name: 'Abrir menu' })).toBeDisabled()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
