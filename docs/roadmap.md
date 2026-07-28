# MarketPulse — Roadmap

| Sprint | Entrega                             | Status       |
| ------ | ----------------------------------- | ------------ |
| 0      | Foundation                          | ✅ Concluída |
| 1      | Authentication                      | ⏳ Próxima   |
| 2      | Design System & Frontend Foundation | ⬜ Planejada |
| 3      | File Import                         | ⬜ Planejada |
| 4      | ETL Engine                          | ⬜ Planejada |
| 5      | Analytics Dashboard                 | ⬜ Planejada |
| 6      | Business Insights                   | ⬜ Planejada |
| 7      | Release Candidate                   | ⬜ Planejada |

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

## Sprint 1 — Authentication ⏳

**Objetivo:** cadastro, login e proteção de rotas com JWT.

**Escopo previsto:**

- Model `User` e primeira migration do Alembic.
- Hash de senha com Passlib/Bcrypt.
- Endpoints `POST /api/v1/auth/register`, `POST /api/v1/auth/login` e
  `GET /api/v1/users/me`, sob o prefixo versionado.
- Dependência `get_current_user` para proteção de rotas.
- Repositório e serviço de usuários seguindo as camadas já estabelecidas.
- Testes de integração com banco de teste.
- CI passa a subir um serviço PostgreSQL para os testes.

---

## Sprint 2 — Design System & Frontend Foundation ⬜

**Objetivo:** identidade visual e componentes reutilizáveis.

**Escopo previsto:**

- Paleta completa e tokens de tipografia, espaçamento e raio em `@theme`.
- Componentes de layout, inputs, feedback, dados e navegação descritos em
  [design-system.md](design-system.md).
- Framer Motion para transições de página e micro animações.
- Cliente HTTP e hooks de React Query.
- Telas de login e cadastro consumindo a API da Sprint 1.
- Reavaliação de hooks de pré-commit (`pre-commit` / `lint-staged`), adiados na
  Sprint 0 (ADR-009).

---

## Sprint 3 — File Import ⬜

**Objetivo:** upload de arquivos CSV e Excel.

**Escopo previsto:**

- Endpoint de upload com validação de formato e tamanho.
- Armazenamento dos arquivos e registro de importações.
- Detecção automática do marketplace de origem.
- Componente `FileUpload` com feedback de progresso.
- Endpoint `GET /ready` (readiness), verificando conexão com o banco (ADR-002).

---

## Sprint 4 — ETL Engine ⬜

**Objetivo:** implementar o processamento dos dados.

**Escopo previsto:**

- Implementações de `Extractor`, `Transformer` e `Loader` para Shopee, Mercado
  Livre, Amazon e Magalu.
- Execução real de `ETLPipeline.run`.
- Modelo canônico de pedidos e produtos, com as migrations correspondentes.
- Tratamento de erros por linha e relatório de importação.
- Testes com arquivos de exemplo de cada marketplace.

---

## Sprint 5 — Analytics Dashboard ⬜

**Objetivo:** indicadores e gráficos.

**Escopo previsto:**

- Endpoints de métricas: faturamento, ticket médio, pedidos, produtos mais
  vendidos, desempenho por marketplace, evolução temporal e categorias.
- Dashboard com KPI Cards e gráficos (Recharts).
- Filtros por período, marketplace e categoria.

---

## Sprint 6 — Business Insights ⬜

**Objetivo:** observações automáticas baseadas em regras de negócio.

**Escopo previsto:**

- Motor de regras sobre os dados consolidados.
- Detecção de crescimento/queda de faturamento, variação de ticket médio,
  produtos em destaque e melhores canais.
- Apresentação dos insights no dashboard.

---

## Sprint 7 — Release Candidate ⬜

**Objetivo:** preparar o produto para apresentação.

**Escopo previsto:**

- Refino de UX, estados de carregamento e tratamento de erros.
- Responsividade para notebook e tablet.
- Ampliação da cobertura de testes e testes end-to-end.
- Documentação final e roteiro de demonstração.
- Deploy de demonstração.
