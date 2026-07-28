# MarketPulse — API Reference

Referência dos endpoints disponíveis após a Sprint 1 (Authentication). A
documentação interativa (Swagger) fica em `/docs` fora do ambiente de
produção — ver [ADR-003](decisions.md#adr-003--health-fora-do-prefixo-versionado-da-api).

---

## Convenções

- **Base URL:** `http://localhost:8000` em desenvolvimento.
- **Prefixo versionado:** todo endpoint de negócio fica sob `/api/v1`. `GET /health` é a exceção — é uma sonda de infraestrutura, não um recurso da API.
- **Formato:** JSON em todas as requisições e respostas (`Content-Type: application/json`).
- **Autenticação:** `Authorization: Bearer <access_token>` nas rotas protegidas.
- **Erros de domínio** (409, 401, 403): `{"detail": "mensagem legível"}`.
- **Erros de validação** (422): formato padrão do Pydantic —
  `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.

---

## `GET /health`

Sonda de *liveness*. Não consulta o banco de dados — ver
[ADR-002](decisions.md#adr-002--get-health-é-liveness-não-readiness).

**Resposta `200`:**

```json
{
  "status": "ok",
  "service": "MarketPulse API",
  "version": "0.1.0",
  "environment": "local"
}
```

---

## Autenticação

### `POST /api/v1/auth/register`

Cria uma nova conta. **Não** retorna tokens — é preciso fazer login em seguida
(o frontend automatiza isso, ver [architecture.md](architecture.md#autenticação-frontend)).

**Corpo da requisição:**

```json
{
  "email": "user@example.com",
  "password": "Sup3rSecret!"
}
```

| Campo      | Regra                                                                 |
| ---------- | ---------------------------------------------------------------------- |
| `email`    | Formato de e-mail válido; normalizado para minúsculas.                 |
| `password` | 8–72 bytes UTF-8; ao menos uma minúscula, uma maiúscula e um dígito.    |

**Resposta `201`:**

```json
{
  "id": "20502cb2-923b-4f3c-a419-0cd43301b2d4",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2026-07-28T17:32:57.641549Z"
}
```

**Erros:**

| Status | Situação                                    |
| ------ | -------------------------------------------- |
| `409`  | Já existe uma conta com esse e-mail.          |
| `422`  | E-mail inválido ou senha fora da política.    |

---

### `POST /api/v1/auth/login`

Autentica e emite um novo par de tokens.

**Corpo da requisição:**

```json
{ "email": "user@example.com", "password": "Sup3rSecret!" }
```

**Resposta `200`:**

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "wArZ9ifou22s2O0VrbUGsjR1RdLQKMXtNeyo74JxwkY",
  "token_type": "bearer",
  "expires_in": 900
}
```

| Campo           | Descrição                                                      |
| --------------- | ---------------------------------------------------------------- |
| `access_token`  | JWT (HS256), válido por `ACCESS_TOKEN_EXPIRE_MINUTES` (15 min).   |
| `refresh_token` | String opaca, válida por `REFRESH_TOKEN_EXPIRE_DAYS` (7 dias).    |
| `expires_in`    | Segundos até o `access_token` expirar.                            |

**Erros:**

| Status | Situação                                    |
| ------ | -------------------------------------------- |
| `401`  | E-mail não cadastrado ou senha incorreta.     |
| `403`  | Conta existe, mas está desativada.            |

---

### `POST /api/v1/auth/refresh`

Troca um refresh token válido por um par de tokens novo. **O token informado é
sempre revogado** — cada refresh token só pode ser usado uma vez (rotação; ver
[ADR-018](decisions.md#adr-018--refresh-token-opaco-e-revogável-em-vez-de-jwt-stateless)).

**Corpo da requisição:**

```json
{ "refresh_token": "wArZ9ifou22s2O0VrbUGsjR1RdLQKMXtNeyo74JxwkY" }
```

**Resposta `200`:** mesmo formato de `/auth/login`.

**Erros:**

| Status | Situação                                              |
| ------ | -------------------------------------------------------- |
| `401`  | Token inexistente, já revogado, expirado ou reutilizado.  |
| `403`  | A conta associada ao token foi desativada.                |

---

### `POST /api/v1/auth/logout`

Revoga um refresh token. **Idempotente**: um token desconhecido ou já revogado
ainda responde `204` — o objetivo (token não utilizável) já está satisfeito.

**Corpo da requisição:**

```json
{ "refresh_token": "wArZ9ifou22s2O0VrbUGsjR1RdLQKMXtNeyo74JxwkY" }
```

**Resposta:** `204 No Content`.

---

### `GET /api/v1/users/me`

Retorna os dados do usuário autenticado. Requer
`Authorization: Bearer <access_token>`.

**Resposta `200`:**

```json
{
  "id": "20502cb2-923b-4f3c-a419-0cd43301b2d4",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2026-07-28T17:32:57.641549Z"
}
```

**Erros:**

| Status | Situação                                                          |
| ------ | -------------------------------------------------------------------- |
| `401`  | Header ausente, token malformado, expirado, ou de tipo errado (ex.: um refresh token usado como access token). |
| `403`  | A conta associada ao token foi desativada.                            |

---

## Fluxo completo (cliente)

```text
1. POST /auth/register        → cria a conta
2. POST /auth/login           → access_token + refresh_token
3. GET  /users/me             → (Authorization: Bearer access_token)
   ... access_token expira em 15 min ...
4. POST /auth/refresh         → novo par de tokens (o antigo refresh_token é revogado)
5. POST /auth/logout          → revoga o refresh_token atual
```

O frontend automatiza os passos 2–4: ao carregar a aplicação, tenta renovar a
sessão a partir do refresh token salvo (`localStorage`); a cada 401 numa
chamada autenticada, tenta uma renovação silenciosa antes de encerrar a sessão
(ver `frontend/src/lib/apiClient.ts`).
