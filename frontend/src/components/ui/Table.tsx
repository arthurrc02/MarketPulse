import type { ReactNode } from 'react'

import { ChevronDownIcon } from '@/components/icons/Icons'

export interface TableColumn<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  sortable?: boolean
  align?: 'left' | 'right'
}

export type SortDirection = 'asc' | 'desc'

interface TableProps<T> {
  columns: TableColumn<T>[]
  rows: T[]
  getRowKey: (row: T) => string
  onRowClick?: (row: T) => void
  sortKey?: string
  sortDirection?: SortDirection
  onSortChange?: (key: string) => void
}

/**
 * Tabela genérica e sem estado próprio: quem chama decide o que ordenar e
 * como — este componente só renderiza `rows` na ordem recebida e emite
 * `onSortChange` quando um cabeçalho ordenável é clicado.
 */
export function Table<T>({
  columns,
  rows,
  getRowKey,
  onRowClick,
  sortKey,
  sortDirection = 'desc',
  onSortChange,
}: TableProps<T>) {
  return (
    <div className="border-border overflow-x-auto rounded-2xl border">
      <table className="w-full min-w-[32rem] text-left text-sm">
        <thead>
          <tr className="border-border border-b">
            {columns.map((column) => {
              const isActive = column.key === sortKey
              const alignClass = column.align === 'right' ? 'text-right' : 'text-left'
              const ariaSort = isActive
                ? sortDirection === 'asc'
                  ? 'ascending'
                  : 'descending'
                : undefined
              return (
                <th
                  key={column.key}
                  scope="col"
                  aria-sort={column.sortable ? ariaSort : undefined}
                  className={['px-4 py-3', alignClass].join(' ')}
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      onClick={() => onSortChange?.(column.key)}
                      className="text-content-muted hover:text-content inline-flex items-center gap-1 font-medium transition-colors"
                    >
                      {column.header}
                      <ChevronDownIcon
                        className={[
                          'h-3.5 w-3.5 transition-transform',
                          isActive ? 'opacity-100' : 'opacity-0',
                          isActive && sortDirection === 'asc' ? 'rotate-180' : '',
                        ].join(' ')}
                      />
                    </button>
                  ) : (
                    <span className="text-content-muted font-medium">{column.header}</span>
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={getRowKey(row)}
              onClick={
                onRowClick
                  ? () => {
                      onRowClick(row)
                    }
                  : undefined
              }
              className={[
                'border-border/60 border-b last:border-b-0',
                onRowClick ? 'hover:bg-surface-elevated cursor-pointer transition-colors' : '',
              ].join(' ')}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={['px-4 py-3', column.align === 'right' ? 'text-right' : ''].join(' ')}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
