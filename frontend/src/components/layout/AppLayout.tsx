import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

/** Layout raiz das páginas protegidas: sidebar + header + área principal (`<Outlet />`). */
export function AppLayout() {
  const [isSidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  // Fecha a gaveta mobile da sidebar sempre que a rota muda.
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  return (
    <div className="bg-surface min-h-dvh">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => {
          setSidebarOpen(false)
        }}
      />
      <div className="flex min-h-dvh flex-col lg:pl-64">
        <Header
          onMenuClick={() => {
            setSidebarOpen(true)
          }}
        />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
