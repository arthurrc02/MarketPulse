import { useState } from 'react'

import { Checkbox } from '@/components/ui/Checkbox'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Tabs } from '@/components/ui/Tabs'
import { PageContainer } from '@/components/layout/PageContainer'
import { Section } from '@/components/layout/Section'
import { useAuth } from '@/hooks/useAuth'

/**
 * Placeholder — nenhuma preferência aqui é persistida ainda (apenas estado
 * local, para demonstrar os componentes). Edição de perfil e segurança
 * chegam em sprints futuras.
 */
export function SettingsPage() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState(true)
  const [compactMode, setCompactMode] = useState(false)

  return (
    <PageContainer>
      <Section title="Configurações" description="Preferências da sua conta.">
        <Tabs
          label="Seções de configuração"
          tabs={[
            {
              id: 'profile',
              label: 'Perfil',
              content: (
                <div className="max-w-md space-y-4">
                  <Input label="E-mail" value={user?.email ?? ''} disabled />
                  <p className="text-content-muted text-sm">
                    A edição de perfil chega em uma sprint futura.
                  </p>
                </div>
              ),
            },
            {
              id: 'preferences',
              label: 'Preferências',
              content: (
                <div className="max-w-md space-y-6">
                  <Select
                    label="Fuso horário"
                    placeholder="Selecione"
                    defaultValue="america-sao_paulo"
                    options={[
                      { value: 'america-sao_paulo', label: 'América/São Paulo (GMT-3)' },
                      { value: 'utc', label: 'UTC' },
                    ]}
                  />
                  <Checkbox
                    label="Notificações por e-mail"
                    description="Receba um resumo semanal por e-mail."
                    checked={notifications}
                    onChange={(event) => {
                      setNotifications(event.target.checked)
                    }}
                  />
                  <Checkbox
                    label="Modo compacto"
                    description="Reduz o espaçamento das listas e tabelas."
                    checked={compactMode}
                    onChange={(event) => {
                      setCompactMode(event.target.checked)
                    }}
                  />
                </div>
              ),
            },
            {
              id: 'security',
              label: 'Segurança',
              content: (
                <div className="max-w-md space-y-4">
                  <p className="text-content-muted text-sm">
                    Troca de senha e autenticação em duas etapas chegam em uma sprint futura.
                  </p>
                </div>
              ),
            },
          ]}
        />
      </Section>
    </PageContainer>
  )
}
