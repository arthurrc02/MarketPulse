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
um `GET /ready` separado será adicionado quando houver uma dependência real
a checar (ver [roadmap.md](roadmap.md) — não fez parte do escopo da Sprint 3).

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

---

## ADR-018 — Refresh token opaco e revogável em vez de JWT stateless

**Sprint:** 1 · **Status:** Aceita

**Contexto.** Um refresh token poderia ser mais um JWT assinado, validado só
pela assinatura (stateless). Isso é simples, mas torna "logout" um teatro: o
token continua criptograficamente válido até expirar, mesmo depois de o
usuário clicar em "Sair".

**Decisão.** O refresh token é uma string aleatória opaca
(`secrets.token_urlsafe(32)`), sem nenhum dado embutido. O servidor guarda
apenas o **hash SHA-256** dela na tabela `refresh_tokens`, junto de
`user_id`, `expires_at` e `revoked_at`. Cada uso rotaciona o token: o antigo é
revogado e um novo é emitido (`AuthService.refresh`), então um refresh token
só serve uma vez — reuso é tratado como sessão inválida.

**Alternativas descartadas.**

- _Refresh token como JWT de longa duração_: mais simples de implementar, mas
  sem revogação real — um "logout" não encerraria nada no servidor.
- _Blocklist de JWTs revogados_: alcançaria o mesmo efeito, mas exige guardar
  uma entrada por token revogado *indefinidamente* (até a expiração natural do
  JWT), enquanto o modelo opaco só guarda tokens *ativos* — o próprio
  `expires_at` limita o crescimento da tabela.

**Consequências.** O access token continua sendo um JWT stateless (rápido de
validar, sem consulta ao banco); só o refresh token toca o banco, e apenas na
troca de sessão (a cada ~15 min, não a cada requisição). SHA-256 (não bcrypt)
é usado para o hash — o valor já é aleatório de alta entropia, não uma senha
escolhida por humano, então não há necessidade de um hash lento.

---

## ADR-019 — Suíte de testes com SQLite por padrão, PostgreSQL real na CI

**Sprint:** 1 · **Status:** Aceita

**Contexto.** O roadmap da Sprint 0 já previa "testes de integração com banco
de teste" e "CI sobe um serviço PostgreSQL". Exigir Postgres rodando para
`uv run pytest` funcionar localmente adicionaria fricção ao ciclo de
desenvolvimento (é preciso ter Docker de pé só para rodar testes).

**Decisão.** `backend/tests/conftest.py` usa SQLite em memória por padrão,
criando o schema do zero a cada teste (`Base.metadata.create_all`/`drop_all`).
Definir `TEST_DATABASE_URL` troca o backend para o banco apontado — é
exatamente o que a CI faz, apontando para o serviço `postgres` do workflow.
A suíte inteira (52 testes) roda sem alteração de código contra os dois
bancos.

**Alternativas descartadas.**

- _Só SQLite, sempre_: mais rápido, mas esconderia incompatibilidades de
  dialeto — foi exatamente isso que expôs o bug do ADR-025 abaixo.
- _Só PostgreSQL, sempre_: mais fiel à produção, mas exige Docker de pé para
  qualquer `pytest` local, inclusive para editar um único teste.

**Consequências.** A CI (`.github/workflows/ci.yml`) roda lint/tipos/testes
**e** `alembic upgrade head` / `downgrade base` / `upgrade head` contra um
Postgres 16 real de serviço, validando tanto a suíte quanto a migration no
dialeto de produção. Isso só funciona porque os models não usam nenhum
recurso específico do PostgreSQL (JSONB, arrays, etc.) — se isso mudar no
futuro, os testes que dependem desses recursos precisarão exigir
`TEST_DATABASE_URL` explicitamente.

---

## ADR-020 — `bcrypt` direto no lugar de `passlib[bcrypt]`

**Sprint:** 1 · **Status:** Aceita

**Contexto.** `architecture.md` previa "Passlib/Bcrypt". Ao testar essa
combinação, `passlib==1.7.4` (última versão, projeto em modo de manutenção)
quebra com `bcrypt>=4.1`: `AttributeError: module 'bcrypt' has no attribute
'__about__'`, um problema de compatibilidade conhecido e nunca corrigido no
passlib.

**Decisão.** Usar a biblioteca `bcrypt` diretamente
(`bcrypt.hashpw`/`bcrypt.checkpw` em `app/core/security.py`), sem a camada do
passlib.

