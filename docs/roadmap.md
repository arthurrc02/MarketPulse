# MarketPulse — Roadmap

| Sprint | Entrega                             | Status       |
| ------ | ----------------------------------- | ------------ |
| 0      | Foundation                          | ✅ Concluída |
| 1      | Authentication                      | ✅ Concluída |
| 2      | Design System & Frontend Foundation | ✅ Concluída |
| 3      | File Import                         | ✅ Concluída |
| 4      | ETL Engine                          | ✅ Concluída |
| 5      | Analytics Dashboard                 | ✅ Concluída |
| 6      | Business Insights                   | ✅ Concluída |
| 7      | Release Candidate                   | ⏳ Próxima   |

---

## Sprint 0 — Foundation ✅

**Objetivo:** preparar toda a infraestrutura do projeto, sem funcionalidades de
negócio.

**Entregue:**

- Workspace uv na raiz reunindo `backend` e `etl` com um único `uv.lock`.
- Backend FastAPI em camadas (`api` → `services` → `repositories` → `db`), com
  settings tipadas via Pydantic Settings e logging configurável.
- SQLAlchemy 2 e Alembic configurados, com convenção de nomes explícita no
  `MetaData`. Nenhuma migration ainda — não há models de negócio.
- Endpoint `GET /health` (liveness), com serviço e schema próprios.
- Estrutura do módulo ETL: contratos `Extractor`, `Transformer`, `Loader`,
  orquestrador `ETLPipeline`, tipos e exceções. Sem processamento.
- Frontend React 19 + TypeScript + Vite, com Tailwind CSS 4, React Router e
  React Query configurados; página temporária informando que o projeto está em
  desenvolvimento.
- Ferramental de qualidade: Ruff, MyPy (strict), Pytest, ESLint, Prettier e
  Vitest.
- Docker e Docker Compose (backend, frontend, PostgreSQL 16) com Dockerfiles
  multi-stage e alvos `development` e `production`.
- GitHub Actions com três jobs: backend, frontend e build das imagens Docker.
- Documentação: `setup.md`, `decisions.md`, `README.md` e atualização de
  `architecture.md` e `roadmap.md`.

**Fora de escopo (por decisão):** autenticação, upload de arquivos, dashboard,
processamento ETL e componentes do Design System.

---

## Sprint 1 — Authentication ✅

**Objetivo:** cadastro, login, sessão persistente, proteção de rotas e logout
— toda a infraestrutura de autenticação, sem nenhuma funcionalidade de
negócio.

**Entregue:**

- Models `User` e `RefreshToken` + primeira migration do Alembic (única
  gerada até aqui), validada com `upgrade`/`downgrade`/`upgrade` contra
  PostgreSQL real.
