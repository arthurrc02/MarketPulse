# MarketPulse

Plataforma SaaS que transforma relatórios de marketplaces em informações
estratégicas para tomada de decisão.

Vendedores que atuam em vários marketplaces recebem relatórios em formatos
diferentes, o que dificulta consolidar os dados e avaliar o desempenho do
negócio. O MarketPulse importa arquivos CSV e Excel de **Shopee, Mercado Livre,
Amazon e Magalu**, padroniza tudo em um único modelo de dados e apresenta
indicadores, gráficos e insights automáticos em um dashboard moderno.

> **Status:** Sprint 2 (Design System & Frontend Foundation) concluída. Além
> da autenticação completa (Sprint 1), o produto agora tem identidade visual
> própria: Design System com 18 componentes, dashboard real (sidebar, header,
> cards de exemplo) e navegação preparada para Uploads, Analytics, Insights e
> Configurações. Nenhuma funcionalidade de negócio (marketplaces, upload,
> ETL, dados reais) existe ainda — começam na Sprint 3 em diante.

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

Depois de subir os contêineres, aplique a migration para criar as tabelas de
autenticação:

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
frontend/    React + TypeScript — auth completa, Design System, dashboard e navegação
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
| 3      | File Import                         | ⏳ Próxima   |
| 4      | ETL Engine                          | ⬜ Planejada |
| 5      | Analytics Dashboard                 | ⬜ Planejada |
| 6      | Business Insights                   | ⬜ Planejada |
| 7      | Release Candidate                   | ⬜ Planejada |