**Alternativas descartadas.**

- _Fixar `bcrypt<4.1`_: resolveria o sintoma, mas fixaria uma versão cada vez
  mais antiga de uma dependência de segurança, sem correção à vista do lado
  do passlib.

**Consequências.** Uma linha a menos de abstração e uma dependência a menos.
O código explicitamente trunca a senha em 72 bytes antes de verificar
(`_BCRYPT_MAX_PASSWORD_BYTES`), replicando a única validação que o passlib
fazia por baixo dos panos. O schema `UserCreate` já rejeita senhas acima
desse limite (ver ADR-024), então esse truncamento nunca deveria disparar na
prática — é uma segunda camada de defesa, não o mecanismo principal.

---

## ADR-021 — `HTTPBearer(auto_error=False)` para responder 401 e não 403

**Sprint:** 1 · **Status:** Aceita

**Contexto.** O padrão do FastAPI para `HTTPBearer()` (`auto_error=True`)
responde **403 Forbidden** quando o header `Authorization` está ausente — um
comportamento historicamente questionado do Starlette/FastAPI. Semanticamente,
"não autenticado" é 401; 403 deveria significar "autenticado, mas sem
permissão".

**Decisão.** `_bearer_scheme = HTTPBearer(auto_error=False)`; quando
`credentials` vem `None`, `get_current_user` levanta explicitamente
`InvalidTokenError` (401, com `WWW-Authenticate: Bearer` implícito no
exception handler).

**Consequências.** Toda ausência ou invalidade de token responde 401,
uniformemente — inclusive testado (`test_me_fails_without_a_token`).

---

## ADR-022 — Cadastro não retorna tokens; frontend faz login automaticamente

**Sprint:** 1 · **Status:** Aceita

**Contexto.** Era preciso decidir se `POST /auth/register` autentica o
usuário imediatamente (retornando tokens) ou apenas cria o recurso.

**Decisão.** `/auth/register` retorna `201` com o `UserRead` criado — sem
tokens. O `AuthContext.register()` do frontend chama `login()` com as mesmas
credenciais logo em seguida, então o usuário só percebe uma "conta criada e já
logada" (ver `docs/api.md`).

**Alternativas descartadas.**

- _Registro retorna tokens diretamente_: uma chamada a menos, mas mistura duas
  responsabilidades num único endpoint (criar recurso vs. iniciar sessão) e
  duplicaria a lógica de emissão de tokens entre `register` e `login` no
  service.

**Consequências.** `AuthService.register` fica simples (só cria o usuário);
toda a lógica de emissão de tokens vive em um único lugar
(`AuthService._issue_tokens`, chamado por `authenticate` e `refresh`).

---

## ADR-023 — Sessão do frontend: access token em memória, refresh token em `localStorage`

**Sprint:** 1 · **Status:** Aceita

**Contexto.** "Permanecer autenticado" exige sobreviver a um F5. Guardar o
access token em `localStorage` é a forma mais simples, mas amplia a janela de
exposição a um roubo via XSS (qualquer script injetado pode lê-lo).

**Decisão.** O access token vive só em memória (`lib/auth/tokenStore.ts`,
variável de módulo) — nunca é persistido. O refresh token vai para
`localStorage` (é o único jeito de sobreviver a um reload). Ao carregar a
aplicação, `AuthProvider` troca o refresh token salvo por um access token novo
(`hydrateFromStoredRefreshToken`); a cada 401 numa chamada autenticada,
`apiClient` tenta uma única renovação silenciosa antes de desistir.

**Alternativas descartadas.**

- _Cookies httpOnly para os dois tokens_: mais seguro contra XSS, mas exige
  que o backend defina/leia cookies (CORS com credentials, CSRF token,
  `SameSite`), passando de um problema de frontend para um de contrato
  full-stack. Fica como melhoria futura (ver seção de melhorias no
  relatório da sprint).

**Consequências.** Um XSS bem-sucedido rouba, na pior hipótese, um access
token de 15 minutos — não os 7 dias do refresh token. O preço é a
complexidade do "silent refresh" (bootstrap + retry em 401), testada em
`AuthContext.test.tsx`.

---

## ADR-024 — `SECRET_KEY` com mínimo de 32 bytes e bloqueio em produção

**Sprint:** 1 · **Status:** Aceita

