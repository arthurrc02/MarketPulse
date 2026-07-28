# MarketPulse — Registro de Decisões Técnicas (ADR)

Cada entrada registra uma decisão relevante de arquitetura ou processo: o
contexto, a decisão tomada, as alternativas descartadas e as consequências.

**Status possíveis:** `Aceita` · `Substituída` · `Descartada`

---

## ADR-001 — Workspace único do uv para backend e ETL

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O `etl/` é um módulo independente do backend, mas consumido por
ele. Precisávamos decidir se seriam dois projetos Python separados, se o ETL
viveria dentro de `backend/app/`, ou algo entre os dois.

**Decisão.** Usar um **workspace do uv** na raiz, com `backend/` e `etl/` como
membros e um único `uv.lock`. O backend declara `marketpulse-etl` como
dependência via `[tool.uv.sources] ... { workspace = true }`.

**Alternativas descartadas.**

- _ETL dentro de `backend/app/etl/`_: mais simples, mas acopla o motor ETL ao
  ciclo de vida da API e impede reaproveitá-lo em jobs/CLI no futuro.
- _Dois projetos com lockfiles separados_: risco de divergência de versões de
  `pandas`/`numpy` entre os dois ambientes e dois `sync` para manter.

**Consequências.** Um `uv sync --all-packages` prepara tudo; Ruff, MyPy e Pytest
são configurados uma única vez na raiz. Em contrapartida, o build Docker do
backend precisa usar a **raiz do repositório** como contexto.

---

## ADR-002 — `GET /health` é liveness, não readiness

**Sprint:** 0 · **Status:** Aceita

**Contexto.** Health checks costumam verificar dependências externas (banco,
cache, filas). Era preciso definir o que `/health` garante.

**Decisão.** `/health` responde `200` sempre que o processo está de pé, sem
tocar no banco. Retorna `status`, `service`, `version` e `environment`.

**Alternativas descartadas.**

- _Executar `SELECT 1` no PostgreSQL_: transformaria uma indisponibilidade do
  banco em "aplicação morta", fazendo o orquestrador reiniciar o contêiner da
  API sem motivo — o problema estaria no banco.

**Consequências.** O healthcheck do Docker é confiável e a CI não precisa de um
PostgreSQL para testar o endpoint. Quando houver dependências que justifiquem,
um `GET /ready` separado será adicionado (Sprint 3 ou posterior).

---

## ADR-003 — `/health` fora do prefixo versionado da API

**Sprint:** 0 · **Status:** Aceita

**Contexto.** Os endpoints de negócio ficarão sob `/api/v1`. `/health` é
consumido por infraestrutura (Docker, CI, orquestradores), não por clientes da
API.

**Decisão.** Manter `GET /health` na raiz. `settings.API_V1_PREFIX` já existe e
passa a ser usado pelos endpoints de negócio a partir da Sprint 1.

**Consequências.** Uma futura `/api/v2` não quebra o healthcheck da
infraestrutura, que nunca precisará ser versionado.

---

## ADR-004 — Arquitetura em camadas com injeção de dependência

**Sprint:** 0 · **Status:** Aceita

**Contexto.** A `architecture.md` define Router → Service → Repository →
Database. Era preciso materializar isso já na fundação, antes que houvesse
pressão de prazo.

**Decisão.** Cada camada é um pacote (`api/`, `services/`, `repositories/`,
`models/`, `schemas/`) e recebe suas dependências pelo sistema de `Depends` do
FastAPI, com aliases tipados centralizados em `app/api/deps.py`. Repositórios
recebem a `Session` e **nunca** abrem ou fecham transações — isso é
responsabilidade da camada de serviço.

**Consequências.** O `HealthService` já é testável sem HTTP, e a substituição de
dependências em testes é trivial via `app.dependency_overrides`. O custo é uma
estrutura que parece grande para o único endpoint da Sprint 0.

---

## ADR-005 — psycopg 3 em vez de psycopg2

**Sprint:** 0 · **Status:** Aceita

**Contexto.** SQLAlchemy 2.0 suporta ambos os drivers PostgreSQL.

**Decisão.** Usar `psycopg[binary]` (versão 3), com a URL
`postgresql+psycopg://`.

**Consequências.** Driver mantido ativamente, com suporte nativo a async caso a
aplicação migre para `AsyncSession` no futuro, e wheels binárias que dispensam
toolchain de compilação na imagem Docker. A URL de conexão **precisa** do
sufixo `+psycopg` — sem ele o SQLAlchemy tenta usar psycopg2.

---

## ADR-006 — Convenção de nomes explícita no `MetaData`

**Sprint:** 0 · **Status:** Aceita

**Contexto.** Sem convenção de nomes, o PostgreSQL gera nomes automáticos para
índices e constraints. O Alembic não consegue referenciá-los de forma
determinística e os `downgrade()` quebram.

