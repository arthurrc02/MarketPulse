import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from '@/App'

describe('App', () => {
  it('renderiza a página temporária na rota raiz', () => {
    render(<App />)

    expect(screen.getByRole('heading', { level: 1, name: 'MarketPulse' })).toBeInTheDocument()
  })

  it('informa que o projeto está em desenvolvimento', () => {
    render(<App />)

    expect(screen.getByText(/projeto em desenvolvimento/i)).toBeInTheDocument()
  })
})
