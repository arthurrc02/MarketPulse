# MarketPulse — Design System

> **Status (Sprint 2):** o Design System está implementado com componentes
> próprios (sem bibliotecas de UI prontas — ver [ADR-027](decisions.md#adr-027--design-system-com-componentes-próprios-sem-bibliotecas-de-ui)),
> cobrindo Layout, Inputs, Feedback, Dados (estrutura visual) e Navegação.
> Tabelas, paginação, filtros, gráficos reais, DatePicker, FileUpload, Alert,
> Breadcrumb, User Menu e Toggle **não** foram implementados — chegam junto
> das funcionalidades que realmente os utilizam (Sprints 3 a 6).

## Objetivo

O MarketPulse deverá possuir uma identidade visual consistente, moderna e profissional, semelhante a produtos SaaS atuais. Todos os componentes devem seguir o mesmo padrão visual e de interação.

---

## Inspirações

- Linear
- Stripe
- Vercel
- Supabase
- Clerk
- Raycast

---

## Identidade Visual

### Tema

Dark Mode como padrão (único tema — não há alternância para claro).

### Estilo

- Glassmorphism leve — `Card`, `Modal`, `Dropdown` e o `Header` usam fundo translúcido com `backdrop-blur`.
- Gradientes sutis — logo e fundo do `AuthLayout`.
- Bordas arredondadas — `rounded-xl` em controles, `rounded-2xl` em contêineres.
- Sombras discretas — `shadow-lg`/`shadow-2xl` com preto translúcido, nunca cores de sombra.
- Micro animações — Framer Motion em `Modal`, `Dropdown`, `Tooltip`, `Toast` e na gaveta mobile da `Sidebar`; nada além disso (ver seção "Animações").
- Alto contraste — tokens `content`/`content-muted` calibrados para leitura confortável em fundo escuro.
- Ícones consistentes — um único catálogo SVG (`components/icons/Icons.tsx`), mesmo traço (1.5–2px) e `viewBox` em todos.
- Tipografia moderna — Inter via Google Fonts, com fallback para a pilha `system-ui` (ver [ADR-028](decisions.md#adr-028--inter-via-google-fonts-com-fallback-progressivo)).

---

## Tokens (`frontend/src/styles/index.css`)

| Token | Uso |
| --- | --- |
| `--color-surface` | Fundo da página. |
| `--color-surface-sunken` | Fundo da `Sidebar` — uma camada abaixo de `surface`. |
| `--color-surface-elevated` | Cards, inputs, popovers — uma camada acima de `surface`. |
| `--color-content` / `--color-content-muted` | Texto principal / secundário. |
| `--color-border` / `--color-border-focus` | Borda padrão / borda em foco. |
| `--color-primary`, `-hover`, `-foreground` | Cor de destaque (ações primárias, links, estado ativo da navegação). |
| `--color-danger`, `-hover`, `-foreground` | Ações destrutivas e erros. |
| `--font-sans` | Inter → `ui-sans-serif` → `system-ui`. |

Verde (sucesso) e âmbar (aviso, ainda não usado) vêm diretamente da paleta padrão do Tailwind (`emerald-*`) — não ganharam token próprio, para não duplicar o que o framework já oferece (ver ADR-015 em decisions.md, mesmo raciocínio aplicado agora a cores semânticas).

**Convenções:**

- Raio: `rounded-lg`/`rounded-xl` em controles (`Button`, `Input`, `Badge`), `rounded-2xl` em contêineres (`Card`, `Modal`, `Dropdown`).
- Sombra: `shadow-lg`/`shadow-2xl` com `shadow-black/20-30` — nunca cores de sombra.
- Transições: `duration-150` a `duration-200` em hover/foco; nunca acima de `duration-300` (evita a sensação de lentidão).

---

## Componentes

Os componentes deverão ser reutilizados em toda a aplicação.

### Layout — ✅ implementado

- **AppLayout** (`components/layout/AppLayout.tsx`) — Sidebar + Header + `<Outlet />`; controla a gaveta mobile.
- **Sidebar** — coluna fixa em telas grandes, gaveta deslizante com backdrop em telas pequenas; navegação via `NavLink` (estado ativo automático via `aria-current`).
- **Header** — botão de menu mobile, busca (desabilitada, placeholder), menu de conta (`Dropdown`) com confirmação de logout (`Dialog`).
- **PageContainer** — largura máxima e espaçamento padrão do conteúdo.
- **Section** — título opcional, descrição e slot de ações para agrupar conteúdo.

### Inputs — Button, Input, PasswordInput, SearchInput, Select, Checkbox ✅ · Toggle, DatePicker, FileUpload ⬜

- **Button** — variantes `primary`/`secondary`/`ghost`/`danger`; estado `isLoading` com `Spinner` embutido.
- **IconButton** — mesma base do Button, só ícone; `aria-label` obrigatório no tipo.
- **Input**, **PasswordInput** (Sprint 1) — label, erro, `aria-invalid`/`aria-describedby`.
- **SearchInput** — ícone de busca, botão de limpar condicional (`onClear`).
- **Select** — `<select>` nativo estilizado (decisão deliberada — ver [ADR-029](decisions.md#adr-029--select-como-native-select-estilizado-não-um-listbox-customizado)).
- **Checkbox** — `<input type="checkbox">` nativo com visual customizado via `peer`.
- **Toggle, DatePicker, FileUpload** — não implementados; entram junto das telas que precisam deles (Sprint 3 em diante).

### Feedback — Toast, Modal, Dialog, Tooltip, Badge, EmptyState, Skeleton, Spinner ✅ · Alert ⬜

- **Toast** (`context/ToastContext.tsx` + `hooks/useToast.ts`) — fila de notificações, auto-dismiss configurável, `role="alert"` para erros e `role="status"` para sucesso/info. Disparado hoje em: login, cadastro e logout bem-sucedidos.
- **Modal** — portal para `document.body`, fecha em Esc/backdrop, devolve o foco ao elemento que abriu.
- **Dialog** — `Modal` com o par de ações padronizado (confirmar/cancelar); usado na confirmação de logout.
- **Tooltip** — posicionamento fixo acima/abaixo do gatilho (sem flip automático — ver limitação no ADR correspondente); mostra em hover e em foco por teclado.
- **Badge** — variantes `neutral`/`primary`/`success`/`danger`.
- **EmptyState** — bloco para telas/seções sem conteúdo; usado em Uploads, Analytics, Insights e na atividade recente do Dashboard.
- **Skeleton** / **Spinner** — placeholders de carregamento; `Spinner` é compartilhado por `Button`, `IconButton` e o loader de sessão.
- **Alert** — não implementado (não surgiu necessidade real ainda; `Toast` cobre os casos atuais).

### Dados — Card, KPI Card ✅ (estrutura visual) · Table, Pagination, Filters, Chart Card ⬜

- **Card** (Sprint 1) — contêiner glassmorphism base.
- **KPI Card** — estrutura visual apenas: rótulo, valor, badge de variação opcional, tooltip de contexto e estado `isLoading` (mostra `Skeleton`). Nenhum dado real — os indicadores de negócio chegam na Sprint 5.
- **Table, Pagination, Filters, Chart Card** — não implementados; não há dado real para exibir neles ainda.

### Navegação — Tabs, Dropdown ✅ · Breadcrumb, User Menu ⬜

- **Tabs** — segue o padrão WAI-ARIA (setas esquerda/direita movem foco e seleção); usado em Configurações (Perfil/Preferências/Segurança).
- **Dropdown** — menu suspenso simples (fecha em clique fora ou Esc); usado no menu de conta do Header.
- **Breadcrumb, User Menu (como componente dedicado)** — não implementados; o Header já resolve a necessidade atual de "conta do usuário" via `Dropdown` diretamente.

---

## Gráficos

Os gráficos deverão possuir aparência consistente.

Tipos previstos (Sprint 5, junto do Analytics Dashboard):

- Área
- Linha
- Barras
- Pizza
- Radar
- Heatmap (futuro)

Nenhum gráfico existe nesta sprint.

---

## Animações

Framer Motion é usado **apenas** onde a transição comunica algo (abrir/fechar, entrar/sair) — não em decoração estática:

- Entrada/saída de `Modal` e `Dialog` (fade + scale, 150ms).
- Abrir/fechar do `Dropdown` (fade + scale, 120ms).
- Aparecer/sumir do `Tooltip` (fade, 120ms).
- Entrada/saída de `Toast` (fade + slide, 180ms).
- Gaveta mobile da `Sidebar` e seu backdrop (fade, 150ms).

Hover de cards, botões e links usa transições CSS puras (`transition-colors duration-150`) — não Framer Motion, para manter essas interações leves (rodam no compositor do navegador sem JS por frame). Nenhuma entrada de página inteira foi animada (evita a sensação de "esperar a animação terminar" a cada navegação).

---

## Responsividade

A interface deverá funcionar em:

- Desktop
- Notebook
- Tablet

O foco principal será Desktop.

**Implementado:** a `Sidebar` vira uma gaveta deslizante abaixo do breakpoint `lg` (1024px); o `Header` esconde a busca e o e-mail completo em telas estreitas, mantendo apenas o avatar; os grids de `KPICard` colapsam de 4 para 2 colunas (`sm`) e 1 coluna no mobile.

---

## Acessibilidade

- **Teclado:** todo componente interativo é alcançável e operável por teclado — `Tabs` com setas esquerda/direita, `Modal`/`Dropdown` fecham com Esc, `Checkbox` e `Select` são elementos nativos (teclado de graça).
- **Labels:** todo campo tem `<label htmlFor>` associado; `IconButton` e `SearchInput` exigem `aria-label` no próprio tipo (erro de compilação sem ele).
- **Foco:** `:focus-visible` com anel consistente (`--color-border-focus`) em todos os controles; `Modal` foca o diálogo ao abrir e devolve o foco ao elemento que o abriu, ao fechar.
- **Papéis ARIA:** `Modal`/`Dialog` (`role="dialog"`, `aria-modal`, `aria-labelledby`), `Dropdown` (`role="menu"`/`menuitem`), `Tabs` (`tablist`/`tab`/`tabpanel`), `Tooltip` (`role="tooltip"` + `aria-describedby`), `Toast` (`alert` para erro, `status` para sucesso/info).
- **Limitações conhecidas:** `Dropdown` não implementa navegação por setas entre itens (só Tab); `Tooltip` não faz flip automático de lado. Ambas documentadas como melhorias futuras.

---

## Objetivo

A aparência final deve transmitir a sensação de um produto SaaS comercial pronto para uso.
