import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/apiClient'
import * as uploadsApi from '@/lib/uploads/api'
import { UploadDetailPage } from '@/pages/UploadDetailPage'
import { renderWithProviders } from '@/test/renderWithProviders'

vi.mock('@/lib/uploads/api')

const mockedUploadsApi = vi.mocked(uploadsApi)

function renderDetailPage(id = 'abc-123') {
  return renderWithProviders(
    <Routes>
      <Route path="/app/uploads" element={<div>LIST_MARKER</div>} />
      <Route path="/app/uploads/:id" element={<UploadDetailPage />} />
    </Routes>,
    { initialEntries: [`/app/uploads/${id}`] },
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('UploadDetailPage', () => {
  it('shows a loading skeleton before the upload resolves', () => {
    mockedUploadsApi.getUpload.mockReturnValue(new Promise(() => undefined))

    renderDetailPage()

    expect(screen.getByText('Detalhes do upload')).toBeInTheDocument()
  })

  it('shows the upload metadata once loaded', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue({
      id: 'abc-123',
      originalFilename: 'relatorio-vendas.csv',
      fileSize: 2048,
      mimeType: 'text/csv',
      status: 'uploaded',
      uploadedAt: '2026-01-15T10:30:00Z',
    })

    renderDetailPage()

    expect(await screen.findByText('relatorio-vendas.csv')).toBeInTheDocument()
    expect(screen.getByText('2.0 KB')).toBeInTheDocument()
    expect(screen.getByText('text/csv')).toBeInTheDocument()
    expect(screen.getByText('Enviado')).toBeInTheDocument()
  })

  it('fetches the upload identified by the route param', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue({
      id: 'xyz-789',
      originalFilename: 'a.csv',
      fileSize: 10,
      mimeType: 'text/csv',
      status: 'uploaded',
      uploadedAt: '2026-01-01T00:00:00Z',
    })

    renderDetailPage('xyz-789')

    await screen.findByText('a.csv')
    expect(mockedUploadsApi.getUpload).toHaveBeenCalledWith('xyz-789')
  })

  it('shows a not-found state when the upload does not exist', async () => {
    mockedUploadsApi.getUpload.mockRejectedValue(new ApiError(404, 'Upload não encontrado.'))

    renderDetailPage()

    expect(await screen.findByText('Upload não encontrado')).toBeInTheDocument()
    expect(screen.getByText('Upload não encontrado.')).toBeInTheDocument()
  })

  it('navigates back to the uploads list via the back link', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue({
      id: 'abc-123',
      originalFilename: 'a.csv',
      fileSize: 10,
      mimeType: 'text/csv',
      status: 'uploaded',
      uploadedAt: '2026-01-01T00:00:00Z',
    })
    const user = userEvent.setup()
    renderDetailPage()
    await screen.findByText('a.csv')

    await user.click(screen.getByRole('link', { name: /Voltar para uploads/ }))

    expect(await screen.findByText('LIST_MARKER')).toBeInTheDocument()
  })
})
