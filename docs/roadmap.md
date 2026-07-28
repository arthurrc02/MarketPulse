# MarketPulse — Roadmap

| Sprint | Entrega                             | Status       |
| ------ | ----------------------------------- | ------------ |
| 0      | Foundation                          | ✅ Concluída |
| 1      | Authentication                      | ✅ Concluída |
| 2      | Design System & Frontend Foundation | ⏳ Próxima   |
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

## Sprint 2 — Design System & Frontend Foundation ⏳

**Objetivo:** identidade visual e componentes reutilizáveis.

**Escopo previsto:**

- Paleta completa e tokens de tipografia, espaçamento e raio em `@theme`
  (os tokens da Sprint 1 — cor primária, borda, erro — são o ponto de
  partida, não um recomeço).
- Componentes de layout (AppLayout, Sidebar, Header, PageContainer, Section)
  e os demais catálogos descritos em [design-system.md](design-system.md).
- Framer Motion para transições de página e micro animações.
- Hooks de React Query para dados de negócio (a base do React Query já está
  configurada desde a Sprint 0).
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
