import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FileUpload } from '@/components/ui/FileUpload'

function makeFile(name: string, type = 'text/csv'): File {
  return new File(['conteudo'], name, { type })
}

describe('FileUpload', () => {
  it('is a real button, so it is keyboard-focusable and operable by default', () => {
    render(<FileUpload onFilesSelected={vi.fn()} />)

    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('opens the hidden file input when clicked', async () => {
    const clickSpy = vi.spyOn(HTMLInputElement.prototype, 'click')
    const user = userEvent.setup()
    render(<FileUpload onFilesSelected={vi.fn()} />)

    await user.click(screen.getByRole('button'))

    expect(clickSpy).toHaveBeenCalled()
    clickSpy.mockRestore()
  })

  it('calls onFilesSelected when a file is chosen via the input', async () => {
    const onFilesSelected = vi.fn()
    const user = userEvent.setup()
    const { container } = render(<FileUpload onFilesSelected={onFilesSelected} />)

    const input = container.querySelector('input[type="file"]')
    expect(input).not.toBeNull()
    const file = makeFile('relatorio.csv')

    await user.upload(input as HTMLInputElement, file)

    expect(onFilesSelected).toHaveBeenCalledWith([file])
  })

  it('shows a dragging state on drag-enter and calls onFilesSelected on drop', () => {
    const onFilesSelected = vi.fn()
    render(<FileUpload onFilesSelected={onFilesSelected} />)
    const dropzone = screen.getByRole('button')
    const file = makeFile('vendas.xlsx')

    fireEvent.dragEnter(dropzone, { dataTransfer: { files: [file] } })
    expect(screen.getByText('Solte para enviar')).toBeInTheDocument()

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    expect(onFilesSelected).toHaveBeenCalledWith([file])
    expect(screen.queryByText('Solte para enviar')).not.toBeInTheDocument()
  })

  it('does not accept drops while disabled', () => {
    const onFilesSelected = vi.fn()
    render(<FileUpload onFilesSelected={onFilesSelected} disabled />)
    const dropzone = screen.getByRole('button')

    fireEvent.drop(dropzone, { dataTransfer: { files: [makeFile('a.csv')] } })

    expect(onFilesSelected).not.toHaveBeenCalled()
  })

  it('shows the provided hint text', () => {
    render(<FileUpload onFilesSelected={vi.fn()} hint="Só CSV ou XLSX, até 10 MB" />)

    expect(screen.getByText('Só CSV ou XLSX, até 10 MB')).toBeInTheDocument()
  })
})
