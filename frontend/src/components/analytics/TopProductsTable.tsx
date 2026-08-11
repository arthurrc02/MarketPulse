import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { Table, type TableColumn } from '@/components/ui/Table'
import { formatCurrency } from '@/lib/format'
import type { TopProduct } from '@/lib/analytics/api'

interface TopProductsTableProps {
  data: TopProduct[]
  isLoading: boolean
}

const COLUMNS: TableColumn<TopProduct>[] = [
  {
    key: 'product',
    header: 'Produto',
    render: (row) => (
      <div>
        <p className="text-content font-medium">{row.productName}</p>
        <p className="text-content-muted text-xs">{row.sku}</p>
      </div>
    ),
  },
  { key: 'quantity', header: 'Quantidade', align: 'right', render: (row) => row.quantity },
  { key: 'orders', header: 'Pedidos', align: 'right', render: (row) => row.orders },
  {
    key: 'revenue',
    header: 'Faturamento',
    align: 'right',
    render: (row) => formatCurrency(row.revenue),
  },
]

/** Produtos com maior faturamento (só pedidos `completed`) — o backend já ordena e limita. */
export function TopProductsTable({ data, isLoading }: TopProductsTableProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-2" data-testid="top-products-skeleton">
        {[0, 1, 2].map((row) => (
          <Skeleton key={row} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <EmptyState
        title="Nenhum produto ainda"
        description="Assim que houver pedidos concluídos, os produtos com maior faturamento aparecem aqui."
      />
    )
  }

  return <Table columns={COLUMNS} rows={data} getRowKey={(row) => row.sku} />
}
