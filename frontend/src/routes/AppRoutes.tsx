import { Navigate, Route, Routes } from 'react-router-dom'

import { UnderConstructionPage } from '@/pages/UnderConstructionPage'

/** Rotas da aplicação. Na Sprint 0 tudo aponta para a página temporária. */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<UnderConstructionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
