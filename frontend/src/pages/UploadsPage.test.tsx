import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as uploadsApi from '@/lib/uploads/api'
import type { UploadRecord } from '@/lib/uploads/api'
import { UploadsPage } from '@/pages/UploadsPage'
import { renderWithProviders } from '@/test/renderWithProviders'

vi.mock('@/lib/uploads/api')

const mockedUploadsApi = vi.mocked(uploadsApi)

function makeUpload(overrides: Partial<UploadRecord> = {}): UploadRecord {
  return {
    id: '1',
    originalFilename: 'relatorio.csv',
    fileSize: 2048,
    mimeType: 'text/csv',
    status: 'uploaded',
    uploadedAt: '2026-01-01T10:00:00Z',
    ...overrides,
  }
}

function renderUploadsPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/app/uploads" element={<UploadsPage />} />
      <Route path="/app/uploads/:id" element={<div>DETAIL_MARKER</div>} />
    </Routes>,
    { initialEntries: ['/app/uploads'] },
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('UploadsPage', () => {
  it('shows a skeleton while the list is loading', () => {
    mockedUploadsApi.listUploads.mockReturnValue(new Promise(() => undefined))

    renderUploadsPage()

    expect(screen.getByTestId('uploads-skeleton')).toBeInTheDocument()
  })

  it('shows an empty state when there are no uploads', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([])

    renderUploadsPage()

    expect(await screen.findByText('Nenhum upload ainda')).toBeInTheDocument()
  })

  it('renders the uploads table once the list resolves', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([
      makeUpload({ id: '1', originalFilename: 'a.csv' }),
      makeUpload({ id: '2', originalFilename: 'b.csv' }),
    ])

    renderUploadsPage()

    expect(await screen.findByText('a.csv')).toBeInTheDocument()
    expect(screen.getByText('b.csv')).toBeInTheDocument()
  })

  it('filters the table by filename via the search field', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([
      makeUpload({ id: '1', originalFilename: 'vendas-janeiro.csv' }),
      makeUpload({ id: '2', originalFilename: 'estoque.xlsx' }),
    ])
    const user = userEvent.setup()
    renderUploadsPage()
    await screen.findByText('vendas-janeiro.csv')

    await user.type(screen.getByLabelText('Buscar por nome do arquivo'), 'vendas')

    expect(screen.getByText('vendas-janeiro.csv')).toBeInTheDocument()
    expect(screen.queryByText('estoque.xlsx')).not.toBeInTheDocument()
  })

  it('toggles the sort order when the date header is clicked', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([
      makeUpload({ id: '1', originalFilename: 'older.csv', uploadedAt: '2026-01-01T10:00:00Z' }),
      makeUpload({ id: '2', originalFilename: 'newer.csv', uploadedAt: '2026-02-01T10:00:00Z' }),
    ])
    const user = userEvent.setup()
    renderUploadsPage()
    await screen.findByText('older.csv')

    // Padrão é mais recente primeiro.
    let rows = screen.getAllByRole('row').slice(1)
    expect(rows[0]).toHaveTextContent('newer.csv')

    await user.click(screen.getByRole('button', { name: /Data/ }))

    rows = screen.getAllByRole('row').slice(1)
    expect(rows[0]).toHaveTextContent('older.csv')
  })

  it('uploads a selected file and shows a success toast', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([])
    mockedUploadsApi.createUpload.mockResolvedValue(makeUpload())
    const user = userEvent.setup()
    const { container } = renderUploadsPage()
    await screen.findByText('Nenhum upload ainda')

    const input = container.querySelector('input[type="file"]')
    const file = new File(['conteudo'], 'relatorio.csv', { type: 'text/csv' })
    await user.upload(input as HTMLInputElement, file)

    // `useMutation` chama `mutationFn` com (variáveis, contexto interno do
    // React Query) — por isso o segundo argumento é `expect.anything()`.
    expect(mockedUploadsApi.createUpload).toHaveBeenCalledWith(file, expect.anything())
    expect(await screen.findByText('relatorio.csv enviado com sucesso.')).toBeInTheDocument()
  })

  it('shows an error toast when the upload fails', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([])
    mockedUploadsApi.createUpload.mockRejectedValue(new Error('network down'))
    const user = userEvent.setup()
    const { container } = renderUploadsPage()
    await screen.findByText('Nenhum upload ainda')

    const input = container.querySelector('input[type="file"]')
    const file = new File(['conteudo'], 'relatorio.csv', { type: 'text/csv' })
    await user.upload(input as HTMLInputElement, file)

    expect(await screen.findByText('Falha ao enviar relatorio.csv.')).toBeInTheDocument()
    expect(screen.getByText('Não foi possível enviar o arquivo.')).toBeInTheDocument()
  })

  it('deletes an upload after confirming the dialog', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([makeUpload({ originalFilename: 'a.csv' })])
    mockedUploadsApi.deleteUpload.mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderUploadsPage()
    await screen.findByText('a.csv')

    await user.click(screen.getByRole('button', { name: 'Excluir a.csv' }))
    expect(screen.getByRole('dialog', { name: 'Excluir upload' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Excluir' }))

    await waitFor(() => {
      expect(mockedUploadsApi.deleteUpload).toHaveBeenCalledWith('1', expect.anything())
    })
    expect(await screen.findByText('a.csv excluído.')).toBeInTheDocument()
  })

  it('closes the delete dialog without deleting when cancelled', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([makeUpload({ originalFilename: 'a.csv' })])
    const user = userEvent.setup()
    renderUploadsPage()
    await screen.findByText('a.csv')

    await user.click(screen.getByRole('button', { name: 'Excluir a.csv' }))
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))

    await waitForElementToBeRemoved(() => screen.queryByRole('dialog'))
    expect(mockedUploadsApi.deleteUpload).not.toHaveBeenCalled()
  })

  it('navigates to the detail page when a row name is clicked', async () => {
    mockedUploadsApi.listUploads.mockResolvedValue([makeUpload({ originalFilename: 'a.csv' })])
    const user = userEvent.setup()
    renderUploadsPage()
    await screen.findByText('a.csv')

    await user.click(screen.getByRole('link', { name: 'a.csv' }))

    expect(await screen.findByText('DETAIL_MARKER')).toBeInTheDocument()
  })
})