**Contexto.** PyJWT emite `InsecureKeyLengthWarning` para chaves HMAC-SHA256
menores que 32 bytes (RFC 7518 §3.2). Como a suíte roda com
`filterwarnings = ["error"]` (ADR-011), o valor padrão inicial de
`SECRET_KEY` (30 bytes) quebrava os testes de emissão de token.

**Decisão.** `_INSECURE_DEFAULT_SECRET_KEY` tem 43 bytes. Um
`model_validator` em `Settings` recusa esse valor padrão quando
`ENVIRONMENT=production`, exigindo uma chave real via variável de ambiente.

**Consequências.** É impossível subir em produção sem definir `SECRET_KEY`
explicitamente — testado (`test_default_secret_key_is_rejected_in_production`)
e validado manualmente contra o Docker Compose (container recusa subir com a
chave padrão quando `ENVIRONMENT=production`).

---

## ADR-025 — Normalização de datetime naive/aware entre SQLite e PostgreSQL

**Sprint:** 1 · **Status:** Aceita

**Contexto.** `RefreshToken.expires_at` é `DateTime(timezone=True)`. O
PostgreSQL devolve datetimes aware; o SQLite (usado nos testes, ver ADR-019)
não preserva timezone — o valor volta *naive*. Comparar os dois formatos
(`record.expires_at < datetime.now(UTC)`) lançava
`TypeError: can't compare offset-naive and offset-aware datetimes`, mas só na
suíte local (SQLite); o mesmo código funcionaria sem erro contra Postgres.

**Decisão.** `app.core.security.ensure_aware_utc()` normaliza qualquer
datetime para aware-UTC antes de comparar, tratando `tzinfo is None` como "já
está em UTC, só faltou o marcador". `AuthService.refresh` usa essa função ao
invés de comparar `record.expires_at` diretamente.

**Consequências.** O mesmo código de comparação funciona nos dois bancos —
achado justamente porque a suíte roda contra ambos (ADR-019). Se o SQLite não
fosse usado nos testes, esse bug só apareceria much mais tarde, com dados
gravados via SQLAlchemy num cenário que por acaso perdesse o timezone.

---

## ADR-026 — `AuthContext.tsx` e a definição do contexto em arquivos separados

**Sprint:** 1 · **Status:** Aceita

**Contexto.** Duas necessidades conflitantes: (1) o ESLint
(`react-refresh/only-export-components`) recomenda que um arquivo que exporta
um componente React não exporte também um valor não-componente (como o objeto
`Context`), para o Fast Refresh funcionar corretamente; (2) nomear o arquivo
da definição `authContext.ts` (mesmo nome do componente, só com inicial
minúscula) quebrou o **TypeScript project service** do ESLint no Windows —
`AuthContext.tsx` deixou de ser encontrado, porque o filesystem é
case-insensitive e as duas identidades colidiram na camada de resolução de
projeto do `tsserver`.

**Decisão.** A definição do contexto (`AuthContext`, `AuthContextValue`,
`AuthStatus`) vive em `src/context/authContextDefinition.ts` — um nome
claramente distinto, não só por capitalização. O componente `AuthProvider`
fica em `src/context/AuthContext.tsx`, importando a definição do outro
arquivo.

**Consequências.** Zero warnings de lint, e nenhuma ambiguidade de nome de
arquivo em filesystems case-insensitive (Windows, macOS padrão). Ao criar
outros contextos React no projeto (nenhum previsto antes da Sprint 3), seguir
o mesmo padrão: nomes de arquivo que diferem por mais do que a capitalização
da primeira letra.

---

## ADR-027 — Design System com componentes próprios, sem bibliotecas de UI

**Sprint:** 2 · **Status:** Aceita

**Contexto.** Bibliotecas como shadcn/ui, Radix, Material UI ou Chakra UI
resolveriam boa parte do catálogo (Modal, Dropdown, Tabs, Tooltip) mais
rápido, com acessibilidade já testada por uma comunidade grande.

**Decisão.** Todos os 18 componentes desta sprint são implementados do zero,
usando apenas React, Tailwind CSS e Framer Motion (já previstos na stack).
Nenhuma biblioteca de componentes prontos foi adicionada.

**Alternativas descartadas.**

- _shadcn/ui_: gera código copiado para o repositório (não é uma dependência
  tradicional), o que reduziria parte do argumento de "vendor lock-in" — mas
  ainda assim o visual sairia reconhecível como "um projeto shadcn", diluindo
  a identidade visual própria que o projeto busca (inspirações da
  `design-system.md`, não cópia).
