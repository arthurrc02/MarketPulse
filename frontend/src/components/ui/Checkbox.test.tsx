import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Checkbox } from '@/components/ui/Checkbox'

describe('Checkbox', () => {
  it('renders the label and description', () => {
    render(<Checkbox label="Notificações por e-mail" description="Resumo semanal." />)

    expect(screen.getByRole('checkbox', { name: /Notificações por e-mail/ })).toBeInTheDocument()
    expect(screen.getByText('Resumo semanal.')).toBeInTheDocument()
  })

  it('toggles when clicking the label text', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<Checkbox label="Aceitar termos" checked={false} onChange={onChange} />)

    await user.click(screen.getByText('Aceitar termos'))

    expect(onChange).toHaveBeenCalledOnce()
  })

  it('reflects the checked state', () => {
    render(<Checkbox label="Aceitar termos" checked readOnly />)

    expect(screen.getByRole('checkbox', { name: 'Aceitar termos' })).toBeChecked()
  })

  it('is keyboard accessible via the space key', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<Checkbox label="Aceitar termos" checked={false} onChange={onChange} />)

    screen.getByRole('checkbox').focus()
    await user.keyboard(' ')

    expect(onChange).toHaveBeenCalledOnce()
  })
})
