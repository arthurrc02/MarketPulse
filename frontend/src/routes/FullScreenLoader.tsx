import { Spinner } from '@/components/ui/Spinner'

/** Estado de carregamento durante o bootstrap da sessão (`AuthProvider`). */
export function FullScreenLoader() {
  return (
    <div className="bg-surface flex min-h-dvh items-center justify-center">
      <Spinner className="text-primary h-8 w-8" />
    </div>
  )
}
