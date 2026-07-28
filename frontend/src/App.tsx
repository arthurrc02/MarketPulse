import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { AuthProvider } from '@/context/AuthContext'
import { createQueryClient } from '@/lib/queryClient'
import { AppRoutes } from '@/routes/AppRoutes'

const queryClient = createQueryClient()

/** Raiz da aplicação: providers globais + roteamento. */
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