- _Radix Primitives (sem estilo) + Tailwind_: teria acelerado a acessibilidade
  de Modal/Dropdown/Tabs, mas o objetivo explícito desta sprint é demonstrar
  domínio de composição de componentes em React puro — terceirizar justamente
  essa parte anularia o propósito da sprint.

**Consequências.** Mais código escrito à mão (~20 arquivos de componente) e
responsabilidade total pela acessibilidade de cada um — testada
explicitamente (ver a suíte de 105 testes de frontend). Como contrapartida, a
UI tem identidade visual própria e cada componente é auditável e ajustável
sem lidar com a API de uma lib externa. Padrões avançados de acessibilidade
(navegação por setas em menus, colisão de tooltip) foram conscientemente
simplificados — ver ADR-030 e ADR-031.

---

## ADR-028 — Inter via Google Fonts, com fallback progressivo

**Sprint:** 2 · **Status:** Aceita

**Contexto.** As referências visuais do projeto (Linear, Vercel, Stripe) usam
tipografia geométrica moderna — a pilha padrão `system-ui` do Tailwind (San
Francisco/Segoe UI/Roboto conforme o SO) já é neutra e legível, mas não
reproduz essa identidade visual específica.

**Decisão.** `index.html` carrega Inter via `<link>` do Google Fonts
(`font-display: swap`), e `--font-sans` no `@theme` lista `'Inter'` antes da
pilha `ui-sans-serif, system-ui, ...`.

**Alternativas descartadas.**

- _Self-host da fonte (arquivo `.woff2` no repositório)_: elimina a
  dependência de rede em runtime, mas adiciona binário ao repositório e
  gestão de licença/versão manual — desproporcional para uma única família
  tipográfica nesta fase do projeto.

**Consequências.** Título e textos usam Inter quando há rede; sem rede (ou
com o carregamento ainda em andamento), o `font-display: swap` evita texto
invisível e cai educadamente para a pilha do sistema — a aplicação nunca
depende da fonte para funcionar.

---

## ADR-029 — `Select` como `<select>` nativo estilizado, não um listbox customizado

**Sprint:** 2 · **Status:** Aceita

**Contexto.** Um listbox customizado (popup próprio, `role="listbox"`,
roving tabindex, busca por digitação) dá mais controle visual sobre cada
`<option>`, mas replica uma quantidade grande de comportamento que o
`<select>` nativo já implementa corretamente — teclado, leitor de tela,
comportamento mobile (abre o seletor nativo do SO em vez de um popup web).

**Decisão.** `Select` estiliza um `<select>` nativo (borda, fundo, ícone de
chevron sobreposto) em vez de construir um listbox próprio.

**Alternativas descartadas.**

- _Listbox customizado_: mais fiel ao design em telas grandes, mas cada
  comportamento reimplementado (teclado, `aria-activedescendant`, fechamento
  em blur/Esc/clique fora) é mais uma superfície de falha de acessibilidade
  para testar e manter — desproporcional a esta sprint, que ainda não tem
  nenhum `Select` com lista longa ou busca.

**Consequências.** Acessibilidade garantida "de graça" pelo navegador; em
troca, o estilo das `<option>` individuais segue a renderização nativa do
SO/navegador (não é possível aplicar o Design System dentro do popup nativo)
— um trade-off visual aceito conscientemente, documentado aqui para não ser
"redescoberto" como bug depois.

---

## ADR-030 — `Tooltip` com posicionamento fixo, sem detecção de colisão

**Sprint:** 2 · **Status:** Aceita

**Contexto.** Um tooltip que sempre abre no mesmo lado (`top` por padrão)
pode ficar cortado pela borda da viewport em telas pequenas ou perto da
borda. Bibliotecas como Floating UI resolvem isso com detecção de colisão e
"flip" automático de lado.

**Decisão.** `Tooltip` aceita um prop `side` (`'top' | 'bottom'`) definido
pelo desenvolvedor no call site, sem detecção automática de colisão.

**Alternativas descartadas.**

- _Adicionar `@floating-ui/react`_: resolveria o problema de forma robusta,
  mas é exatamente o tipo de dependência que a sprint pediu para evitar
  (biblioteca pronta assumindo uma responsabilidade de UI) — desproporcional
  para os dois usos atuais (ícone de info em `KPICard`, item de navegação),
  ambos longe da borda da viewport.