**Decisão.** Definir `NAMING_CONVENTION` em `app/db/base.py`, aplicada ao
`MetaData` da `Base` declarativa.

**Consequências.** Migrations reversíveis desde a primeira revisão. A convenção
precisa ser fixada **antes** da primeira migration — mudá-la depois exige
renomear constraints já existentes no banco.

---

## ADR-007 — Alembic resolve a URL de conexão em tempo de execução

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O `alembic.ini` normalmente carrega `sqlalchemy.url` fixo, o que
duplica configuração e coloca credenciais em arquivo versionado.

**Decisão.** Deixar `sqlalchemy.url` vazio no `alembic.ini` e preenchê-lo em
`migrations/env.py` a partir de `app.core.config.settings`.

**Consequências.** Migrations e runtime apontam sempre para o mesmo banco, e
nenhuma credencial é versionada. O `env.py` passa a depender do pacote `app`,
então os comandos do Alembic precisam ser executados a partir de `backend/`
(garantido por `prepend_sys_path = .` no `alembic.ini`).

---

## ADR-008 — Tailwind CSS v4 com o plugin oficial do Vite

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O Tailwind v4 substituiu a configuração em `tailwind.config.js`
por configuração em CSS (`@theme`) e oferece um plugin nativo para o Vite.

**Decisão.** Usar `@tailwindcss/vite` e declarar os tokens em
`src/styles/index.css`.

**Alternativas descartadas.**

- _Tailwind v3_: estável e mais documentado, mas nasceria legado e exigiria
  migração antes do Design System da Sprint 2.

**Consequências.** Sem PostCSS na cadeia de build e build mais rápido. Na
Sprint 0 apenas quatro tokens de cor foram definidos — o suficiente para a
página temporária renderizar em dark mode. A paleta completa e os componentes
chegam na Sprint 2, respeitando o escopo desta sprint.

---

## ADR-009 — Verificações de qualidade duplicadas em CI e localmente

**Sprint:** 0 · **Status:** Aceita

**Contexto.** Era preciso decidir se lint/tipos/testes rodariam via hooks de
pré-commit, apenas na CI, ou em ambos.

**Decisão.** A CI é a fonte da verdade (`.github/workflows/ci.yml`), com os
mesmos comandos disponíveis como scripts locais (`uv run ...` e `npm run ...`).
Nenhuma ferramenta de pré-commit foi adicionada na Sprint 0.

**Alternativas descartadas.**

- _`pre-commit` + `husky`/`lint-staged`_: reduziria o ciclo de feedback, mas
  adiciona duas ferramentas e dois arquivos de configuração a um projeto que
  ainda não tem código de negócio. Reavaliar na Sprint 2.

**Consequências.** Configuração mais enxuta agora; feedback de lint um pouco
mais lento até a CI rodar.

---

## ADR-010 — MyPy em modo `strict` e TypeScript em `strictTypeChecked`

**Sprint:** 0 · **Status:** Aceita

**Contexto.** "Tipagem forte" é um princípio declarado na `architecture.md`.
Regras estritas são baratas de adotar em um projeto vazio e caras depois.

**Decisão.** MyPy com `strict = true` e `warn_unreachable`; ESLint com
`strictTypeChecked` + `stylisticTypeChecked` do typescript-eslint; `tsconfig`
com `noUncheckedIndexedAccess` e `exactOptionalPropertyTypes`.

**Consequências.** Erros de tipo aparecem no momento em que o código é escrito.
Já na Sprint 0 isso pegou um caso real: `VITE_API_URL` estava declarada como
`string` obrigatória, mas o fallback em `lib/env.ts` provava que ela é
opcional — a declaração foi corrigida para `string | undefined`.

---

## ADR-011 — `httpx2` no lugar de `httpx` para o `TestClient`

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O Starlette 1.3 emite `StarletteDeprecationWarning` ao usar o
`TestClient` com `httpx` 0.x. Como o Pytest está configurado com
`filterwarnings = ["error"]`, o aviso quebrava a coleta dos testes.

**Decisão.** Usar `httpx2` no grupo de dependências de desenvolvimento.

**Alternativas descartadas.**

- _Silenciar o aviso via `filterwarnings`_: esconderia uma incompatibilidade
  real que voltaria a aparecer na próxima atualização do Starlette.

**Consequências.** A suíte roda sem avisos suprimidos. `filterwarnings =
["error"]` permanece ativo, garantindo que depreciações futuras apareçam como
falha de teste em vez de passarem despercebidas.

---

## ADR-012 — Pytest com `--import-mode=importlib`

**Sprint:** 0 · **Status:** Aceita

**Contexto.** `backend/tests/` e `etl/tests/` compartilham o mesmo `rootdir`. No
modo de importação padrão do Pytest, dois diretórios de mesmo nome colidem
(`ModuleNotFoundError: No module named 'tests.test_structure'`).

**Decisão.** Usar `--import-mode=importlib` com `consider_namespace_packages` e
**não** criar `__init__.py` nos diretórios de teste.

