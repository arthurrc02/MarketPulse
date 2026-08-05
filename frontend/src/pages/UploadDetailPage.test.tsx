import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/apiClient'
import * as uploadsApi from '@/lib/uploads/api'
import type { UploadRecord } from '@/lib/uploads/api'
import { UploadDetailPage } from '@/pages/UploadDetailPage'
import { renderWithProviders } from '@/test/renderWithProviders'

vi.mock('@/lib/uploads/api')

const mockedUploadsApi = vi.mocked(uploadsApi)

function buildUploadRecord(overrides: Partial<UploadRecord> = {}): UploadRecord {
  return {
    id: 'abc-123',
    originalFilename: 'relatorio-vendas.csv',
    fileSize: 2048,
    mimeType: 'text/csv',
    status: 'uploaded',
    errorMessage: null,
    startedAt: null,
    finishedAt: null,
    uploadedAt: '2026-01-15T10:30:00Z',
    ...overrides,
  }
}

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
    mockedUploadsApi.getUpload.mockResolvedValue(buildUploadRecord())

    renderDetailPage()

    expect(await screen.findByText('relatorio-vendas.csv')).toBeInTheDocument()
    expect(screen.getByText('2.0 KB')).toBeInTheDocument()
    expect(screen.getByText('text/csv')).toBeInTheDocument()
    expect(screen.getByText('Enviado')).toBeInTheDocument()
  })

  it('fetches the upload identified by the route param', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue(
      buildUploadRecord({
        id: 'xyz-789',
        originalFilename: 'a.csv',
        fileSize: 10,
        uploadedAt: '2026-01-01T00:00:00Z',
      }),
    )

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
    mockedUploadsApi.getUpload.mockResolvedValue(
      buildUploadRecord({ originalFilename: 'a.csv', fileSize: 10 }),
    )
    const user = userEvent.setup()
    renderDetailPage()
    await screen.findByText('a.csv')

    await user.click(screen.getByRole('link', { name: /Voltar para uploads/ }))

    expect(await screen.findByText('LIST_MARKER')).toBeInTheDocument()
  })

  it('shows start, end and duration once the upload has been processed', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue(
      buildUploadRecord({
        status: 'processed',
        startedAt: '2026-01-15T10:30:00.000Z',
        finishedAt: '2026-01-15T10:30:02.500Z',
      }),
    )

    renderDetailPage()

    expect(await screen.findByText('Processado')).toBeInTheDocument()
    expect(screen.getByText('Início do processamento')).toBeInTheDocument()
    expect(screen.getByText('Fim do processamento')).toBeInTheDocument()
    expect(screen.getByText('2,5s')).toBeInTheDocument()
  })

  it('shows the error message inline when the upload failed', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue(
      buildUploadRecord({
        status: 'failed',
        errorMessage: 'Não foi possível identificar o marketplace de origem.',
        startedAt: '2026-01-15T10:30:00.000Z',
        finishedAt: '2026-01-15T10:30:01.000Z',
      }),
    )

    renderDetailPage()

    expect(await screen.findByText('Falhou')).toBeInTheDocument()
    expect(
      screen.getByText('Não foi possível identificar o marketplace de origem.'),
    ).toBeInTheDocument()
  })

  it('processes the upload and shows a success toast', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue(buildUploadRecord())
    mockedUploadsApi.processUpload.mockResolvedValue(buildUploadRecord({ status: 'processed' }))
    const user = userEvent.setup()
    renderDetailPage()
    await screen.findByText('relatorio-vendas.csv')

    await user.click(screen.getByRole('button', { name: 'Processar' }))

    expect(mockedUploadsApi.processUpload).toHaveBeenCalledWith('abc-123', expect.anything())
    expect(await screen.findByText('Arquivo processado com sucesso.')).toBeInTheDocument()
  })

  it('shows an error toast when processing fails', async () => {
    mockedUploadsApi.getUpload.mockResolvedValue(buildUploadRecord())
    mockedUploadsApi.processUpload.mockResolvedValue(
      buildUploadRecord({ status: 'failed', errorMessage: 'Arquivo corrompido.' }),
    )
    const user = userEvent.setup()
    renderDetailPage()
    await screen.findByText('relatorio-vendas.csv')

    await user.click(screen.getByRole('button', { name: 'Processar' }))

    expect(await screen.findByText('Arquivo corrompido.')).toBeInTheDocument()
  })

  it('polls while the upload is processing until it settles', async () => {
    mockedUploadsApi.getUpload
      .mockResolvedValueOnce(buildUploadRecord({ status: 'processing' }))
      .mockResolvedValue(buildUploadRecord({ status: 'processed' }))

    renderDetailPage()

    expect(await screen.findByText('Processando')).toBeInTheDocument()
    expect(await screen.findByText('Processado', {}, { timeout: 5000 })).toBeInTheDocument()
    expect(mockedUploadsApi.getUpload.mock.calls.length).toBeGreaterThan(1)
  })
})
