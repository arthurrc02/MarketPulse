import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { SearchInput } from '@/components/ui/SearchInput'

describe('SearchInput', () => {
  it('renders with the given accessible name', () => {
    render(<SearchInput aria-label="Buscar" placeholder="Buscar" />)

    expect(screen.getByRole('searchbox', { name: 'Buscar' })).toBeInTheDocument()
  })

  it('calls onChange as the user types', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<SearchInput aria-label="Buscar" value="" onChange={onChange} />)

    await user.type(screen.getByRole('searchbox'), 'abc')

    expect(onChange).toHaveBeenCalledTimes(3)
  })

  it('does not show the clear button when there is no value', () => {
    render(<SearchInput aria-label="Buscar" value="" onChange={vi.fn()} onClear={vi.fn()} />)

    expect(screen.queryByRole('button', { name: 'Limpar busca' })).not.toBeInTheDocument()
  })

  it('shows the clear button with a value and calls onClear when clicked', async () => {
    const onClear = vi.fn()
    const user = userEvent.setup()
    render(<SearchInput aria-label="Buscar" value="produto" onChange={vi.fn()} onClear={onClear} />)

    const clearButton = screen.getByRole('button', { name: 'Limpar busca' })
    await user.click(clearButton)

    expect(onClear).toHaveBeenCalledOnce()
  })
})
