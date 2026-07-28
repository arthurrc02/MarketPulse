/**
 * Página temporária da Sprint 0.
 *
 * Substituída pelas telas reais a partir da Sprint 2 (Design System &
 * Frontend Foundation). Nenhum componente aqui pertence ao Design System.
 */
export function UnderConstructionPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="text-content-muted text-xs font-medium tracking-[0.3em] uppercase">
        Sprint 0 · Foundation
      </p>

      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">MarketPulse</h1>

      <p className="text-content-muted max-w-md text-base text-balance">
        Projeto em desenvolvimento. A infraestrutura está configurada e as funcionalidades serão
        entregues nas próximas sprints.
      </p>
    </main>
  )
}
