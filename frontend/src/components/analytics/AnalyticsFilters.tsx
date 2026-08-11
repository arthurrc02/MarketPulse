import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import type { AnalyticsFilters as Filters, Marketplace } from '@/lib/analytics/api'

interface AnalyticsFiltersProps {
  value: Filters
  onChange: (value: Filters) => void
}

const MARKETPLACE_OPTIONS: { value: Marketplace; label: string }[] = [
  { value: 'shopee', label: 'Shopee' },
  { value: 'mercado_livre', label: 'Mercado Livre' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'magalu', label: 'Magalu' },
]

/** `exactOptionalPropertyTypes` exige omitir a chave, não setá-la como `undefined`. */
function withOptionalField<K extends keyof Filters>(
  value: Filters,
  key: K,
  next: Filters[K] | undefined,
): Filters {
  const rest = Object.fromEntries(
    Object.entries(value).filter(([entryKey]) => entryKey !== key),
  ) as Filters
  return next === undefined ? rest : { ...rest, [key]: next }
}

/**
 * Período (de/até) e marketplace. Cada mudança chama `onChange` com o
 * filtro completo — quem decide o que fazer com ele (refazer as buscas via
 * React Query) é a página, não este componente.
 */
export function AnalyticsFilters({ value, onChange }: AnalyticsFiltersProps) {
  return (
    <div className="flex flex-wrap items-end gap-4">
      <Input
        type="date"
        label="De"
        value={value.from ?? ''}
        max={value.to}
        onChange={(event) => {
          onChange(withOptionalField(value, 'from', event.target.value || undefined))
        }}
        className="w-40"
      />
      <Input
        type="date"
        label="Até"
        value={value.to ?? ''}
        min={value.from}
        onChange={(event) => {
          onChange(withOptionalField(value, 'to', event.target.value || undefined))
        }}
        className="w-40"
      />
      <Select
        label="Marketplace"
        placeholder="Todos"
        options={MARKETPLACE_OPTIONS}
        onChange={(event) => {
          const selected = event.target.value
          onChange(
            withOptionalField(
              value,
              'marketplace',
              selected ? (selected as Marketplace) : undefined,
            ),
          )
        }}
        className="w-48"
      />
    </div>
  )
}
