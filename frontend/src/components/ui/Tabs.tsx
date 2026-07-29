import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react'

interface TabItem {
  id: string
  label: string
  content: ReactNode
}

interface TabsProps {
  tabs: TabItem[]
  defaultTabId?: string
  label?: string
}

/** Segue o padrão WAI-ARIA de Tabs: setas esquerda/direita movem foco e seleção juntos. */
export function Tabs({ tabs, defaultTabId, label = 'Seções' }: TabsProps) {
  const [activeId, setActiveId] = useState(defaultTabId ?? tabs[0]?.id)
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  const activeTab = tabs.find((tab) => tab.id === activeId) ?? tabs[0]

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    event.preventDefault()
    const delta = event.key === 'ArrowRight' ? 1 : -1
    const nextTab = tabs[(index + delta + tabs.length) % tabs.length]
    if (!nextTab) return
    setActiveId(nextTab.id)
    tabRefs.current[nextTab.id]?.focus()
  }

  return (
    <div>
      <div role="tablist" aria-label={label} className="border-border flex gap-1 border-b">
        {tabs.map((tab, index) => {
          const selected = tab.id === activeTab?.id
          return (
            <button
              key={tab.id}
              ref={(element) => {
                tabRefs.current[tab.id] = element
              }}
              role="tab"
              type="button"
              id={`tab-${tab.id}`}
              aria-selected={selected}
              aria-controls={`panel-${tab.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => {
                setActiveId(tab.id)
              }}
              onKeyDown={(event) => {
                handleKeyDown(event, index)
              }}
              className={[
                'relative px-4 py-2.5 text-sm font-medium transition-colors',
                selected ? 'text-content' : 'text-content-muted hover:text-content',
              ].join(' ')}
            >
              {tab.label}
              {selected && (
                <span className="bg-primary absolute inset-x-0 -bottom-px h-0.5 rounded-full" />
              )}
            </button>
          )
        })}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={tab.id !== activeTab?.id}
          className="pt-6"
        >
          {tab.id === activeTab?.id && tab.content}
        </div>
      ))}
    </div>
  )
}
