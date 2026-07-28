import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { App } from '@/App'

describe('App', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders the login page when there is no active session', async () => {
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Entrar no MarketPulse' }),
    ).toBeInTheDocument()
  })
})
