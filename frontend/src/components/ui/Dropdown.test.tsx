import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Dropdown } from '@/components/ui/Dropdown'

function renderDropdown(onSelect = vi.fn()) {
  return render(
    <Dropdown
      trigger={<button type="button">Abrir menu</button>}
      items={[
        { label: 'Editar', onSelect },
        { label: 'Excluir', variant: 'danger', onSelect: vi.fn() },
      ]}
    />,
  )
}

describe('Dropdown', () => {
  it('is closed by default', () => {
    renderDropdown()

    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })

  it('opens the menu when the trigger is clicked', async () => {
    const user = userEvent.setup()
    renderDropdown()

    await user.click(screen.getByRole('button', { name: 'Abrir menu' }))

    expect(screen.getByRole('menu')).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Editar' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Excluir' })).toBeInTheDocument()
  })

  it('calls onSelect and closes the menu when an item is clicked', async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()
    renderDropdown(onSelect)

    await user.click(screen.getByRole('button', { name: 'Abrir menu' }))
    await user.click(screen.getByRole('menuitem', { name: 'Editar' }))

    expect(onSelect).toHaveBeenCalledOnce()
    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  it('closes on Escape', async () => {
    const user = userEvent.setup()
    renderDropdown()

    await user.click(screen.getByRole('button', { name: 'Abrir menu' }))
    expect(screen.getByRole('menu')).toBeInTheDocument()

    await user.keyboard('{Escape}')

    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  it('closes when clicking outside', async () => {
    const user = userEvent.setup()
    render(
      <div>
        <Dropdown
          trigger={<button type="button">Abrir menu</button>}
          items={[{ label: 'Item', onSelect: vi.fn() }]}
        />
        <button type="button">Fora</button>
      </div>,
    )

    await user.click(screen.getByRole('button', { name: 'Abrir menu' }))
    expect(screen.getByRole('menu')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Fora' }))

    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })
})
