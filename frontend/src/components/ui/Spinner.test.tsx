import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Spinner } from '@/components/ui/Spinner'

describe('Spinner', () => {
  it('announces a default loading label to assistive tech', () => {
    render(<Spinner />)

    expect(screen.getByRole('status')).toHaveTextContent('Carregando...')
  })

  it('accepts a custom label', () => {
    render(<Spinner label="Enviando arquivo..." />)

    expect(screen.getByRole('status')).toHaveTextContent('Enviando arquivo...')
  })
})
