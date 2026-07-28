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
- JWT Authentication (Sprint 1)
- Passlib/Bcrypt (Sprint 1)
- Pytest

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- React Query
- Tailwind CSS 4
- Recharts (Sprint 5)
- Framer Motion (Sprint 2)

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

| Camada     | Diretório       | Responsabilidade                             |
| ---------- | --------------- | -------------------------------------------- |
| Pages      | `src/pages/`    | Telas completas.                              |
| Routes     | `src/routes/`   | Definição de rotas e redirecionamentos.       |
| Components | `src/components/` | Design System e componentes reutilizáveis (Sprint 2). |
| Hooks      | `src/hooks/`    | Lógica de UI e consultas ao React Query (Sprint 2).   |
| Lib        | `src/lib/`      | QueryClient, cliente HTTP e configuração.     |
| Styles     | `src/styles/`   | Tokens e camadas base do Tailwind.            |

O alias `@/` aponta para `src/`, configurado tanto no Vite quanto no TypeScript.

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

1. **Backend** — Ruff (lint + formatação), MyPy (strict) e Pytest com cobertura.
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