- Hash de senha com `bcrypt` direto (substitui `Passlib/Bcrypt`, incompatível
  com `bcrypt>=4.1` — ver [ADR-020](decisions.md#adr-020--bcrypt-direto-no-lugar-de-passlibbcrypt)).
- Access token JWT (PyJWT, HS256, 15 min) e refresh token opaco e revogável,
  com rotação a cada uso (ver [ADR-018](decisions.md#adr-018--refresh-token-opaco-e-revogável-em-vez-de-jwt-stateless)).
- Endpoints `POST /api/v1/auth/{register,login,refresh,logout}` e
  `GET /api/v1/users/me`, todos sob o prefixo versionado — contrato completo
  em [api.md](api.md) (novo).
- `AuthService` + `UserRepository`/`RefreshTokenRepository` seguindo a
  arquitetura em camadas já estabelecida; hierarquia `AppError` traduzida
  para HTTP por um exception handler central.
- Dependência `get_current_user` (via `HTTPBearer`) protegendo `GET /users/me`.
- Frontend: `AuthContext`/`AuthProvider` (sessão, silent refresh no boot),
  `apiClient` com retry automático em 401, guards `ProtectedRoute` /
  `PublicOnlyRoute`, páginas de Login, Cadastro e um Dashboard temporário
  ("Bem-vindo ao MarketPulse.").
- Seis componentes mínimos de UI (`Button`, `Input`, `PasswordInput`, `Card`,
  `Logo`, `AuthLayout`) — o restante do Design System é da Sprint 2.
- 57 testes de backend (security, config, fluxo completo de auth via HTTP,
  casos de erro) rodando contra SQLite **e** PostgreSQL real; 21 testes de
  frontend (bootstrap de sessão, login, cadastro, logout, guards de rota).
- CI: serviço PostgreSQL no job de backend, validando migration e suíte
  contra o dialeto de produção (ver [ADR-019](decisions.md#adr-019--suíte-de-testes-com-sqlite-por-padrão-postgresql-real-na-ci)).

**Fora de escopo (por decisão):** upload de arquivos, ETL, dashboard real,
insights, integrações com marketplaces, Design System completo.

---

## Sprint 2 — Design System & Frontend Foundation ✅

**Objetivo:** identidade visual e componentes reutilizáveis — sem nenhuma
funcionalidade de negócio.

**Entregue:**

- Tokens completos em `@theme`: superfícies em camadas (`surface` →
  `surface-elevated`/`surface-sunken`), tipografia (Inter + fallback),
  animação (`fade-in`). Cores semânticas de sucesso/erro reaproveitam a
  paleta padrão do Tailwind — não duplicam tokens que o framework já oferece.
- **18 componentes próprios** (sem bibliotecas de UI prontas — ver
  [ADR-027](decisions.md#adr-027--design-system-com-componentes-próprios-sem-bibliotecas-de-ui)):
  `IconButton`, `SearchInput`, `Select`, `Checkbox`, `Badge`, `KPICard`,
  `Modal`, `Dialog`, `Dropdown`, `Tooltip`, `Tabs`, `EmptyState`, `Skeleton`,
  `Spinner` (extraído do `Button` da Sprint 1, eliminando duplicação), além
  de `Button` ganhando a variante `danger`.
- Componentes de layout: `AppLayout`, `Sidebar` (coluna fixa/gaveta mobile),
  `Header` (busca placeholder, menu de conta), `PageContainer`, `Section`.
- Catálogo único de ícones SVG consistentes (`components/icons/Icons.tsx`).
- Sistema de notificações (`ToastContext`/`ToastProvider`/`useToast`),
  disparado em login, cadastro e logout bem-sucedidos.
- Dashboard real (sidebar + header + KPICards placeholder + EmptyState),
  substituindo a página protegida mínima da Sprint 1.
- Navegação preparada: `/app/uploads`, `/app/analytics`, `/app/insights`
  (EmptyState apontando a sprint de cada funcionalidade) e `/app/settings`
  (Tabs Perfil/Preferências/Segurança, com Select e Checkbox de exemplo).
- Framer Motion usado seletivamente (Modal, Dropdown, Tooltip, Toast, gaveta
  da Sidebar) — não em toda transição de página.
- Responsivo: Sidebar vira gaveta abaixo de `lg`, grids de KPICard colapsam
  em telas menores.
- Acessibilidade revisada: navegação por teclado em Tabs/Modal/Dropdown,
  `aria-label` obrigatório em `IconButton`/`SearchInput` (erro de tipo sem
  ele), foco devolvido ao fechar modais, papéis ARIA corretos em todos os
  componentes interativos.
- 105 testes de frontend (era 21 na Sprint 1): componentes do Design System,
  Sidebar, Header (incluindo a confirmação de logout), AppLayout, navegação
  aninhada e páginas placeholder.

**Fora de escopo (por decisão):** upload de arquivos, ETL, analytics,
insights, integrações com marketplaces, gráficos reais, qualquer dado real —
todos os cards e páginas de negócio permanecem placeholders.

---

## Sprint 3 — File Import ✅

**Objetivo:** infraestrutura de upload e gestão de arquivos, preparando uma
base sólida para o motor ETL da Sprint 4 — **sem** nenhum processamento,
parsing, leitura de planilha ou análise nesta sprint.

**Entregue:**

- Model `Upload` (`id`, `user_id`, `original_filename`, `stored_filename`,
  `file_size`, `mime_type`, `status`, `error_message`, `uploaded_at`,
  `updated_at`) + relação `User.uploads`, com migration própria validada
  `upgrade`/`downgrade`/`upgrade` contra PostgreSQL real.
- `UploadStatus` (`uploaded`/`queued`/`processing`/`processed`/`failed`) — só
  `uploaded` é usado nesta sprint; os demais existem para a Sprint 4
  transicionar.
- Abstração `FileStorage` (`save`/`open`/`delete`) com implementação
  `LocalFileStorage`, organizando os arquivos em
  `storage/uploads/{user_id}/{stored_filename}` — local nesta sprint, sem
  S3/nuvem (ver [decisions.md](decisions.md)), mas desenhada para a Sprint 4
  consumir via `open()` sem refatoração.
- `UploadService` com validação de extensão (`.csv`/`.xlsx`), Content-Type e
  tamanho máximo configurável (`MAX_UPLOAD_SIZE_BYTES`), leitura em chunks
  para não estourar memória, e `stored_filename` opaco (UUID) por segurança.
- Endpoints `POST/GET/GET-{id}/DELETE /api/v1/uploads`, todos autenticados —
  contrato completo em [api.md](api.md). Detalhe e exclusão de upload de
  outro usuário respondem `404` (nunca `403` — mesmo padrão de
  [ADR-018](decisions.md#adr-018--refresh-token-opaco-e-revogável-em-vez-de-jwt-stateless)).
- Frontend: componentes `FileUpload` (drag & drop + seleção manual) e `Table`
  genérica (ordenação, `aria-sort`) — novos membros do Design System, sem
  bibliotecas de UI prontas (mesma decisão da Sprint 2).
- `UploadsPage` real (fila com progresso simulado, busca por nome, ordenação
  por data, exclusão com confirmação em `Dialog`, `EmptyState`/`Skeleton`/
  `Toast`) substituindo o placeholder da Sprint 2; `UploadDetailPage` nova em
  `/app/uploads/:id`.
- Primeiro uso real de React Query no projeto (`useUploads.ts`): cache,
  invalidação após criar/excluir.
- 77 testes de backend (era 57 na Sprint 1) e 131 de frontend (era 105 na
  Sprint 2), cobrindo upload válido/inválido, limite de tamanho, autenticação,
  listagem, detalhe, exclusão, drag & drop, busca e ordenação.
- Correções encontradas na revisão técnica: valores do enum de status
  gravados em minúsculas (não os nomes do Python), precisão de timestamp no
  SQLite, `<input>` fora do `<button>` (HTML inválido), `aria-sort` movido
  para o `<th>`, mensagens de erro de upload distintas entre toast e item da
  fila, e permissão de escrita em `/app/storage` no Dockerfile de produção.

**Fora de escopo (por decisão, fica para a Sprint 4):** parsing de CSV/XLSX,
leitura de conteúdo dos arquivos, detecção de marketplace de origem,
dashboards, analytics, insights.

---

## Sprint 4 — ETL Engine ✅

**Objetivo:** implementar o motor de processamento que transforma os arquivos
já enviados (Sprint 3) em dados estruturados — sem dashboard, sem
analytics, sem IA.

**Ajuste de escopo (decisão explícita, ver [decisions.md](decisions.md)):** em vez de
implementar os quatro marketplaces da visão de produto de uma vez, a sprint
entrega **dois formatos de exemplo completos** (Shopee e Mercado Livre,
fictícios mas realistas) e uma arquitetura desenhada para que Amazon e Magalu
sejam apenas mais um detector/extractor/transformer — sem tocar no
orquestrador, no model ou nos endpoints.

**Entregue:**

- Pacote `etl` totalmente implementado: `Extractor` → `Transformer` →
  Validação → `Loader`, orquestrados por `ETLPipeline.run` (antes,
  `NotImplementedError`). Cada etapa continua com responsabilidade única.
- Detecção automática de marketplace por cabeçalho (`etl.detectors`), sem IA
  — conjuntos de colunas exigidos, disjuntos entre marketplaces. Cabeçalho
  não reconhecido (ou ambíguo) vira `UnknownMarketplaceError` → upload
  `failed`.
- Parser resiliente (`etl.parsing`): CSV e XLSX, cabeçalhos normalizados
  (espaço → `_`, minúsculo), colunas fora de ordem ou extras não quebram a
  leitura, `dtype=str` preserva zeros à esquerda em SKUs/IDs.
- Regras de transformação centralizadas (`etl.transformers.common`): valores
  monetários em centavos (evita erro de ponto flutuante), datas `dd/mm/aaaa`,
  percentuais, status por marketplace mapeado para um `OrderStatus`
  canônico (status desconhecido vira `UNKNOWN`, não interrompe o arquivo).
- Model `OrderItem` (uma linha por item de pedido, não `Order`/`Product`
  separados — ver ADR) + campos `started_at`/`finished_at` em `Upload`, com
  migration própria validada `upgrade`/`downgrade`/`upgrade` contra
  PostgreSQL real.
- `OrderItemLoader` (adapta o contrato `Loader` do `etl` para SQLAlchemy):
  insere em lote (`INSERT` multi-linha único) e substitui itens de uma
  tentativa anterior antes de inserir — reprocessar um upload é idempotente.
- `ETLProcessorService`: orquestra detecção → pipeline → status do upload
  (`uploaded` → `processing` → `processed`/`failed`), sempre a partir de um
  `upload_id` — a mesma assinatura que um worker de fila chamaria no futuro,
  sem reescrever o pipeline.
- Endpoint `POST /api/v1/uploads/{id}/process` — síncrono nesta sprint,
  sempre responde `200` com o resultado (mesmo em falha de processamento);
  `404` só para upload inexistente/de outro usuário.
- Frontend: botão "Processar" (Uploads e detalhe do upload), `useUploadQuery`
  com polling enquanto `status === "processing"` (arquitetura pronta para
  processamento assíncrono, mesmo síncrono hoje), `UploadDetailPage` exibindo
  início/fim/duração/erro do processamento — nenhum dado extraído é
  mostrado (fica para a Sprint 5).
- 45 testes novos no pacote `etl` (parsing, schema, detectores, extractors,
  transformers, pipeline) e 14 no backend (CSV/XLSX válidos, marketplace
  desconhecido, arquivo ilegível, dados inválidos, reprocessamento
  idempotente, cascata de exclusão), além de 8 novos testes de frontend
  (botão processar, polling, estados de sucesso/erro). 91 testes de backend
  no total (era 77), 139 de frontend (era 131); `uv run pytest` na raiz
  (backend + etl juntos, ver `pyproject.toml`) soma 136.
- Validação real via Docker Compose: upload e processamento de um CSV real
  contra o alvo `production` do backend (não só `development`), incluindo o
  caso de marketplace desconhecido (rollback — nenhum `OrderItem` parcial) e
  reprocessamento idempotente.

**Hotfix 4.1 (pós-sprint):** um relatório oficial real da Shopee (XLSX,
Seller Center) era rejeitado como "marketplace desconhecido" — o conjunto
de cabeçalhos fictício desta sprint não coincide com os nomes reais de
coluna. `ShopeeDetector` passou a reconhecer o arquivo por uma assinatura de
5 conceitos característicos (PT-BR/EN, com pequenas variações de grafia),
em vez de um conjunto fixo e completo — ver
[ADR-060](decisions.md#adr-060--detecção-da-shopee-por-assinatura-de-conceitos-hotfix-sprint-41-não-mais-por-cabeçalhos-fixos).
Só a detecção mudou; `Extractor`/`Transformer`/`Loader`/`ETLPipeline` e a
API permanecem como entregues nesta sprint — um relatório real da Shopee
agora é corretamente roteado ao pipeline Shopee, mas o `ShopeeTransformer`
ainda espera os nomes de coluna do formato fictício de exemplo (ajustá-lo
ao layout real é trabalho futuro, fora deste hotfix).

**Hotfix 4.2 (pós-sprint):** com a detecção corrigida, o processamento do
relatório oficial real ainda falhava no `ShopeeTransformer` (colunas com
nomes diferentes do formato fictício, datas em `aaaa-mm-dd hh:mm`, valores
monetários sem `R$`/vírgula, nenhuma coluna de SKU preenchida). Analisado o
arquivo real (`tests/fixtures/shopee/orders.xlsx`, 239 pedidos) e adaptado o
`ShopeeTransformer` para aceitar os dois layouts por alias de coluna
(`find_column`, mesma estratégia do Hotfix 4.1), com SKU derivado do nome
do produto quando ausente — ver
[ADR-061](decisions.md#adr-061--shopeetransformer-aceita-dois-layouts-por-alias-de-coluna-hotfix-sprint-42).
O arquivo real processa as 239 linhas com `status: "processed"`, sem
regressão no formato fictício. `Extractor`/`Loader`/`ETLPipeline`, models,
migrations e endpoints não foram alterados.

**Fora de escopo (por decisão, fica para sprints futuras):** Amazon e Magalu
(arquitetura pronta, sem detector ainda), fila real (Celery/Dramatiq/RQ —
processamento continua síncrono), tolerância a erro por linha (um arquivo com
uma linha inválida falha inteiro, não parcialmente), dashboards, analytics,
insights, OCR, IA.

---

## Sprint 5 — Analytics Dashboard ✅

**Objetivo:** transformar os `OrderItem` persistidos (Sprint 4) em métricas
reais e substituir os KPIs placeholder do Dashboard por dados de verdade.

**Entregue:**

- Camada de Analytics em camadas (`AnalyticsRepository` → `AnalyticsService`
  → `routes/analytics.py`), toda consulta agregada no PostgreSQL (`SUM`,
  `COUNT DISTINCT`, `GROUP BY`) — nenhum `OrderItem` é carregado linha a
  linha para o Python somar.
- Quatro endpoints: `GET /api/v1/analytics/{overview,sales-over-time,
  orders-by-status,top-products}`, todos exigindo autenticação e filtrando
  por `user_id` do token — nunca aceito do cliente. Filtros opcionais de
  período (`from`/`to`) e `marketplace` em todos; `top-products` também
  aceita `limit` (padrão 10, máximo 50, controlado pelo backend).
- KPIs (faturamento, pedidos, ticket médio, produtos ativos) calculados
  apenas sobre `OrderItem` com `status = completed` — ver
  [ADR-062](decisions.md#adr-062--kpis-de-analytics-consideram-somente-orderitem-com-status-completed).
  "Pedido" é sempre `COUNT(DISTINCT external_order_id)`, nunca a contagem de
  itens.
- `orders-by-status` é a exceção deliberada: mostra a distribuição entre
  **todos** os status, não só `completed` — é o próprio propósito do
  endpoint.
- Campo `has_data` no `overview`, calculado à parte dos filtros, para o
  frontend diferenciar "nunca importei nada" de "meu filtro não bateu com
  nada" — ver [ADR-063](decisions.md#adr-063--campo-has_data-para-distinguir-sem-dados-de-filtro-sem-resultado).
- Frontend: Dashboard real com quatro `KPICard`, dois gráficos de série
  temporal (faturamento e pedidos por dia), um gráfico de pizza (pedidos por
  status) e uma tabela de top produtos — todos via Recharts 3 (React Query
  refaz a busca a cada mudança de filtro, nunca refiltra em memória).
  Estados de carregamento (skeleton), erro (mensagem + "Tentar novamente",
  nunca um "—" silencioso) e vazio (`EmptyState` com atalho para
  `/app/uploads`) tratados separadamente.
- Novos componentes no Design System (`components/analytics/`):
  `AnalyticsFilters`, `RevenueChart`, `OrdersChart`, `OrderStatusChart`,
  `TopProductsTable` — reaproveitam `Card`, `Table`, `Skeleton`,
  `EmptyState` já existentes; nenhuma cor nova fora dos tokens já definidos.
- 20 testes novos de backend (fixtures determinísticas + integração com o
  `orders.xlsx` real) e 18 de frontend (KPIs, loading, erro, filtros,
  EmptyState, gráficos, tabela) — 182 testes de backend/etl e 154 de
  frontend no total.

**Fora de escopo (por decisão, fica para sprints futuras):** desempenho por
marketplace como indicador dedicado (o filtro de marketplace já cobre o caso
de uso principal), categorias de produto (não existe esse dado no modelo
atual), previsão de vendas, recomendação, edição manual dos dados
importados, fila assíncrona, insights automáticos (Sprint 6).

---

## Sprint 6 — Business Insights ✅

**Objetivo:** transformar os dados de Analytics em observações de negócio
objetivas e explicáveis — sem IA/ML, só regras matemáticas transparentes
sobre agregações já existentes.

**Entregue:**

- Camada de Insights própria (`Router → Service → Repository`), separada de
  Analytics mas reaproveitando suas agregações — `InsightsRepository`
  compõe `AnalyticsRepository` (mesma sessão) em vez de duplicar SQL; só a
  receita agrupada por marketplace é uma consulta nova (ver
  [ADR-067](decisions.md#adr-067--insightsrepository-reaproveita-analyticsrepository-em-vez-de-duplicar-sql)).
- Seis tipos de insight: tendência de faturamento, evolução de pedidos e de
  ticket médio (todos comparando com um "período anterior equivalente" —
  mesmo número de dias, imediatamente antes, exigindo `from`/`to`
  explícitos, ver [ADR-065](decisions.md#adr-065--período-atual-e-anterior-em-insights)),
  produto em destaque (maior faturamento + participação %), produto com
  queda de desempenho (só entre produtos relevantes — ≥ 10% do faturamento
  do período anterior, ver [ADR-066](decisions.md#adr-066--critério-de-relevância-para-produto-em-queda)),
  e marketplace de melhor desempenho (só com 2+ marketplaces nos dados).
- Endpoint `GET /api/v1/insights`, mesmos filtros de Analytics
  (`from`/`to`/`marketplace`), resposta tipada (`has_data` + lista de
  `Insight` com `id`/`type`/`title`/`description`/`severity`/`value`) —
  contrato completo em [api.md](api.md#business-insights).
- Frontend: `InsightsSection` no Dashboard (busca própria via
  `useInsightsQuery`, estados de carregamento/erro/vazio/dados
  insuficientes/sucesso distintos), `InsightCard` (ícone e cor por
  severidade — nunca por tipo, já que o mesmo tipo pode ser positivo ou
  negativo conforme os dados), animação de entrada/saída seletiva (Framer
  Motion) ao trocar filtros.
- 22 testes de backend novos (20 determinísticos + 2 de integração contra
  `orders.xlsx` real) e 9 de frontend (`InsightsSection`), cobrindo
  crescimento/queda em cada métrica, produto em destaque, produto em queda
  (incluindo exclusão de produto irrelevante), marketplace único vs.
  múltiplo, ausência de dados, dados insuficientes, período anterior sem
  dados, filtros, isolamento por usuário e empate.
- Validado o fluxo completo com o arquivo real (`orders.xlsx`, 239 pedidos,
  não alterado): upload → processamento → `GET /insights` retornando
  faturamento em queda (-19,7%), pedidos em queda (-14,7%), ticket médio em
  queda (-5,8%), produto em destaque (86,1% de participação) e produto em
  queda (-100%, produto sem vendas no período atual) — números conferidos
  de forma independente antes de escrever os testes, não copiados às cegas.

**Fora de escopo (por decisão):** IA/ML/LLM, previsão de vendas,
recomendações automáticas, análise de sentimento, novos marketplaces,
alterações no ETL/autenticação/upload, fila assíncrona, edição manual de
`OrderItem`.

---

## Sprint 7 — Release Candidate ⏳

**Objetivo:** preparar o produto para apresentação.

**Escopo previsto:**

- Refino de UX, estados de carregamento e tratamento de erros.
- Responsividade para notebook e tablet.
- Ampliação da cobertura de testes e testes end-to-end.
- Documentação final e roteiro de demonstração.
- Deploy de demonstração.
