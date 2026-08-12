# MarketPulse — Architecture

## Visão Geral

O MarketPulse será desenvolvido seguindo uma arquitetura em camadas, separando responsabilidades entre interface, regras de negócio, persistência de dados e processamento ETL.

```text
Frontend (React)
        │
        ▼
 FastAPI REST API
        │
        ▼
     Services
        │
        ▼
   Repositories
        │
        ▼
    PostgreSQL

ETL Engine (Pandas)
        │
        └── Importação, transformação e carga de dados
```

---

## Stack Tecnológica

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL 16
- Pydantic v2 / Pydantic Settings
- psycopg 3
- PyJWT (access token)
- bcrypt (hash de senha — ver [ADR-020](decisions.md#adr-020--bcrypt-direto-no-lugar-de-passlibbcrypt); substitui o `Passlib/Bcrypt` planejado inicialmente)
- Pytest

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- React Query
- Tailwind CSS 4
- Framer Motion
- Recharts 3 (gráficos do Dashboard de Analytics, Sprint 5 — v3, não v2 como
  originalmente previsto, por compatibilidade oficial com React 19)

### ETL

- Pandas
- OpenPyXL

### Infraestrutura

- uv (workspace: `backend` + `etl`)
- Docker
- Docker Compose
- GitHub Actions
- Ruff
- MyPy
- ESLint
- Prettier
- Vitest

---

## Organização do Repositório

```text
MarketPulse/
├── backend/          # API FastAPI
├── etl/              # Motor ETL (pacote Python independente)
├── frontend/         # Aplicação React
├── docker/           # Dockerfiles e configuração do Nginx
├── docs/             # Documentação
├── .github/          # Pipelines de CI
├── docker-compose.yml
└── pyproject.toml    # Workspace uv + configuração de Ruff, MyPy e Pytest
```

`backend/` e `etl/` são membros de um **workspace do uv**, compartilhando um
único `uv.lock`. O ETL é um pacote separado — e não um subpacote do backend —
para que possa ser reaproveitado por jobs e CLIs sem arrastar a API junto
(ver ADR-001 em [decisions.md](decisions.md)).

---

## Arquitetura do Backend

```text
Router
   │
   ▼
Service
   │
   ▼
Repository
   │
   ▼
Database
```

Cada camada possui responsabilidade única.

### Mapeamento para o código

| Camada         | Diretório              | Responsabilidade                                     |
| -------------- | ---------------------- | ---------------------------------------------------- |
| Router         | `app/api/routes/`      | Contrato HTTP: rotas, status codes, validação.        |
| Dependências   | `app/api/deps.py`      | Injeção de dependência (aliases `Annotated`).         |
| Service        | `app/services/`        | Regras de negócio; controla o limite transacional.    |
| Repository     | `app/repositories/`    | Acesso a dados; opera sobre a sessão recebida.        |
| Model          | `app/models/`          | Entidades SQLAlchemy.                                 |
| Schema         | `app/schemas/`         | Contratos Pydantic de entrada e saída.                |
| Infraestrutura | `app/core/`, `app/db/` | Settings, logging, engine e sessão.                   |

Regras que a estrutura impõe:

- Routers **não** acessam o banco diretamente — sempre via service.
- Repositories **não** abrem nem encerram transações — quem controla é o service.
- Models nunca são serializados diretamente na resposta — sempre via schema.

### Versionamento da API

Endpoints de negócio ficam sob `settings.API_V1_PREFIX` (`/api/v1`), a partir da
Sprint 1. `GET /health` fica fora do prefixo por ser uma sonda de
infraestrutura, consumida por Docker e CI, e não um recurso da API (ADR-003).

---

## Autenticação (Backend)

Implementada na Sprint 1. Endpoints e contratos completos em
[api.md](api.md); aqui, apenas o desenho.

```text
POST /auth/register  → cria o usuário (não emite tokens)
POST /auth/login     → valida credenciais, emite access + refresh token
POST /auth/refresh   → rotaciona o refresh token, emite um par novo
POST /auth/logout    → revoga o refresh token informado
GET  /users/me       → protegido por get_current_user
```

| Peça                    | Arquivo                            | Papel                                                        |
| ------------------------ | ----------------------------------- | ------------------------------------------------------------- |
| `User`, `RefreshToken`   | `app/models/`                       | Entidades persistidas (única tabela de negócio desta sprint). |
| `AuthService`            | `app/services/auth.py`              | Cadastro, login, refresh (rotação), logout (revogação).       |
| `UserRepository`, `RefreshTokenRepository` | `app/repositories/`   | Acesso a dados, sem lógica de negócio.                         |
| `security.py`            | `app/core/security.py`              | Hash de senha (bcrypt), JWT (PyJWT), geração/hash do refresh token. |
| `errors.py`              | `app/core/errors.py`                | Hierarquia `AppError` → HTTP, via exception handler em `main.py`. |
| `get_current_user`       | `app/api/deps.py`                   | Resolve o usuário a partir do `Authorization: Bearer`.         |

**Modelo de tokens:**

- **Access token** — JWT (HS256), stateless, 15 min (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Refresh token** — string opaca de alta entropia; só o hash SHA-256 é
  persistido (`refresh_tokens.token_hash`); 7 dias (`REFRESH_TOKEN_EXPIRE_DAYS`);
  **rotacionado a cada uso** e revogável (torna o logout real — ver
  [ADR-018](decisions.md#adr-018--refresh-token-opaco-e-revogável-em-vez-de-jwt-stateless)).

---

## Upload de Arquivos (Backend)

Endpoints e contratos completos em [api.md](api.md#uploads); aqui, apenas o
desenho. O upload em si (`POST`/`GET`/`DELETE`) só valida e armazena — o
processamento (`POST /process`) é uma camada separada (ver "Processamento de
Uploads (Backend)", abaixo), mantendo `UploadService` sem nenhuma regra de
ETL.

```text
POST   /uploads          → valida, gera stored_filename, grava e registra
GET    /uploads          → lista os uploads do usuário (mais recente primeiro)
GET    /uploads/{id}     → metadados de um upload do usuário
POST   /uploads/{id}/process → processa (ETL) — Sprint 4
DELETE /uploads/{id}     → remove o arquivo em disco, o registro e os OrderItem gerados
```

| Peça                | Arquivo                        | Papel                                                          |
| -------------------- | -------------------------------- | ----------------------------------------------------------------- |
| `Upload`              | `app/models/upload.py`           | Entidade persistida; `status` cobre todo o ciclo de vida (ver abaixo). |
| `UploadService`       | `app/services/upload.py`         | Validação (extensão/MIME/tamanho), geração do `stored_filename`, orquestração storage+DB. |
| `UploadRepository`    | `app/repositories/upload.py`     | Acesso a dados, sem lógica de negócio.                              |
| `FileStorage` / `LocalFileStorage` | `app/storage/`      | Abstração de armazenamento — ver "Armazenamento de Arquivos" abaixo. |

**Modelo de dados:** `id`, `user_id` (FK, `ondelete="CASCADE"`),
`original_filename` (só exibição — nunca usado para montar caminho),
`stored_filename` (`uuid4().hex` + extensão validada; opaco, evita colisão e
*path traversal*), `file_size`, `mime_type`, `status`, `error_message`,
`started_at`/`finished_at` (Sprint 4 — preenchidos por
`ETLProcessorService`), `uploaded_at`, `updated_at`.

**`status` — `UploadStatus`:** `uploaded` → `processing` → `processed` |
`failed` (Sprint 4 implementa essa transição — ver "Processamento de
Uploads (Backend)"). `queued` permanece no enum, reservado para quando uma
fila real existir; nesta sprint o processamento é síncrono, então não há um
estado "esperando na fila" a representar.

---

## Armazenamento de Arquivos

Local, organizado por usuário — sem S3/nuvem (ver ADR em decisions.md):

```text
storage/
└── uploads/
    └── {user_id}/
        └── {uuid4().hex}.{csv|xlsx}
```

`app/storage/base.py` define `FileStorage` (ABC): `save`, `open`, `delete`.
`LocalFileStorage` é a única implementação. `open()` — sem uso na Sprint 3 —
é exatamente o que `ETLProcessorService` chama para ler um upload existente
(Sprint 4), sem precisar de nenhuma interface nova nem refatoração no
`UploadService`, no model `Upload` ou nos endpoints já existentes.

Em Docker, `storage/` é um **bind mount** (`./storage:/app/storage`), não um
volume nomeado — os arquivos ficam inspecionáveis diretamente no host, tanto
em desenvolvimento quanto para depurar o que o motor ETL vai consumir.

---

## Arquitetura do Frontend

```text
Pages
   │
   ▼
Components
   │
   ▼
Hooks
   │
   ▼
API Client
   │
   ▼
Backend
```

Os componentes deverão ser reutilizáveis sempre que possível.

### Mapeamento para o código

| Camada     | Diretório                | Responsabilidade                                                |
| ---------- | ------------------------- | ------------------------------------------------------------------ |
| Pages      | `src/pages/`              | Telas completas.                                                    |
| Routes     | `src/routes/`             | Definição de rotas e guards (`ProtectedRoute`, `PublicOnlyRoute`).  |
| Context    | `src/context/`            | Estado global (`AuthContext`/`AuthProvider`, `ToastContext`/`ToastProvider`). |
| Components | `src/components/ui/`      | Design System: primitivos reutilizáveis (ver [design-system.md](design-system.md)). |
| Components | `src/components/layout/`  | `AppLayout`, `Sidebar`, `Header`, `PageContainer`, `Section`, `AuthLayout`. |
| Components | `src/components/icons/`   | Catálogo único de ícones SVG (`Icons.tsx`).                         |
| Components | `src/components/analytics/` | `AnalyticsFilters`, `RevenueChart`, `OrdersChart`, `OrderStatusChart`, `TopProductsTable` (Sprint 5). |
| Hooks      | `src/hooks/`              | `useAuth`, `useToast`, `useUploads`, `useAnalytics` (React Query).  |
| Lib        | `src/lib/`                | `apiClient`, `auth/api`, `uploads/api`, `analytics/api`, `auth/tokenStore`, `format`, QueryClient, `env`. |
| Styles     | `src/styles/`             | Tokens e camadas base do Tailwind (ver design-system.md).           |
| Test       | `src/test/`               | Setup do Vitest e `renderWithProviders` (helper de testes).         |

O alias `@/` aponta para `src/`, configurado tanto no Vite quanto no TypeScript.

> Arquivos de contexto React devem ter nomes que diferem por mais do que a
> capitalização da primeira letra (ex.: `AuthContext.tsx` +
> `authContextDefinition.ts`, não `AuthContext.tsx` + `authContext.ts`) — o
> `tsserver` do ESLint confunde os dois em filesystems case-insensitive
> (ver [ADR-026](decisions.md#adr-026--authcontexttsx-e-a-definição-do-contexto-em-arquivos-separados)).

---

## Autenticação (Frontend)

```text
AuthProvider (Context)
   │
   ├── bootstrap: troca o refresh token salvo por uma sessão nova (silent refresh)
   ├── login / register / logout
   │
   ▼
ProtectedRoute / PublicOnlyRoute   (guards baseados em status: loading | authenticated | unauthenticated)
   │
   ▼
apiClient   → anexa o access token; em 401, tenta uma renovação silenciosa antes de desistir
   │
   ▼
Backend
```

| Peça                                | Arquivo                                | Papel                                                        |
| ------------------------------------ | ---------------------------------------- | ------------------------------------------------------------- |
| `tokenStore`                        | `src/lib/auth/tokenStore.ts`             | Access token em memória; refresh token em `localStorage`.      |
| `auth/api`                          | `src/lib/auth/api.ts`                    | Chamadas HTTP tipadas (camelCase), mapeando o wire snake_case. |
| `apiClient`                         | `src/lib/apiClient.ts`                   | `fetch` com header de auth e retry único em 401.               |
| `AuthContext` / `AuthProvider`      | `src/context/`                           | Estado de sessão + bootstrap (ver acima).                       |
| `useAuth`                            | `src/hooks/useAuth.ts`                   | Hook de acesso ao contexto.                                     |
| `ProtectedRoute` / `PublicOnlyRoute` | `src/routes/`                            | Guards de rota.                                                 |
| `Button`, `Input`, `PasswordInput`, `Card`, `Logo` | `src/components/ui/`     | Componentes de autenticação (Sprint 1).                        |
| `AuthLayout`                         | `src/components/layout/`                 | Layout compartilhado por login e cadastro.                      |

O access token nunca é persistido (só em memória); o refresh token vai para
`localStorage` porque precisa sobreviver a um reload — é o que torna
"permanecer autenticado" possível (ver
[ADR-023](decisions.md#adr-023--sessão-do-frontend-access-token-em-memória-refresh-token-em-localstorage)).

---

## Design System e navegação protegida (Sprint 2)

Catálogo completo de componentes, tokens e convenções visuais em
[design-system.md](design-system.md). Aqui, apenas como as rotas protegidas se
encaixam:

```text
/app              (layout route: ProtectedRoute → AppLayout)
├── index             → DashboardPage      (KPICards placeholder + EmptyState)
├── uploads            → UploadsPage        (fluxo completo — Sprint 3)
├── uploads/:id         → UploadDetailPage   (metadados — Sprint 3)
├── analytics           → AnalyticsPage       (EmptyState — Sprint 5)
├── insights             → InsightsPage        (EmptyState — Sprint 6)
└── settings              → SettingsPage        (Tabs: Perfil/Preferências/Segurança)
```

`AppLayout` renderiza `Sidebar` + `Header` + `<Outlet />`; cada página nova
sob `/app` só precisa de uma rota filha — não repete layout, sidebar ou
header. `ToastProvider` envolve toda a árvore (acima do `BrowserRouter`, para
sobreviver a navegações) e é usado hoje em login, cadastro, logout e upload
(sucesso/erro).

---

## Upload de Arquivos (Frontend)

Primeiro uso real do React Query configurado desde a Sprint 0 — `useUploads.ts`
substitui o padrão manual `useState`/`useEffect` por `useQuery`/`useMutation`,
com invalidação automática da lista após criar/excluir.

```text
UploadsPage
   ├── FileUpload (drag & drop + clique)     → onFilesSelected
   ├── progresso simulado (0→90% via setInterval; 100% na resposta real)
   ├── useCreateUploadMutation                → POST /uploads (multipart)
   ├── busca (SearchInput) + ordenação (Table) → client-side, sobre a lista já carregada
   └── Table + UploadStatusBadge + Dialog de exclusão
        │
        ▼ (clique na linha)
UploadDetailPage  →  useUploadQuery(id)  →  GET /uploads/{id}
```

| Peça                        | Arquivo                                    | Papel                                                          |
| ----------------------------- | --------------------------------------------- | ------------------------------------------------------------------ |
| `uploads/api`                | `src/lib/uploads/api.ts`                       | Chamadas HTTP tipadas; `createUpload` monta o `FormData`; `processUpload` chama `POST /process`. |
| `useUploads`                  | `src/hooks/useUploads.ts`                      | `useUploadsQuery`, `useUploadQuery` (com polling — ver abaixo), `useCreateUploadMutation`, `useDeleteUploadMutation`, `useProcessUploadMutation`. |
| `FileUpload`                  | `src/components/ui/FileUpload.tsx`             | Dropzone (Design System) — cumpre a lacuna deixada em aberto na Sprint 2. |
| `Table`                       | `src/components/ui/Table.tsx`                  | Tabela genérica (Design System), sem estado próprio de ordenação.   |
| `UploadStatusBadge`           | `src/components/uploads/`                      | Composição de `Badge` específica do domínio — não é um primitivo do Design System. |
| `apiClient`                   | `src/lib/apiClient.ts`                         | Estendido para aceitar `FormData` sem forçar `Content-Type` (o navegador define o boundary multipart). |

`apiClient.ts` (Sprint 1) precisou de um ajuste: `buildRequestInit` agora
detecta `body instanceof FormData` e pula tanto o `JSON.stringify` quanto o
header `Content-Type` explícito — necessário para upload de arquivo, e
retrocompatível com todas as chamadas JSON existentes.

---

## Motor ETL (Sprint 4)

```text
Extractor  →  Transformer  →  Validação  →  Loader
  (lê)         (padroniza)     (confere)     (persiste)
```

O `ETLPipeline` recebe `Extractor`, `Transformer` e `Loader` por injeção, de
modo que cada marketplace combine suas próprias implementações sem alterar o
orquestrador; a Validação é uma função compartilhada (não uma classe por
marketplace), porque a essa altura os dados já estão no esquema canônico —
as mesmas regras valem para qualquer origem.

| Componente     | Diretório             | Responsabilidade                                            |
| -------------- | ---------------------- | ------------------------------------------------------------- |
| `Extractor`    | `etl/extractors/`      | Lê o arquivo (`FileSource`) e devolve os dados brutos.         |
| `Transformer`  | `etl/transformers/`    | Converte o formato do marketplace no esquema canônico de pedidos. |
| `validate_canonical_schema` | `etl/schema.py` | Confere que a saída do Transformer está completa e consistente. |
| `Loader`       | `etl/loaders/`         | Contrato de persistência; implementação concreta no backend.   |
| `ETLPipeline`  | `etl/pipeline.py`      | Encadeia as quatro etapas, reembrulhando qualquer falha na `ETLError` da etapa correspondente. |

**Detecção de marketplace** (`etl/detectors/`, sem IA): cada `MarketplaceDetector`
declara o conjunto de cabeçalhos que exige; `detect_marketplace` testa os
cabeçalhos normalizados do arquivo contra cada detector registrado
(`etl/detectors/registry.py`) e levanta `UnknownMarketplaceError` se nenhum
(ou mais de um) reconhecer o arquivo.

**Leitura resiliente** (`etl/parsing.py`): `read_tabular_file` despacha entre
`pandas.read_csv`/`read_excel` conforme o `SourceFormat`, sempre com
`dtype=str` (conversão de tipo é responsabilidade do Transformer, não da
leitura) e cabeçalhos normalizados (`" Data  Pedido "` → `"data_pedido"`) —
resiliente a espaços, capitalização, ordem de coluna e colunas extras.
`peek_headers` lê só o cabeçalho, para a detecção não precisar carregar o
arquivo inteiro.

**Transformação centralizada** (`etl/transformers/common.py`): todo
marketplace usa os mesmos helpers para moeda (`"R$ 1.234,56"` → `123456`
centavos, nunca `float`), data (`dd/mm/aaaa`), percentual e identificador —
evita que cada `Transformer` reimplemente (e arrisque divergir de) o mesmo
parsing. Status do marketplace vira um `OrderStatus` canônico fechado
(`completed`/`pending`/`cancelled`/`refunded`/`unknown`); um status não
mapeado vira `unknown`, não interrompe o arquivo.

**Escopo desta sprint** (ver [decisions.md](decisions.md)): dois formatos de
exemplo implementados — Shopee e Mercado Livre, com detector, extractor e
transformer próprios (`etl/detectors|extractors|transformers/{shopee,mercado_livre}.py`).
`Marketplace.AMAZON`/`Marketplace.MAGALU` existem no enum (visão de produto)
mas sem implementação — adicionar um marketplace novo é um detector +
extractor + transformer + uma entrada em `etl/components.py`, sem tocar no
`ETLPipeline`, no model `OrderItem` nem nos endpoints.

O módulo ETL continua sem conhecer SQLAlchemy nem os models do backend: o
`Loader` concreto (`app/services/etl_loader.py`) é injetado pelo
`ETLProcessorService`.

---

## Processamento de Uploads (Backend)

```text
POST /uploads/{id}/process
        │
        ▼
ETLProcessorService.process_upload(user, upload_id)
        │
        ├── Upload.status = processing; started_at = agora  (commit imediato)
        │
        ├── storage.open(...)  →  FileSource
        ├── peek_headers  →  detect_marketplace
        ├── get_pipeline_components(marketplace)  →  Extractor, Transformer
        ├── OrderItemLoader(...)
        └── ETLPipeline.run(file_source)
                │
        ┌───────┴───────┐
        ▼               ▼
   sucesso           ETLError (ou exceção inesperada)
        │               │
        ▼               ▼
processed          rollback → failed + error_message
finished_at         finished_at
```

| Peça                | Arquivo                            | Papel                                                              |
| -------------------- | ------------------------------------ | --------------------------------------------------------------------- |
| `ETLProcessorService` | `app/services/etl_processor.py`    | Orquestra: resolve o `Upload`, monta o pipeline, traduz o resultado em status. Nenhuma regra de parsing/transformação mora aqui. |
| `OrderItemLoader`    | `app/services/etl_loader.py`         | Implementa `etl.loaders.base.Loader`; delega a persistência ao repositório. |
| `OrderItemRepository` | `app/repositories/order_item.py`   | `bulk_create` (um único `INSERT` multi-linha) e `delete_for_upload` (reprocessar é idempotente). |
| `OrderItem`          | `app/models/order_item.py`           | Entidade persistida — uma linha por item de pedido já padronizado.    |

**Transação:** `Upload.status = processing` é *commitado imediatamente*
(visível a quem consultar o upload durante o processamento); se o pipeline
falhar, só o que o `Loader` tiver inserido nessa tentativa é desfeito
(`rollback`) antes de gravar `status = failed` numa transação nova — nunca há
`OrderItem` parcial de uma tentativa malsucedida.

**Sem fila real nesta sprint:** `process_upload` recebe só um `upload_id` (não
um handle de arquivo aberto nem estado em memória) — é a característica que
permite trocar "chamado direto pela rota" por "chamado por um worker Celery/
Dramatiq/RQ" sem reescrever o `ETLPipeline`, o `Extractor`/`Transformer`/
`Loader` ou o endpoint (só o que acontece *dentro* do endpoint mudaria). Ver
ADR em decisions.md.

**Resposta HTTP sempre `200`, mesmo em falha de processamento:** um
marketplace não reconhecido ou um arquivo corrompido não é um erro da
requisição — é um resultado válido do processamento, refletido em
`Upload.status`/`error_message` (contrato completo em
[api.md](api.md#post-apiv1uploadsidprocess)). Só a ausência do upload (ou
pertencer a outro usuário) é `404`.

---

## Processamento de Uploads (Frontend)

O botão "Processar" (Uploads e detalhe do upload) chama
`useProcessUploadMutation`, que invalida a lista e o upload individual ao
concluir. `useUploadQuery` faz *polling* (`refetchInterval`, 1,5s) enquanto
`status === "processing"` — hoje a resposta já chega resolvida (processamento
síncrono), então o polling nunca chega a repetir na prática, mas é o que
deixa a página pronta para quando o backend passar a responder
`"processing"` por mais tempo (fila real), sem nenhuma mudança de código no
frontend.

`UploadDetailPage` mostra início/fim/duração (`formatDuration`, calculada a
partir de `started_at`/`finished_at`) e a mensagem de erro quando
`status === "failed"` — nunca os dados extraídos (`OrderItem`) em si; a
visão agregada desses dados é o Dashboard de Analytics (abaixo).

---

## Analytics (Backend)

```text
Router (routes/analytics.py)
        │
        ▼
AnalyticsService  — valida filtro (from <= to), converte centavos → reais
        │
        ▼
AnalyticsRepository  — só SELECT agregado (SUM/COUNT DISTINCT/GROUP BY)
        │
        ▼
PostgreSQL  (OrderItem, sempre WHERE user_id = :usuário_autenticado)
```

| Peça                  | Arquivo                          | Papel                                                                 |
| ---------------------- | ----------------------------------- | ------------------------------------------------------------------------ |
| `routes/analytics.py`  | `app/api/routes/analytics.py`      | Quatro endpoints (`overview`, `sales-over-time`, `orders-by-status`, `top-products`); só parsing de query params, nenhuma regra de negócio. |
| `AnalyticsService`     | `app/services/analytics.py`        | Valida o período, monta `AnalyticsFilters`, converte centavos (`int`) em reais (`float`) — só nesta borda, nunca nos cálculos. |
| `AnalyticsRepository`  | `app/repositories/analytics.py`    | Toda agregação em SQL; nenhum `OrderItem` é carregado linha a linha para o Python somar. |

**KPIs e o que cada um mede** (contrato completo com exemplos em
[api.md](api.md#analytics)): `revenue` (soma de `total_price_cents` dos itens
`completed`), `orders` (`COUNT(DISTINCT external_order_id)` — nunca a
contagem de `OrderItem`, que é por item, não por pedido), `average_order_value`
(`revenue / orders`, `0` se não houver pedidos), `active_products`
(`COUNT(DISTINCT sku)`). Todos os quatro — e `sales-over-time` e
`top-products` — consideram **somente** `status = completed`; só
`orders-by-status` mostra a distribuição entre todos os status, de propósito
(ver [ADR-062](decisions.md#adr-062--kpis-de-analytics-consideram-somente-orderitem-com-status-completed)).

**Filtros:** `from`/`to` (data) e `marketplace`, opcionais e combináveis,
aplicados como `WHERE` adicionais por `build_order_item_conditions`
(função de módulo em `app/repositories/analytics.py` — não mais um método
"privado" de `AnalyticsRepository` desde a Sprint 6, para que
`InsightsRepository` reaproveite a mesma lógica sem acessar um método
interno de outra classe; ver
[ADR-067](decisions.md#adr-067--insightsrepository-reaproveita-analyticsrepository-em-vez-de-duplicar-sql)).
Sem filtro, considera todo o histórico do usuário. `AnalyticsService` rejeita
`from > to` com `422` antes de qualquer consulta.

**Isolamento por usuário:** todo método de `AnalyticsRepository` recebe
`user_id` explicitamente e o usa como primeira condição do `WHERE` — o valor
vem sempre de `CurrentUserDep` (o token), nunca de um parâmetro do cliente.

**`has_data`:** calculado por uma consulta `EXISTS` separada, ignorando
filtro e status — permite ao frontend diferenciar "usuário nunca importou
nada" (mostra o EmptyState de onboarding) de "o filtro atual não bateu com
nada" (mostra KPIs zerados de verdade) — ver
[ADR-063](decisions.md#adr-063--campo-has_data-para-distinguir-sem-dados-de-filtro-sem-resultado).

---

## Analytics (Frontend)

```text
DashboardPage
   ├── useOverviewQuery(filters)              → GET /analytics/overview
   │      ├── isError            → mensagem de erro + "Tentar novamente"
   │      ├── isSuccess && !hasData → EmptyState (ir para /app/uploads)
   │      └── isSuccess && hasData  → KPICards + gráficos + tabela
   ├── AnalyticsFilters (período + marketplace) → atualiza `filters` (state)
   ├── useSalesOverTimeQuery(filters)          → RevenueChart + OrdersChart
   ├── useOrdersByStatusQuery(filters)         → OrderStatusChart
   └── useTopProductsQuery(filters, limit)     → TopProductsTable
```

Trocar um filtro atualiza o `state` de `DashboardPage`; como `filters` entra
na `queryKey` de cada hook, o React Query refaz a busca sozinho — nenhum
dado já carregado é refiltrado no cliente.

| Peça                  | Arquivo                                  | Papel                                                              |
| ---------------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| `lib/analytics/api`    | `src/lib/analytics/api.ts`                | Chamadas HTTP tipadas (camelCase); monta a query string dos filtros. |
| `useAnalytics`         | `src/hooks/useAnalytics.ts`               | `useOverviewQuery`, `useSalesOverTimeQuery`, `useOrdersByStatusQuery`, `useTopProductsQuery`. |
| `components/analytics/` | `AnalyticsFilters`, `RevenueChart`, `OrdersChart`, `OrderStatusChart`, `TopProductsTable` | Componentes novos do Design System — reaproveitam `Card`/`Table`/`Skeleton`/`EmptyState` já existentes; cores dos gráficos vêm dos tokens já definidos (`--color-primary`, `--color-emerald-*`, `--color-danger`), nenhuma cor nova. |

Três estados tratados explicitamente (não apenas "carregando" vs.
"carregado"): **erro** (mensagem específica + retry, nunca um "—" silencioso
— requisito explícito da sprint), **sem dados** (`EmptyState` completo, com
ação para `/app/uploads`, só quando `has_data` é `false`) e **filtro sem
resultado** (KPIs zerados de verdade, sem esconder os filtros — `has_data`
continua `true`).

---

## Business Insights (Backend)

```text
Router (routes/insights.py)
        │
        ▼
InsightsService  — valida filtro (from <= to), matemática de período, 6 regras
        │
        ▼
InsightsRepository  — compõe AnalyticsRepository; só uma agregação nova (por marketplace)
        │
        ▼
PostgreSQL  (OrderItem, sempre WHERE user_id = :usuário_autenticado)
```

| Peça                  | Arquivo                          | Papel                                                                 |
| ---------------------- | ----------------------------------- | ------------------------------------------------------------------------ |
| `routes/insights.py`   | `app/api/routes/insights.py`       | Um endpoint (`GET /insights`); reaproveita os `Query()` de `routes/analytics.py`, não os redefine. |
| `InsightsService`      | `app/services/insights.py`         | Seis regras determinísticas (`_build_*`), cálculo do "período anterior equivalente", nenhuma consulta SQL. |
| `InsightsRepository`   | `app/repositories/insights.py`     | Compõe `AnalyticsRepository` (mesma sessão) para totais de período e receita por produto; só a receita agrupada por marketplace é uma consulta nova. |

**Diferença de Analytics:** Analytics expõe métricas (faturamento, pedidos);
Insights interpreta essas métricas e produz observações em texto pronto
("seu faturamento caiu 19,7%"), com severidade (`positive`/`negative`/
`neutral`) e um percentual — nunca uma string solta sem número por trás (ver
contrato completo em [api.md](api.md#business-insights)).

**Sem IA/ML** — cada um dos seis tipos é uma regra aritmética simples e
documentada (ADR-065/066 em [decisions.md](decisions.md)):

1. `revenue_trend`, `orders_trend`, `average_order_value_trend` — variação
   percentual entre o período selecionado e um "período anterior
   equivalente" (mesmo número de dias, imediatamente antes).
2. `top_product` — produto com maior faturamento no período, com
   participação percentual no total.
3. `product_decline` — produto relevante (≥ 10% do faturamento do período
   anterior) com a maior queda percentual.
4. `best_marketplace` — marketplace com maior faturamento, só quando há
   ≥ 2 marketplaces com faturamento no recorte filtrado.

**No máximo 5 consultas por requisição**, nunca uma por insight: totais do
período atual, produtos do período atual, receita por marketplace do
período atual e, só quando `from`/`to` estão os dois presentes, totais e
produtos do período anterior. As seis regras são funções puras em Python
sobre esses resultados já agregados — nenhum loop grande, nenhuma consulta
por produto individual (ver
[ADR-067](decisions.md#adr-067--insightsrepository-reaproveita-analyticsrepository-em-vez-de-duplicar-sql)).

**Período atual e anterior:** insights de comparação (1) só existem quando
`from` **e** `to` são informados — sem os dois não há um comprimento de
janela para definir um período anterior, e a regra simplesmente não gera o
insight (não inventa uma janela padrão). Ver
[ADR-065](decisions.md#adr-065--período-atual-e-anterior-em-insights) para a
fórmula exata e o racional.

**`has_data`:** mesmo papel do campo homônimo em Analytics — calculado uma
vez por `InsightsRepository.has_any_data` (reaproveita
`AnalyticsRepository.has_any_data`), ignora filtro e status.

---

## Business Insights (Frontend)

```text
DashboardPage
   └── InsightsSection (filters)                  → GET /insights
          ├── isLoading                → skeletons
          ├── isError                  → mensagem de erro + "Tentar novamente"
          ├── isSuccess && !hasData    → nada (a página já mostra o EmptyState de onboarding)
          ├── isSuccess && insights=[] → EmptyState leve ("dados insuficientes")
          └── isSuccess && insights.length > 0 → grade de InsightCard
```

`InsightsSection` faz sua **própria** busca (`useInsightsQuery`), não deriva
de `useOverviewQuery` — tem seus próprios estados de carregamento/erro,
distintos dos KPIs, mas é renderizada dentro do mesmo bloco condicional dos
gráficos em `DashboardPage` (evita buscar/mostrar Insights quando a página
inteira já está no EmptyState de onboarding).

| Peça                  | Arquivo                                  | Papel                                                              |
| ---------------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| `lib/insights/api`     | `src/lib/insights/api.ts`                 | Chamadas HTTP tipadas; reaproveita o tipo `AnalyticsFilters` de `lib/analytics/api` (mesmos filtros). |
| `useInsights`          | `src/hooks/useInsights.ts`                | `useInsightsQuery(filters)` — `filters` na `queryKey`, mesmo padrão da Sprint 5. |
| `components/insights/` | `InsightCard`, `InsightsSection`          | `InsightCard` é puramente apresentacional (ícone/cor por severidade); `InsightsSection` decide qual estado mostrar. |

**Cor e ícone por severidade** — `positive` (verde, seta para cima),
`negative` (vermelho, seta para baixo), `neutral` (cor primária, ícone de
destaque) — nunca por `type`: o mesmo tipo (`revenue_trend`) pode ser
positivo ou negativo dependendo dos dados. O sinal (`+`/`-`) no valor também
vem da severidade, não do tipo.

**Animação:** `InsightCard` usa `motion.div` (fade + leve deslocamento
vertical) para entrada/saída — a lista inteira muda quando o filtro muda,
então cartões aparecendo/sumindo merecem uma transição (Framer Motion usado
seletivamente, mesmo critério do design-system.md).

---

## Banco de Dados

- Cada usuário possuirá seu próprio workspace.
- Todas as entidades principais serão vinculadas ao usuário autenticado —
  `Upload` foi a primeira entidade de negócio a seguir esse padrão
  (`user_id` com `ondelete="CASCADE"`, mesmo relacionamento de `RefreshToken`);
  `OrderItem` (Sprint 4) segue o mesmo padrão, com `user_id` **e**
  `upload_id` (ambos `ondelete="CASCADE"` — excluir um upload remove seus
  itens; excluir o usuário remove tudo).
- `OrderItem` reaproveita os enums `Marketplace`/`OrderStatus` do pacote
  `etl` (`etl.types`) na coluna do model, em vez de duplicar os valores no
  lado do backend — o mesmo `Marketplace` que o pipeline detecta é o que fica
  gravado.
- As migrations serão gerenciadas pelo Alembic.
- A `Base` declarativa (`app/db/base.py`) define uma convenção de nomes
  explícita para índices e constraints, garantindo migrations reversíveis
  (ADR-006).
- O Alembic resolve a URL de conexão em tempo de execução a partir das settings
  da aplicação, e não do `alembic.ini` (ADR-007).

---

## Configuração

Toda a configuração vem de variáveis de ambiente, tipadas e validadas por
`Settings` (Pydantic Settings) em `app/core/config.py`. Um único `.env` na raiz
atende ao Docker Compose e ao backend (ADR-013). Nenhum segredo é versionado —
`.env.example` documenta as variáveis disponíveis.

---

## Infraestrutura

### Docker

Um Dockerfile por serviço, multi-stage, com dois alvos:

| Alvo          | Uso                | Características                                   |
| ------------- | ------------------ | ------------------------------------------------- |
| `development` | Docker Compose     | Hot reload, dependências de desenvolvimento.       |
| `production`  | CI / deploy        | Backend sem privilégios; frontend servido por Nginx. |

Ambos usam a **raiz do repositório** como contexto de build (ADR-014). No
alvo `production`, `/app/storage` é a única exceção ao "sem privilégios sobre
o próprio código": pertence ao usuário da aplicação, porque os uploads
(Sprint 3) são gravados ali em runtime — sem isso, `UploadService` falharia
com `PermissionError` (achado durante a validação Docker desta sprint).

### Integração Contínua

`.github/workflows/ci.yml` roda em três jobs paralelos:

1. **Backend** — Ruff (lint + formatação), MyPy (strict), migration do Alembic
   (`upgrade`/`downgrade`/`upgrade` contra um serviço PostgreSQL real) e Pytest
   com cobertura (ver [ADR-019](decisions.md#adr-019--suíte-de-testes-com-sqlite-por-padrão-postgresql-real-na-ci)).
2. **Frontend** — ESLint, Prettier, `tsc`, Vitest e build do Vite.
3. **Docker** — build das imagens de produção (depende dos dois anteriores).

---

## Princípios do Projeto

- Arquitetura em camadas.
- Responsabilidade única.
- Tipagem forte.
- Componentes reutilizáveis.
- Testes automatizados.
- Código limpo.
- Documentação contínua.
- CI/CD.
- Interface moderna com foco em experiência do usuário.

---

## Decisões

As decisões técnicas relevantes, com contexto, alternativas descartadas e
consequências, estão registradas em [decisions.md](decisions.md).

## Referência da API

Endpoints, contratos de requisição/resposta e o fluxo completo de
autenticação estão documentados em [api.md](api.md).

## Design System

Catálogo de componentes, tokens visuais e convenções de acessibilidade em
[design-system.md](design-system.md).