**Consequências.** Funciona bem para os usos atuais. Se um `Tooltip` futuro
precisar aparecer perto da borda da tela, listado como melhoria futura no
relatório da sprint.

---

## ADR-031 — `Dropdown` sem navegação por setas entre itens

**Sprint:** 2 · **Status:** Aceita

**Contexto.** O padrão completo de "menu button" do WAI-ARIA prevê que, com o
menu aberto, as setas para cima/baixo movam o foco entre os itens (roving
tabindex), Home/End pulem para o primeiro/último item, e digitar uma letra
pule para o item correspondente.

**Decisão.** `Dropdown` implementa apenas fechar em Esc e em clique fora; a
navegação entre itens é feita via Tab (cada item é um `<button>` real,
focável na ordem natural do DOM).

**Alternativas descartadas.**

- _Roving tabindex completo_: mais fiel ao padrão ARIA, mas o único uso atual
  (menu de conta no `Header`, com dois itens) não justifica a complexidade —
  o ganho de usabilidade real é marginal com tão poucos itens.

**Consequências.** Uso por teclado funciona (Tab alcança os itens, Enter/Espaço
ativa), mas não segue a expectativa de "setas navegam o menu" que usuários de
leitor de tela avançados podem ter. Listado como melhoria futura — relevante
se um `Dropdown` futuro tiver uma lista longa de itens.

---

## ADR-032 — Toast é responsabilidade da página, não do `AuthContext`

**Sprint:** 2 · **Status:** Aceita

**Contexto.** Era possível disparar o toast de "login bem-sucedido" dentro de
`AuthContext.login()`, centralizando o efeito colateral junto da lógica de
autenticação.

**Decisão.** `AuthContext` permanece agnóstico de UI (como já era desde a
Sprint 1); `LoginPage`, `RegisterPage` e `Header` (logout) chamam
`useToast().showToast(...)` explicitamente, depois de `await login(...)` /
`register(...)` / `logout(...)` resolverem.

**Alternativas descartadas.**

- _Toast disparado dentro do `AuthContext`_: acoplaria a camada de estado de
  autenticação a uma decisão de apresentação (texto da mensagem, variante de
  cor) — o mesmo racional de camadas já aplicado no backend (ADR-004):
  serviço não deveria conhecer a UI que o consome.

**Consequências.** `AuthContext.test.tsx` continua testável sem
`ToastProvider` (context isolado). Cada página decide sua própria mensagem de
sucesso — nem toda chamada de `login`/`register`/`logout` precisa,
necessariamente, do mesmo texto no futuro.

---

## ADR-033 — `/app` como rota de layout aninhada (`AppLayout` + `<Outlet />`)

**Sprint:** 2 · **Status:** Aceita

**Contexto.** A Sprint 1 tinha uma única rota protegida (`/app` →
`DashboardPage`, sem layout compartilhado). Esta sprint adiciona quatro
páginas nesse mesmo espaço protegido (Uploads, Analytics, Insights,
Settings), todas precisando da mesma Sidebar e Header.

**Decisão.** `/app` passa a ser uma rota de layout: `ProtectedRoute` envolve
`AppLayout`, que renderiza `Sidebar` + `Header` + `<Outlet />`; as cinco
páginas viram rotas filhas (`index`, `uploads`, `analytics`, `insights`,
`settings`), sem repetir layout nenhum.

**Alternativas descartadas.**

- _Cada página import a própria Sidebar/Header_: duplicaria o layout em cinco
  arquivos e tornaria fácil um deles divergir visualmente com o tempo.

**Consequências.** Adicionar uma página protegida nova (Sprint 3+) é só
acrescentar uma rota filha — nenhum arquivo de layout muda. `AppLayout`
também centraliza o estado da gaveta mobile da Sidebar (fecha sozinha a cada
navegação), que seria estranho de replicar por página.

---

## ADR-034 — Armazenamento local em disco, sem S3/nuvem nesta sprint

**Sprint:** 3 · **Status:** Aceita

**Contexto.** `architecture.md` prevê armazenamento de arquivos, mas a Sprint
3 tem escopo explicitamente restrito a "guardar o arquivo" — sem
processamento. Um provedor de object storage (S3, R2, GCS) resolveria
durabilidade e escala, mas exige credenciais, um SDK e infraestrutura extra
que ainda não existem no projeto.

