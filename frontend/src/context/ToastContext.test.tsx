import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ToastProvider } from '@/context/ToastContext'
import { useToast } from '@/hooks/useToast'

function TriggerButton({
  variant = 'info',
  message,
  durationMs,
}: {
  variant?: 'success' | 'error' | 'info'
  message: string
  durationMs?: number
}) {
  const { showToast } = useToast()
  return (
    <button
      type="button"
      onClick={() => {
        showToast(
          durationMs === undefined ? { variant, message } : { variant, message, durationMs },
        )
      }}
    >
      Disparar
    </button>
  )
}

describe('ToastProvider / useToast', () => {
  it('throws when useToast is used outside a ToastProvider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined)

    expect(() => render(<TriggerButton message="oi" />)).toThrow(
      'useToast deve ser usado dentro de um ToastProvider.',
    )

    consoleError.mockRestore()
  })

  it('shows a toast with role="status" for info/success variants', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <TriggerButton variant="success" message="Sessão encerrada com sucesso." />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Disparar' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Sessão encerrada com sucesso.')
  })

  it('shows a toast with role="alert" for the error variant', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <TriggerButton variant="error" message="Algo deu errado." />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Disparar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Algo deu errado.')
  })

  it('dismisses the toast when the close button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <TriggerButton variant="info" message="Mensagem informativa." />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Disparar' }))
    expect(await screen.findByText('Mensagem informativa.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Fechar notificação' }))

    await waitFor(() => {
      expect(screen.queryByText('Mensagem informativa.')).not.toBeInTheDocument()
    })
  })

  it('auto-dismisses after the given duration', async () => {
    // Duração real e curta em vez de fake timers: `userEvent` e as animações
    // do Framer Motion (requestAnimationFrame) não convivem bem com timers
    // falsos, e travam o teste em vez de falhar de forma clara.
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <TriggerButton variant="info" message="Some embora." durationMs={50} />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Disparar' }))
    expect(screen.getByText('Some embora.')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.queryByText('Some embora.')).not.toBeInTheDocument()
    })
  })
})
