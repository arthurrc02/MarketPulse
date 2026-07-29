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
- Recharts (Sprint 5)

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
| Hooks      | `src/hooks/`              | `useAuth`, `useToast`. Consultas ao React Query chegam com o primeiro dado real (Sprint 3+). |
| Lib        | `src/lib/`                | `apiClient`, `auth/api`, `auth/tokenStore`, QueryClient, `env`.     |
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
/app          (layout route: ProtectedRoute → AppLayout)
├── index         → DashboardPage      (KPICards placeholder + EmptyState)
├── uploads        → UploadsPage        (EmptyState — Sprint 3)
├── analytics       → AnalyticsPage       (EmptyState — Sprint 5)
├── insights        → InsightsPage        (EmptyState — Sprint 6)
└── settings        → SettingsPage        (Tabs: Perfil/Preferências/Segurança)
```

`AppLayout` renderiza `Sidebar` + `Header` + `<Outlet />`; cada página nova
sob `/app` só precisa de uma rota filha — não repete layout, sidebar ou
header. `ToastProvider` envolve toda a árvore (acima do `BrowserRouter`, para
sobreviver a navegações) e é usado hoje em login, cadastro e logout
bem-sucedidos.

---

## Arquitetura do ETL

```text
Extractor  →  Transformer  →  Loader
  (lê)         (padroniza)     (persiste)
```

O `ETLPipeline` recebe as três etapas por injeção, de modo que cada marketplace
combine suas próprias implementações sem alterar o orquestrador:

| Componente    | Diretório           | Responsabilidade                                          |
| ------------- | ------------------- | --------------------------------------------------------- |
| `Extractor`   | `etl/extractors/`   | Lê o arquivo de origem e devolve os dados brutos.          |
| `Transformer` | `etl/transformers/` | Converte o formato do marketplace no modelo canônico.      |
| `Loader`      | `etl/loaders/`      | Persiste os dados padronizados.                            |
| `ETLPipeline` | `etl/pipeline.py`   | Encadeia as três etapas e resume o resultado.              |

O módulo ETL não conhece SQLAlchemy nem os models do backend: o `Loader`
concreto é injetado pela camada de serviço, mantendo o motor independente da
infraestrutura de persistência.

> Na Sprint 0 apenas os contratos existem. As implementações por marketplace
> chegam na Sprint 4.

---

## Banco de Dados

- Cada usuário possuirá seu próprio workspace.
- Todas as entidades principais serão vinculadas ao usuário autenticado.
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

Ambos usam a **raiz do repositório** como contexto de build (ADR-014).

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
