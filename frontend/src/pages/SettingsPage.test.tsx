import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { SettingsPage } from '@/pages/SettingsPage'
import { renderWithProviders } from '@/test/renderWithProviders'

describe('SettingsPage', () => {
  it('shows the profile tab by default with the read-only e-mail', () => {
    renderWithProviders(<SettingsPage />)

    expect(screen.getByLabelText('E-mail')).toHaveValue('user@example.com')
    expect(screen.getByLabelText('E-mail')).toBeDisabled()
  })

  it('switches to the preferences tab and toggles a checkbox', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SettingsPage />)

    await user.click(screen.getByRole('tab', { name: 'Preferências' }))

    const notifications = screen.getByRole('checkbox', { name: /Notificações por e-mail/ })
    expect(notifications).toBeChecked()

    await user.click(notifications)

    expect(notifications).not.toBeChecked()
  })

  it('switches to the security tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SettingsPage />)

    await user.click(screen.getByRole('tab', { name: 'Segurança' }))

    expect(screen.getByText(/Troca de senha e autenticação em duas etapas/)).toBeInTheDocument()
  })
})