**Decisão.** Os arquivos são gravados em disco local, organizados por
usuário em `storage/uploads/{user_id}/{stored_filename}`, montados no
contêiner via bind mount do Docker Compose (`./storage:/app/storage`) — não
um volume nomeado, para que o conteúdo seja inspecionável diretamente do
host durante o desenvolvimento.

**Alternativas descartadas.**

- _S3 (ou compatível) desde já_: adiciona uma dependência de infraestrutura
  externa (conta, bucket, credenciais) a uma sprint que só precisa provar
  que "salvar e listar arquivos" funciona — desproporcional ao escopo atual.

**Consequências.** Nenhum arquivo enviado sobrevive a um ambiente sem disco
persistente (ex.: um PaaS com filesystem efêmero) — aceitável para
desenvolvimento e para a fase atual do projeto, mas listado como melhoria
futura para quando houver deploy real. A migração para object storage é
isolada pela abstração `FileStorage` (ver [ADR-035](#adr-035--abstração-filestorage-isolando-o-mecanismo-de-persistência)) — trocar a implementação não exige tocar em
`UploadService` nem nos routers.

---

## ADR-035 — Abstração `FileStorage` isolando o mecanismo de persistência

**Sprint:** 3 · **Status:** Aceita

**Contexto.** A Sprint 3 pediu explicitamente para preparar o terreno da
Sprint 4: o motor ETL vai precisar *ler* o conteúdo dos arquivos já
enviados, sem que a Sprint 3 tenha implementado nenhum parsing. Se
`UploadService` chamasse `Path.write_bytes()`/`open()` diretamente, o ETL
(ou uma futura migração para S3) exigiria reescrever a camada de serviço.

**Decisão.** `app/storage/base.py` define `FileStorage`, uma classe
abstrata com três métodos: `save`, `open` (retorna um `BinaryIO`, não usado
nesta sprint — existe para a Sprint 4) e `delete` (idempotente).
`LocalFileStorage` é a única implementação por ora; `UploadService` recebe a
instância via injeção de dependência (`get_upload_service` em
`app/api/deps.py`), sem conhecer o caminho em disco.

**Consequências.** A Sprint 4 pode chamar `storage.open(user_id=...,
stored_filename=...)` para ler o conteúdo de um upload existente sem
nenhuma mudança em `UploadService`, no model `Upload` ou nos endpoints. Uma
futura migração para S3 é uma nova classe `S3FileStorage` mais uma troca na
factory de `deps.py` — nenhum outro arquivo muda.

---

## ADR-036 — `stored_filename` opaco (UUID) em vez do nome original

**Sprint:** 3 · **Status:** Aceita

**Contexto.** Gravar o arquivo com o `original_filename` enviado pelo
usuário parece natural, mas expõe dois problemas: colisão de nomes entre
uploads diferentes do mesmo usuário, e path traversal se o nome não for
sanitizado com cuidado (`../../etc/passwd`, caracteres de controle, etc.).

**Decisão.** `UploadService.create_upload` gera
`stored_filename = f"{uuid.uuid4().hex}{extension}"` — só a extensão
validada do arquivo original é preservada. `original_filename` continua
guardado no banco (e devolvido pela API) só para exibição; nunca é usado
para compor um caminho em disco.

**Consequências.** Path traversal via nome de arquivo é estruturalmente
impossível — o nome gravado nunca deriva de entrada do usuário além da
extensão (já validada contra uma lista fechada). O schema `UploadRead`
deliberadamente omite `stored_filename` da resposta da API — é um detalhe
de implementação, não um contrato com o cliente.

---

## ADR-037 — `values_callable` para gravar os valores do enum, não os nomes do Python

**Sprint:** 3 · **Status:** Aceita

**Contexto.** O comportamento padrão do `sa.Enum()` do SQLAlchemy grava o
**nome** do membro Python (`"UPLOADED"`) na coluna, não o `.value`
(`"uploaded"`). A API serializa `UploadStatus` via Pydantic usando `.value`
(minúsculo, por ser um `StrEnum`) — sem correção, o valor gravado no banco
divergiria do valor devolvido pela API, e uma futura query SQL bruta do ETL
(Sprint 4) contra a coluna `status` encontraria `"UPLOADED"`, não
`"uploaded"`.

**Decisão.** A coluna `status` do model `Upload` declara
`values_callable=lambda enum_cls: [member.value for member in enum_cls]`,
forçando o SQLAlchemy a gravar `.value` em vez do nome do membro. A
migration autogerada inicialmente (`c619d3650ce0`, com valores maiúsculos)
foi descartada e regenerada (`420e360b0aa9`) já com os valores corretos.

**Consequências.** Banco e API concordam sobre o formato do status,
verificado por teste de integração e por inspeção manual do
`CHECK CONSTRAINT` gerado. Esse é exatamente o tipo de divergência que só
aparece ao ler a migration autogerada com atenção — vale conferir sempre
que um novo `Enum` for adicionado a um model.

---

## ADR-038 — `native_enum=False` no enum de status do upload

**Sprint:** 3 · **Status:** Aceita

**Contexto.** Por padrão, `sa.Enum()` cria um tipo `ENUM` nativo do
PostgreSQL. Adicionar um valor novo a um enum nativo do Postgres exige
`ALTER TYPE ... ADD VALUE` — uma operação com restrições (não pode rodar
dentro de uma transação junto de outros comandos em versões mais antigas do
Postgres) e mais cerimônia do que uma migration comum. A Sprint 4 vai
precisar transicionar `status` por `queued`/`processing`/`processed`/
`failed` — os valores já existem hoje, mas é razoável esperar refinamentos
(ex.: um status `partially_processed`) conforme o ETL amadurece.

**Decisão.** `native_enum=False` grava a coluna como `VARCHAR(20)` com um
`CHECK CONSTRAINT` listando os valores válidos, em vez de um tipo `ENUM`
nativo.

**Consequências.** Adicionar um valor novo no futuro é uma migration comum
(`ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT ...`), sem as
restrições do `ALTER TYPE` nativo. O custo é um `CHECK CONSTRAINT` levemente
menos eficiente que um tipo nativo — irrelevante no volume de dados desta
fase do projeto.

---

## ADR-039 — Leitura em chunks para validar o tamanho do upload

**Sprint:** 3 · **Status:** Aceita

**Contexto.** Validar `MAX_UPLOAD_SIZE_BYTES` exige saber o tamanho do
arquivo. Chamar `file.read()` inteiro antes de checar o tamanho carregaria
um arquivo arbitrariamente grande inteiro em memória antes de rejeitá-lo —
exatamente o cenário que a validação deveria prevenir.

**Decisão.** `_read_within_limit` (em `app/services/upload.py`) lê o
`UploadFile` em blocos de 1 MiB, somando o total lido; assim que o total
excede `max_upload_size_bytes`, a leitura para e `FileTooLargeError` é
levantada — sem nunca materializar mais que ~1 MiB acima do limite
configurado em memória de uma vez.

**Consequências.** Um upload de 500 MB com limite de 10 MiB nunca chega a
alocar 500 MB de memória — o teste de limite de tamanho
(`test_upload_rejects_file_above_size_limit`) usa um limite artificialmente
baixo (10 bytes) via `dependency_overrides` para exercitar esse caminho sem
precisar gerar um arquivo grande de verdade.

---

## ADR-040 — `chown` restrito a `/app/storage` no Dockerfile de produção

**Sprint:** 3 · **Status:** Aceita

**Contexto.** A Sprint 0 ([ADR-014](#adr-014--dockerfiles-multi-stage-com-alvos-development-e-production)) deixou `/app` pertencendo a `root` no
estágio de produção, deliberadamente, para que o processo não pudesse
alterar o próprio código em runtime. A Sprint 3 introduziu escrita real em
disco (`storage/uploads/`) — descoberto durante a validação manual do
Docker (não por um teste automatizado): rodar a imagem de produção e tentar
um upload real falhava com `PermissionError`, porque o usuário `marketpulse`
(uid 1000) não tinha permissão de escrita em nenhum subdiretório de `/app`.

**Decisão.** Adicionar `chown -R marketpulse:marketpulse /app/storage`
**depois** do `useradd`, mantendo o restante de `/app` como estava
(propriedade de `root`, leitura/execução para todos).

**Consequências.** Upload funciona em produção sem reabrir a decisão da
Sprint 0 para o resto do código-fonte — só o diretório que realmente precisa
de escrita em runtime muda de dono. Validado com um upload real via `curl`
contra um contêiner standalone no alvo `production` (não só o `development`
do Compose, que roda como root e mascararia o problema).

---

## ADR-041 — Toast e erro inline com textos distintos no upload

**Sprint:** 3 · **Status:** Aceita

**Contexto.** A primeira versão do tratamento de erro em `UploadsPage`
usava a mesma string (`error.message`, vinda da API) tanto no `Toast`
quanto no item da fila de upload — uma redundância visual (a mesma frase
aparecendo duas vezes na tela) descoberta ao escrever o teste de erro:
`findByText` passou a encontrar dois elementos com o mesmo texto.

**Decisão.** O `Toast` mostra uma mensagem curta e genérica
(`Falha ao enviar ${nome}.`); o item da fila mostra o motivo específico
vindo da API (`error.message`, ex.: "Tipo de arquivo não suportado").

**Consequências.** Nenhuma duplicação visual, e cada mensagem cumpre um
papel diferente: o toast avisa que algo falhou (efêmero, pode ser
dispensado sem ler), o item da fila explica o motivo (permanece na tela até
o usuário remover ou tentar de novo).

---

## ADR-042 — `<input type="file">` como irmão do `<button>`, não filho

**Sprint:** 3 · **Status:** Aceita

**Contexto.** A primeira versão de `FileUpload` colocava o `<input
type="file">` **dentro** do `<button>` clicável, escondido via `sr-only`. A
spec do HTML proíbe conteúdo interativo (como `<input>`) como filho de
`<button>` — um erro de HTML inválido pego na revisão de acessibilidade
pedida explicitamente pelo prompt da sprint, não por um teste automatizado
(jsdom não valida aninhamento de HTML).

**Decisão.** `<button>` e `<input>` viram irmãos dentro de um `<div
className="relative">`. O `<input>` recebe `tabIndex={-1}` e
`aria-hidden="true"` — só o `<button>` é alcançável por teclado/leitor de
tela; o clique nele dispara `inputRef.current?.click()` programaticamente.

**Consequências.** HTML válido, um único elemento focável por teclado
(evita foco duplo ao tabular pela área de upload), suíte completa
(131 testes de frontend) re-executada após a correção sem regressão.

---

## ADR-043 — `apiClient` detecta `FormData` para omitir o `Content-Type`

**Sprint:** 3 · **Status:** Aceita

**Contexto.** `buildRequestInit` (em `lib/apiClient.ts`) sempre definia
`Content-Type: application/json` e serializava o corpo com
`JSON.stringify`. Um upload de arquivo precisa de
`multipart/form-data`, cujo `boundary` só o próprio navegador consegue
gerar corretamente — definir o header manualmente (mesmo com o valor
"certo") quebra o parsing do multipart no servidor.

**Decisão.** `buildRequestInit` verifica `options.body instanceof
FormData`: se for, **não** define `Content-Type` (o navegador define
`multipart/form-data; boundary=...` sozinho) e passa o `FormData` como
corpo sem `JSON.stringify`.

**Consequências.** `createUpload` (em `lib/uploads/api.ts`) monta um
`FormData` comum e chama `apiClient` normalmente, sem nenhum tratamento
especial no call site — a distinção fica isolada dentro do próprio cliente
HTTP, reutilizável por qualquer endpoint multipart futuro.

---

## ADR-044 — `FileUpload` e `Table` continuam o Design System sem bibliotecas prontas

**Sprint:** 3 · **Status:** Aceita

**Contexto.** A restrição da Sprint 2 ([ADR-027](#adr-027--design-system-com-componentes-próprios-sem-bibliotecas-de-ui)) era, em parte,
temporária por escopo: uploads e tabelas de dados não existiam ainda. Uma
área de drag & drop e uma tabela ordenável são exatamente o tipo de
componente onde uma lib pronta (`react-dropzone`, `@tanstack/table`)
economiza tempo real.

**Decisão.** `FileUpload` e `Table` são implementados do zero, seguindo o
mesmo princípio da Sprint 2 — Design System próprio, sem bibliotecas de UI
ou de dados de terceiros.

**Alternativas descartadas.**

- _`react-dropzone`_: resolveria os handlers de drag & drop prontos, mas o
  componente resultante teria pouco código próprio — a área de upload é,
  visualmente, a peça central desta sprint.
- _`@tanstack/table`_: poderoso para tabelas complexas (paginação virtual,
  filtros compostos), mas a `UploadsPage` precisa só de ordenação por uma
  coluna — desproporcional a uma dependência nova para esse requisito.

**Consequências.** Mais duas peças auditáveis no Design System, testadas
diretamente (`FileUpload.test.tsx`, `Table.test.tsx`), sem API de terceiros
para aprender. `Table` é genérica (`Table<T>`) o bastante para ser
reaproveitada em listagens futuras (Sprint 5+) sem reescrita.
