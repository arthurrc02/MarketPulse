# MarketPulse

Plataforma SaaS que transforma relatórios de marketplaces em informações
estratégicas para tomada de decisão.

Vendedores que atuam em vários marketplaces recebem relatórios em formatos
diferentes, o que dificulta consolidar os dados e avaliar o desempenho do
negócio. O MarketPulse importa arquivos CSV e Excel de **Shopee, Mercado Livre,
Amazon e Magalu**, padroniza tudo em um único modelo de dados e apresenta
indicadores, gráficos e insights automáticos em um dashboard moderno.

> **Status:** Sprint 4 (ETL Engine) concluída. Além do upload (Sprint 3),
> usuários já conseguem processar seus arquivos: o motor ETL detecta o
> marketplace de origem automaticamente (dois formatos de exemplo — Shopee e
> Mercado Livre, arquitetura pronta para os demais), normaliza os dados
> (moeda, data, percentual) e persiste os itens padronizados. Nenhum
> dashboard, gráfico ou insight sobre esses dados existe ainda — começam na
> Sprint 5 em diante.

---

## Stack

| Camada             | Tecnologias                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **Backend**        | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 · PostgreSQL 16 · PyJWT · bcrypt |
| **Frontend**       | React 19 · TypeScript · Vite · Tailwind CSS 4 · React Router · React Query · Framer Motion |
| **ETL**            | Pandas · OpenPyXL                                                           |
| **Infraestrutura** | Docker · Docker Compose · GitHub Actions                                     |
| **Qualidade**      | Ruff · MyPy (strict) · Pytest · ESLint · Prettier · Vitest                   |

---

## Início rápido

```bash
cp .env.example .env
docker compose up --build
```

| Serviço    | URL                          |
| ---------- | ---------------------------- |
| Frontend   | http://localhost:5173        |
| API        | http://localhost:8000        |
| Health     | http://localhost:8000/health |
| Swagger UI | http://localhost:8000/docs   |

Depois de subir os contêineres, aplique as migrations para criar as tabelas
de autenticação e uploads:

```bash
docker compose exec backend alembic upgrade head
```

O setup local (sem Docker), as variáveis de ambiente e os comandos de migration
estão em **[docs/setup.md](docs/setup.md)**; os endpoints disponíveis em
**[docs/api.md](docs/api.md)**.

---

## Estrutura

```text
backend/     API FastAPI em camadas (api → services → repositories → db)
etl/         Motor ETL (extractors, transformers, loaders)
frontend/    React + TypeScript — auth completa, Design System, uploads e navegação
storage/     Arquivos enviados via upload (bind mount, fora do Git)
docker/      Dockerfiles e configuração do Nginx
docs/        Documentação do projeto
.github/     Pipelines de CI
```

Backend e ETL formam um **workspace do uv**: um único `uv sync --all-packages`
na raiz instala os dois pacotes e o ferramental de desenvolvimento.

---

## Qualidade

```bash
# Backend + ETL
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest

# Frontend
cd frontend
npm run lint && npm run format:check && npm run typecheck && npm run test && npm run build
```

As mesmas verificações rodam na CI a cada `push` e `pull_request` para `main`,
somadas ao build das imagens Docker de produção.

---

## Documentação

| Documento                                   | Conteúdo                                    |
| ------------------------------------------- | ------------------------------------------- |
| [product-vision.md](docs/product-vision.md) | Visão de produto e objetivos                |
| [architecture.md](docs/architecture.md)     | Arquitetura, camadas e stack                |
| [design-system.md](docs/design-system.md)   | Identidade visual e catálogo de componentes |
| [roadmap.md](docs/roadmap.md)               | Sprints e escopo de cada entrega            |
| [api.md](docs/api.md)                       | Referência dos endpoints e fluxo de autenticação |
| [setup.md](docs/setup.md)                   | Instalação, execução e solução de problemas |
| [decisions.md](docs/decisions.md)           | Registro de decisões técnicas (ADRs)        |

---

## Roadmap

| Sprint | Entrega                             | Status       |
| ------ | ----------------------------------- | ------------ |
| 0      | Foundation                          | ✅ Concluída |
| 1      | Authentication                      | ✅ Concluída |
| 2      | Design System & Frontend Foundation | ✅ Concluída |
| 3      | File Import                         | ✅ Concluída |
| 4      | ETL Engine                          | ✅ Concluída |
| 5      | Analytics Dashboard                 | ⏳ Próxima   |
| 6      | Business Insights                   | ⬜ Planejada |
| 7      | Release Candidate                   | ⬜ Planejada |
