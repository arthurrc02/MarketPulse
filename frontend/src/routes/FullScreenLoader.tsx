/**
 * Estado de carregamento durante o bootstrap da sessão (`AuthProvider`).
 *
 * Não é um componente do Design System (esses chegam na Sprint 2) — apenas o
 * suficiente para não piscar `/login` antes de sabermos se há sessão válida.
 */
export function FullScreenLoader() {
  return (
    <div className="bg-surface flex min-h-dvh items-center justify-center" role="status">
      <span className="sr-only">Carregando...</span>
      <div
        className="border-border border-t-primary h-8 w-8 animate-spin rounded-full border-2"
        aria-hidden="true"
      />
    </div>
  )
}
