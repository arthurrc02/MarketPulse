import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AppLayout } from '@/components/layout/AppLayout'
import { renderWithProviders } from '@/test/renderWithProviders'

function renderAppLayout() {
  return renderWithProviders(
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<div>PAGE_CONTENT</div>} />
        <Route path="uploads" element={<div>UPLOADS_CONTENT</div>} />
      </Route>
    </Routes>,
    { initialEntries: ['/'] },
  )
}

describe('AppLayout', () => {
  it('renders the sidebar, header and the matched page content', () => {
    renderAppLayout()

    expect(screen.getByText('PAGE_CONTENT')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Dashboard/ })).toBeInTheDocument()
    expect(screen.getByText('user@example.com')).toBeInTheDocument()
  })

  it('opens the mobile sidebar drawer from the header menu button', async () => {
    const user = userEvent.setup()
    renderAppLayout()

    expect(screen.queryByTestId('sidebar-backdrop')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Abrir menu de navegação' }))

    expect(screen.getByTestId('sidebar-backdrop')).toBeInTheDocument()
  })
})
