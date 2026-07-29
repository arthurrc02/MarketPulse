import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Dialog } from '@/components/ui/Dialog'

describe('Dialog', () => {
  it('renders title, description and the default action labels', () => {
    render(
      <Dialog
        isOpen
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Excluir item"
        description="Essa ação não pode ser desfeita."
      />,
    )

    expect(screen.getByRole('dialog', { name: 'Excluir item' })).toBeInTheDocument()
    expect(screen.getByText('Essa ação não pode ser desfeita.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirmar' })).toBeInTheDocument()
  })

  it('calls onConfirm and onClose from their respective buttons', async () => {
    const onConfirm = vi.fn()
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<Dialog isOpen onClose={onClose} onConfirm={onConfirm} title="Título" />)

    await user.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(onConfirm).toHaveBeenCalledOnce()

    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('disables both actions while confirming', () => {
    render(<Dialog isOpen onClose={vi.fn()} onConfirm={vi.fn()} title="Título" isConfirming />)

    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Confirmar/ })).toBeDisabled()
  })

  it('uses custom labels when provided', () => {
    render(
      <Dialog
        isOpen
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Encerrar sessão"
        confirmLabel="Sair"
        cancelLabel="Ficar"
      />,
    )

    expect(screen.getByRole('button', { name: 'Sair' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ficar' })).toBeInTheDocument()
  })
})
