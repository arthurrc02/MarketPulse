import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { Tooltip } from '@/components/ui/Tooltip'

describe('Tooltip', () => {
  it('is hidden until the trigger is hovered or focused', () => {
    render(
      <Tooltip content="Dica útil">
        <button type="button">Gatilho</button>
      </Tooltip>,
    )

    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('shows the tooltip on hover', async () => {
    const user = userEvent.setup()
    render(
      <Tooltip content="Dica útil">
        <button type="button">Gatilho</button>
      </Tooltip>,
    )

    await user.hover(screen.getByRole('button', { name: 'Gatilho' }))

    expect(await screen.findByRole('tooltip')).toHaveTextContent('Dica útil')
  })

  it('shows the tooltip on keyboard focus and hides it on blur', async () => {
    const user = userEvent.setup()
    render(
      <>
        <Tooltip content="Dica útil">
          <button type="button">Gatilho</button>
        </Tooltip>
        <button type="button">Outro</button>
      </>,
    )

    await user.tab()
    expect(await screen.findByRole('tooltip')).toBeInTheDocument()

    await user.tab()
    await waitFor(() => {
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    })
  })

  it('links the trigger to the tooltip via aria-describedby', async () => {
    const user = userEvent.setup()
    render(
      <Tooltip content="Dica útil">
        <button type="button">Gatilho</button>
      </Tooltip>,
    )

    const trigger = screen.getByRole('button', { name: 'Gatilho' })
    await user.hover(trigger)
    const tooltip = await screen.findByRole('tooltip')

    expect(trigger).toHaveAttribute('aria-describedby', tooltip.id)
  })
})
