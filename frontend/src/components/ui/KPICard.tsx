import { Badge, type BadgeVariant } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { Tooltip } from '@/components/ui/Tooltip'
import { InfoIcon } from '@/components/icons/Icons'

interface KPIDelta {
  value: string
  direction: 'up' | 'down' | 'neutral'
}

interface KPICardProps {
  label: string
  value: string
  hint?: string
  delta?: KPIDelta
  isLoading?: boolean
}

const DELTA_VARIANT: Record<KPIDelta['direction'], BadgeVariant> = {
  up: 'success',
  down: 'danger',
  neutral: 'neutral',
}

/**
 * Estrutura visual apenas (Sprint 2) — nenhum dado real é calculado aqui.
 * Os indicadores de negócio chegam com o Analytics Dashboard (Sprint 5).
 */
export function KPICard({ label, value, hint, delta, isLoading = false }: KPICardProps) {
  return (
    <Card className="flex flex-col gap-3 p-6">
      <div className="flex items-center justify-between gap-2">
        <p className="text-content-muted text-sm font-medium">{label}</p>
        {hint && (
          <Tooltip content={hint}>
            <button
              type="button"
              className="text-content-muted hover:text-content"
              aria-label={hint}
            >
              <InfoIcon className="h-4 w-4" />
            </button>
          </Tooltip>
        )}
      </div>

      {isLoading ? (
        <Skeleton className="h-8 w-24" />
      ) : (
        <p className="text-content text-3xl font-semibold tracking-tight">{value}</p>
      )}

      {delta && !isLoading && <Badge variant={DELTA_VARIANT[delta.direction]}>{delta.value}</Badge>}
    </Card>
  )
}
