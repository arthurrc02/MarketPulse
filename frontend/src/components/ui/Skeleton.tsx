interface SkeletonProps {
  className?: string
}

/** Placeholder de carregamento (shimmer). Puramente decorativo — sempre `aria-hidden`. */
export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={['bg-surface-elevated animate-pulse rounded-lg', className].join(' ')}
    />
  )
}