**Alternativas descartadas.**

- _Renomear um dos diretórios_ (ex.: `etl/tests_etl/`): resolveria a colisão às
  custas de uma inconsistência permanente na estrutura do projeto.

**Consequências.** Uma única suíte cobre backend e ETL a partir da raiz. Novos
diretórios de teste não devem receber `__init__.py`.

---

## ADR-013 — Um único `.env` na raiz do repositório

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O Docker Compose lê o `.env` da raiz; o Pydantic Settings lê, por
padrão, o `.env` do diretório de trabalho — que é `backend/` ao rodar o Uvicorn
localmente. Isso levaria a dois arquivos com as mesmas credenciais.

**Decisão.** `Settings.model_config` aponta para
`(REPO_ROOT / ".env", ".env")`: o arquivo da raiz é o padrão e um `.env` local
sobrescreve, se existir. Ambos são opcionais — em contêiner as variáveis chegam
pelo ambiente.

**Consequências.** Uma única fonte de configuração para toda a stack. O cálculo
de `REPO_ROOT` depende da profundidade de `app/core/config.py` na árvore; mover
esse arquivo exige ajustar o índice de `parents[...]`.

---

## ADR-014 — Dockerfiles multi-stage com alvos `development` e `production`

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O ambiente de desenvolvimento precisa de hot reload e ferramentas
de teste; a imagem de produção deve ser mínima e rodar sem privilégios.

**Decisão.** Um Dockerfile por serviço, com estágios `deps` → `development` e
`deps` → `production`. O Compose usa `target: development`; a CI constrói
`target: production`. O backend em produção roda como usuário não-root e o
frontend é servido por Nginx com fallback de SPA.

**Consequências.** As duas variantes compartilham a camada `deps`, o que
mantém o cache eficiente. Ambos os Dockerfiles usam a **raiz do repositório**
como contexto de build — o do backend por causa do workspace do uv (ADR-001), o
do frontend para copiar `docker/nginx.conf`.

---

## ADR-015 — `CORS_ORIGINS` com `NoDecode` e validador próprio

**Sprint:** 0 · **Status:** Aceita

**Contexto.** O Pydantic Settings tenta decodificar campos de tipo complexo
(como `list[str]`) **como JSON antes** de executar validadores `mode="before"`.
Com `CORS_ORIGINS=http://localhost:5173` no `.env`, o parse JSON falhava e a
aplicação morria no startup com `SettingsError` — problema detectado ao subir a
stack no Docker Compose.

**Decisão.** Anotar o campo como `Annotated[list[str], NoDecode]`, desligando o
parse automático, e aceitar os dois formatos no validador: lista JSON (quando a
string começa com `[`) ou valores separados por vírgula.

**Alternativas descartadas.**

- _Exigir JSON no `.env`_ (`CORS_ORIGINS='["http://localhost:5173"]'`): sintaxe
  hostil em `.env` e no `docker-compose.yml`, e fácil de errar.
- _Declarar o campo como `str` e expor uma property com a lista_: funcionaria,
  mas perderia a validação de tipo do próprio campo.

**Consequências.** Ambos os formatos funcionam, cobertos por testes de
regressão em `backend/tests/test_config.py`.

---

## ADR-016 — Credenciais como `SecretStr` e URL de conexão como `@property`

**Sprint:** 0 · **Status:** Aceita

**Contexto.** `sqlalchemy_database_uri` era um `@computed_field`, o que o
incluía em `model_dump()`. Qualquer serialização das settings — um log de
diagnóstico, um endpoint de debug — exporia a senha do banco em texto puro.

**Decisão.** `POSTGRES_PASSWORD` e `DATABASE_URL` são `SecretStr`;
`sqlalchemy_database_uri` e `is_production` são `@property` comuns, e não
campos computados.

**Consequências.** Nenhuma credencial aparece em `repr()` nem em
`model_dump()`, o que é verificado por teste. O acesso ao valor real exige
`.get_secret_value()` explícito — um ponto único e auditável no código.

---

## ADR-017 — Polling do watcher do Vite condicionado ao ambiente

**Sprint:** 0 · **Status:** Aceita

**Contexto.** Bind mounts do Docker não propagam eventos de filesystem, então o
HMR do Vite só funciona no contêiner com polling ativado. Deixar
`watch.usePolling` sempre ligado, porém, faz o watcher varrer o disco em
intervalos fixos também no desenvolvimento nativo, consumindo CPU sem ganho.

**Decisão.** O `vite.config.ts` ativa o polling apenas quando
`CHOKIDAR_USEPOLLING=true`, variável definida pelo serviço `frontend` no
`docker-compose.yml`.

**Consequências.** HMR funciona nos dois modos, sem custo desnecessário fora do
Docker. Quem rodar o frontend em outro ambiente com bind mount precisa definir a
variável manualmente (documentado em [setup.md](setup.md)).
