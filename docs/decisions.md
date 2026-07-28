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
