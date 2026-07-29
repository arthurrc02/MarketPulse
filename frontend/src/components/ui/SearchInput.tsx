import { forwardRef, type InputHTMLAttributes } from 'react'

import { CloseIcon, SearchIcon } from '@/components/icons/Icons'

interface SearchInputProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'type' | 'aria-label'
> {
  'aria-label': string
  onClear?: () => void
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(function SearchInput(
  { onClear, value, className = '', ...props },
  ref,
) {
  const showClear = Boolean(onClear) && Boolean(value)

  return (
    <div className="relative">
      <SearchIcon className="text-content-muted pointer-events-none absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2" />
      <input
        ref={ref}
        type="search"
        value={value}
        className={[
          'bg-surface-elevated text-content placeholder:text-content-muted w-full rounded-xl border border-border py-2.5 pl-10 text-sm placeholder:opacity-60',
          'outline-none transition-colors duration-150 focus:border-border-focus disabled:cursor-not-allowed disabled:opacity-60',
          showClear ? 'pr-10' : 'pr-3.5',
          className,
        ].join(' ')}
        {...props}
      />
      {showClear && (
        <button
          type="button"
          onClick={onClear}
          aria-label="Limpar busca"
          className="text-content-muted hover:text-content absolute top-1/2 right-3 -translate-y-1/2"
        >
          <CloseIcon className="h-4 w-4" />
        </button>
      )}
    </div>
  )
})
