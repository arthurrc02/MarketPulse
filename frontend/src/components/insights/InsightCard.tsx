import { motion } from 'framer-motion'

import { SparkleIcon, TrendDownIcon, TrendUpIcon } from '@/components/icons/Icons'
import { Card } from '@/components/ui/Card'
import type { Insight, InsightSeverity } from '@/lib/insights/api'

type IconComponent = typeof TrendUpIcon

const SEVERITY_ICON: Record<InsightSeverity, IconComponent> = {
  positive: TrendUpIcon,
  negative: TrendDownIcon,
  neutral: SparkleIcon,
}

const SEVERITY_BADGE_CLASS: Record<InsightSeverity, string> = {
  positive: 'bg-emerald-500/10 text-emerald-400',
  negative: 'bg-danger/10 text-danger',
  neutral: 'bg-primary/10 text-primary',
}

const SEVERITY_VALUE_CLASS: Record<InsightSeverity, string> = {
  positive: 'text-emerald-400',
  negative: 'text-danger',
  neutral: 'text-content',
}

/** `+25,9%` / `-14,3%` / `81,0%` — sinal vem da severidade, nunca do tipo do insight. */
function formatValue(value: number, severity: InsightSeverity): string {
  const magnitude = Math.abs(value).toLocaleString('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
  if (severity === 'positive') return `+${magnitude}%`
  if (severity === 'negative') return `-${magnitude}%`
  return `${magnitude}%`
}

/**
 * Um cartão de Business Insight — ícone, título, descrição e o percentual
 * principal, com cor indicando positivo/negativo/neutro. A entrada/saída
 * anima via `motion.div` (a lista inteira é recalculada a cada troca de
 * filtro, então cartões que desaparecem/aparecem merecem uma transição, não
 * um corte seco — ver design-system.md, "Animações").
 */
export function InsightCard({ insight }: { insight: Insight }) {
  const Icon = SEVERITY_ICON[insight.severity]

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.18 }}
    >
      <Card className="flex h-full flex-col gap-3 p-5">
        <div className="flex items-center justify-between gap-2">
          <span
            className={[
              'flex h-9 w-9 items-center justify-center rounded-full',
              SEVERITY_BADGE_CLASS[insight.severity],
            ].join(' ')}
          >
            <Icon className="h-4 w-4" />
          </span>
          <span
            className={[
              'text-lg font-semibold tracking-tight',
              SEVERITY_VALUE_CLASS[insight.severity],
            ].join(' ')}
          >
            {formatValue(insight.value, insight.severity)}
          </span>
        </div>
        <div>
          <h4 className="text-content text-sm font-semibold">{insight.title}</h4>
          <p className="text-content-muted mt-1 text-sm">{insight.description}</p>
        </div>
      </Card>
    </motion.div>
  )
}
