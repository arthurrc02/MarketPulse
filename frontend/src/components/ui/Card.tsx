import type { HTMLAttributes } from 'react'

/** Glassmorphism leve: fundo translúcido, blur, borda e sombra discreta. */
export function Card({ className = '', children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={[
        'bg-surface-elevated/80 border-border rounded-2xl border p-8 shadow-2xl shadow-black/20 backdrop-blur-xl',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </div>
  )
}
