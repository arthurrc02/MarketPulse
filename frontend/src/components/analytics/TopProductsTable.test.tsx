import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TopProductsTable } from '@/components/analytics/TopProductsTable'
import type { TopProduct } from '@/lib/analytics/api'

function makeProduct(overrides: Partial<TopProduct> = {}): TopProduct {
  return {
    productName: 'Camiseta Azul',
    sku: 'SKU-A',
    quantity: 4,
    revenue: 4000,
    orders: 2,
    ...overrides,
  }
}

describe('TopProductsTable', () => {
  it('shows a skeleton while loading', () => {
    render(<TopProductsTable data={[]} isLoading />)

    expect(screen.getByTestId('top-products-skeleton')).toBeInTheDocument()
  })

  it('shows an empty state when there are no products', () => {
    render(<TopProductsTable data={[]} isLoading={false} />)

    expect(screen.getByText('Nenhum produto ainda')).toBeInTheDocument()
  })

  it('renders every product with its formatted revenue', () => {
    render(
      <TopProductsTable
        data={[
          makeProduct({ sku: 'SKU-A', productName: 'Camiseta Azul', revenue: 4000 }),
          makeProduct({ sku: 'SKU-B', productName: 'Boné Preto', revenue: 1500 }),
        ]}
        isLoading={false}
      />,
    )

    expect(screen.getByText('Camiseta Azul')).toBeInTheDocument()
    expect(screen.getByText('SKU-A')).toBeInTheDocument()
    expect(screen.getByText('Boné Preto')).toBeInTheDocument()
    expect(screen.getByText(/R\$\s*4\.000,00/)).toBeInTheDocument()
  })
})
