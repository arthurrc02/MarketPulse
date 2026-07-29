import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Modal } from '@/components/ui/Modal'

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()} title="Título">
        <p>Conteúdo</p>
      </Modal>,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders the dialog with an accessible name from the title', () => {
    render(
      <Modal isOpen onClose={vi.fn()} title="Confirmar ação">
        <p>Conteúdo</p>
      </Modal>,
    )

    expect(screen.getByRole('dialog', { name: 'Confirmar ação' })).toBeInTheDocument()
    expect(screen.getByText('Conteúdo')).toBeInTheDocument()
  })

  it('closes on Escape', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      <Modal isOpen onClose={onClose} title="Título">
        <p>Conteúdo</p>
      </Modal>,
    )

    await user.keyboard('{Escape}')

    expect(onClose).toHaveBeenCalledOnce()
  })

  it('closes when the backdrop is clicked', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      <Modal isOpen onClose={onClose} title="Título">
        <p>Conteúdo</p>
      </Modal>,
    )

    await user.click(screen.getByTestId('modal-backdrop'))

    expect(onClose).toHaveBeenCalledOnce()
  })

  it('does not close when the dialog content itself is clicked', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      <Modal isOpen onClose={onClose} title="Título">
        <p>Conteúdo</p>
      </Modal>,
    )

    await user.click(screen.getByText('Conteúdo'))

    expect(onClose).not.toHaveBeenCalled()
  })
})
