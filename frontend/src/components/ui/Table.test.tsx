import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Table, type TableColumn } from '@/components/ui/Table'

interface Row {
  id: string
  name: string
  size: number
}

const ROWS: Row[] = [
  { id: '1', name: 'a.csv', size: 100 },
  { id: '2', name: 'b.csv', size: 200 },
]

const COLUMNS: TableColumn<Row>[] = [
  { key: 'name', header: 'Nome', render: (row) => row.name },
  {
    key: 'size',
    header: 'Tamanho',
    sortable: true,
    align: 'right',
    render: (row) => String(row.size),
  },
]

describe('Table', () => {
  it('renders a header and a row per item', () => {
    render(<Table columns={COLUMNS} rows={ROWS} getRowKey={(row) => row.id} />)

    expect(screen.getByRole('columnheader', { name: 'Nome' })).toBeInTheDocument()
    expect(screen.getByText('a.csv')).toBeInTheDocument()
    expect(screen.getByText('b.csv')).toBeInTheDocument()
  })

  it('calls onRowClick with the clicked row', async () => {
    const onRowClick = vi.fn()
    const user = userEvent.setup()
    render(
      <Table columns={COLUMNS} rows={ROWS} getRowKey={(row) => row.id} onRowClick={onRowClick} />,
    )

    await user.click(screen.getByText('a.csv'))

    expect(onRowClick).toHaveBeenCalledWith(ROWS[0])
  })

  it('calls onSortChange with the column key when a sortable header is clicked', async () => {
    const onSortChange = vi.fn()
    const user = userEvent.setup()
    render(
      <Table
        columns={COLUMNS}
        rows={ROWS}
        getRowKey={(row) => row.id}
        sortKey="size"
        sortDirection="desc"
        onSortChange={onSortChange}
      />,
    )

    await user.click(screen.getByRole('button', { name: /Tamanho/ }))

    expect(onSortChange).toHaveBeenCalledWith('size')
  })

  it('does not render a sort button for non-sortable columns', () => {
    render(<Table columns={COLUMNS} rows={ROWS} getRowKey={(row) => row.id} />)

    expect(screen.queryByRole('button', { name: /Nome/ })).not.toBeInTheDocument()
  })

  it('marks the active sort column with aria-sort', () => {
    render(
      <Table
        columns={COLUMNS}
        rows={ROWS}
        getRowKey={(row) => row.id}
        sortKey="size"
        sortDirection="asc"
        onSortChange={vi.fn()}
      />,
    )

    expect(screen.getByRole('columnheader', { name: /Tamanho/ })).toHaveAttribute(
      'aria-sort',
      'ascending',
    )
  })

  it('renders nothing extra when rows is empty', () => {
    render(<Table columns={COLUMNS} rows={[]} getRowKey={(row) => row.id} />)

    expect(screen.queryByRole('row', { name: /a\.csv/ })).not.toBeInTheDocument()
  })
})
