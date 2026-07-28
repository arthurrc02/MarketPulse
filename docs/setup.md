# MarketPulse — Setup

Guia para colocar o ambiente de desenvolvimento do MarketPulse no ar.

---

## Pré-requisitos

| Ferramenta         | Versão mínima | Observação                                      |
| ------------------ | ------------- | ----------------------------------------------- |
| **Docker**         | 24            | Caminho recomendado — sobe tudo com um comando.  |
| **Docker Compose** | v2            | Já incluído no Docker Desktop.                   |
| **uv**             | 0.5           | Necessário apenas no setup local (sem Docker).   |
| **Python**         | 3.12          | O `uv` instala a versão correta automaticamente. |
| **Node.js**        | 20.19         | Necessário apenas no setup local (sem Docker).   |

---

## Estrutura do repositório

```text
MarketPulse/
├── backend/            # API FastAPI (arquitetura em camadas)
│   ├── app/
│   │   ├── api/        # Routers e dependências HTTP
│   │   ├── core/       # Settings e logging
│   │   ├── db/         # Engine, sessão e base declarativa
│   │   ├── models/     # Models SQLAlchemy (vazio na Sprint 0)
│   │   ├── repositories/
│   │   ├── schemas/    # Contratos Pydantic
│   │   └── services/   # Regras de negócio
│   ├── migrations/     # Alembic
│   └── tests/
├── etl/                # Motor ETL (apenas contratos na Sprint 0)
│   ├── etl/
│   │   ├── extractors/
│   │   ├── transformers/
│   │   └── loaders/
│   └── tests/
├── frontend/           # Aplicação React + TypeScript + Vite
│   └── src/
│       ├── lib/        # QueryClient, env
│       ├── pages/      # Páginas
│       ├── routes/     # Roteamento
│       ├── styles/     # Tailwind
│       └── test/       # Setup do Vitest
├── docker/             # Dockerfiles e configuração do Nginx
├── docs/               # Documentação do projeto
├── .github/workflows/  # Pipelines de CI
├── docker-compose.yml
└── pyproject.toml      # Workspace uv (backend + etl)
```

---

## Variáveis de ambiente

Um único `.env` na raiz atende ao Docker Compose e ao backend:

```bash
cp .env.example .env
```

| Variável                            | Padrão                  | Descrição                                |
| ----------------------------------- | ----------------------- | ---------------------------------------- |
| `ENVIRONMENT`                       | `local`                 | `local`, `development`, `staging` ou `production`. |
| `LOG_LEVEL`                         | `INFO`                  | Nível de log do backend.                  |
| `POSTGRES_USER` / `_PASSWORD` / `_DB` | `marketpulse`         | Credenciais do PostgreSQL.                |
| `POSTGRES_HOST` / `_PORT`           | `localhost` / `5432`    | Host e porta do banco.                    |
| `BACKEND_PORT` / `FRONTEND_PORT`    | `8000` / `5173`         | Portas publicadas pelo Compose.           |
| `CORS_ORIGINS`                      | `http://localhost:5173` | Origens permitidas (separadas por vírgula). |
| `VITE_API_URL`                      | `http://localhost:8000` | URL da API consumida pelo frontend.       |

> Em `production`, a documentação interativa (`/docs`, `/redoc`, `/openapi.json`) é desabilitada automaticamente.

---

## Opção 1 — Docker (recomendado)

```bash
cp .env.example .env
docker compose up --build
```

| Serviço    | URL                            |
| ---------- | ------------------------------ |
| Frontend   | http://localhost:5173          |
| API        | http://localhost:8000          |
| Health     | http://localhost:8000/health   |
| Swagger UI | http://localhost:8000/docs     |
| PostgreSQL | `localhost:5432`               |

Comandos úteis:

```bash
docker compose logs -f backend     # acompanhar logs
docker compose down                # parar os serviços
docker compose down -v             # parar e apagar o volume do banco
docker compose exec backend bash   # shell dentro do contêiner
```

Os Dockerfiles são multi-stage: o Compose usa o alvo `development` (hot reload no
backend e no frontend); a CI constrói o alvo `production` (Uvicorn sem `--reload`
e assets estáticos servidos por Nginx).

---

## Opção 2 — Local, sem Docker

### Backend + ETL

O repositório é um **workspace do uv**: um único `uv sync` na raiz instala o
backend, o ETL e as ferramentas de desenvolvimento em `.venv/`.

```bash
uv sync --all-packages
```

Suba um PostgreSQL (via Docker ou instalação local) e rode a API:

```bash
docker compose up -d postgres      # opcional: só o banco
cd backend
uv run uvicorn app.main:app --reload
```

Qualidade:

```bash
uv run ruff check .          # lint
uv run ruff format .         # formatação
uv run mypy                  # type checking (strict)
uv run pytest                # testes (backend + etl)
uv run pytest --cov          # com cobertura
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Qualidade:

```bash
npm run lint          # ESLint
npm run format:check  # Prettier
npm run typecheck     # TypeScript
npm run test          # Vitest
npm run build         # build de produção
```

---

## Migrations (Alembic)

Todos os comandos rodam a partir de `backend/`. A URL de conexão é resolvida em
tempo de execução por `migrations/env.py` a partir das settings da aplicação —
não é preciso preencher `sqlalchemy.url` no `alembic.ini`.

```bash
cd backend
uv run alembic revision --autogenerate -m "descrição da mudança"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic current
```

> A Sprint 0 não possui migrations: nenhum model de negócio foi criado ainda. A
> primeira revisão nasce na Sprint 1, junto do model de usuário.

---

## Verificando a instalação

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "service": "MarketPulse API",
  "version": "0.1.0",
  "environment": "local"
}
```

O frontend em http://localhost:5173 deve exibir a página temporária informando
que o projeto está em desenvolvimento.

---

## Integração contínua

O workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) roda em
`push` e `pull_request` para `main`, em três jobs:

1. **Backend** — Ruff (lint + formatação), MyPy (strict) e Pytest com cobertura.
2. **Frontend** — ESLint, Prettier, `tsc`, Vitest e build do Vite.
3. **Docker** — constrói as imagens de produção do backend e do frontend.

Rode o equivalente localmente antes de abrir um PR:

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
cd frontend && npm run lint && npm run format:check && npm run typecheck && npm run test && npm run build
```

---

## Solução de problemas

**`uv sync` falha ao encontrar o Python 3.12**
O `uv` baixa a versão automaticamente; se estiver offline, instale o Python 3.12
manualmente e rode `uv python pin 3.12`.

**Backend não conecta ao banco no Docker**
Dentro do Compose o host do banco é `postgres`, não `localhost`. O Compose já
injeta `POSTGRES_HOST=postgres`; não sobrescreva isso no `.env`.

**Porta 5432 já em uso**
Ajuste `POSTGRES_PORT` no `.env` — apenas a porta publicada no host muda.

**Hot reload do frontend não funciona no Docker**
O polling do watcher é ativado pela variável `CHOKIDAR_USEPOLLING`, já definida
pelo Compose. Fora do Docker ela fica desligada, para não consumir CPU à toa.

**Erro de CORS no navegador**
Adicione a origem em `CORS_ORIGINS` no `.env` e recrie o backend
(`docker compose up -d --force-recreate backend`).
