interface SpinnerProps {
  className?: string
  label?: string
}

/** Indicador de carregamento reutilizado por Button, IconButton e páginas de sessão. */
export function Spinner({ className = 'h-4 w-4', label = 'Carregando...' }: SpinnerProps) {
  return (
    <span role="status" className="inline-flex items-center">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className={`animate-spin ${className}`}
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
        <path
          d="M22 12a10 10 0 0 0-10-10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </span>
  )
}
