import { QueryClient } from '@tanstack/react-query'

/**
 * Cria um QueryClient isolado.
 *
 * Os testes criam a própria instância para não compartilhar cache entre casos.
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 30_000,
      },
    },
  })
}
