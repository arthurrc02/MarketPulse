import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '@/hooks/useAuth'
import { FullScreenLoader } from '@/routes/FullScreenLoader'

/** Afasta usuários já autenticados de `/login` e `/register`, enviando-os para `/app`. */
export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth()

  if (status === 'loading') {
    return <FullScreenLoader />
  }

  if (status === 'authenticated') {
    return <Navigate to="/app" replace />
  }

  return <>{children}</>
}
