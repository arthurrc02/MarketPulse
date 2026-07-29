import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Select } from '@/components/ui/Select'

const OPTIONS = [
  { value: 'utc', label: 'UTC' },
  { value: 'sp', label: 'América/São Paulo (GMT-3)' },
]

describe('Select', () => {
  it('renders the label and every option', () => {
    render(<Select label="Fuso horário" options={OPTIONS} />)

    const select = screen.getByLabelText('Fuso horário')
    expect(select).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'UTC' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'América/São Paulo (GMT-3)' })).toBeInTheDocument()
  })

  it('shows a disabled placeholder option when provided', () => {
    // A opção placeholder usa o atributo `hidden`, removendo-a da árvore de
    // acessibilidade por design (não deve aparecer na lista de opções do
    // usuário) — por isso é verificada via DOM, não via `getByRole`.
    const { container } = render(
      <Select label="Fuso horário" placeholder="Selecione" options={OPTIONS} />,
    )

    const placeholderOption = container.querySelector('option[value=""]')
    expect(placeholderOption).not.toBeNull()
    expect(placeholderOption).toBeDisabled()
    expect(placeholderOption).toHaveTextContent('Selecione')
  })

  it('calls onChange with the selected value', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<Select label="Fuso horário" options={OPTIONS} onChange={onChange} />)

    await user.selectOptions(screen.getByLabelText('Fuso horário'), 'sp')

    expect(onChange).toHaveBeenCalled()
    expect(screen.getByLabelText('Fuso horário')).toHaveValue('sp')
  })

  it('shows the error message and marks the field as invalid', () => {
    render(<Select label="Fuso horário" options={OPTIONS} error="Selecione um fuso horário." />)

    expect(screen.getByRole('alert')).toHaveTextContent('Selecione um fuso horário.')
    expect(screen.getByLabelText('Fuso horário')).toHaveAttribute('aria-invalid', 'true')
  })
})
