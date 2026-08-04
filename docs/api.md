# MarketPulse — API Reference

Referência dos endpoints disponíveis após a Sprint 3 (File Import). A
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

## Uploads

Todos os endpoints exigem `Authorization: Bearer <access_token>`. Nenhum
processamento acontece nesta sprint — os arquivos só são armazenados (ver
[roadmap.md](roadmap.md), Sprint 3).

### `POST /api/v1/uploads`

Envia um arquivo (`multipart/form-data`, campo `file`). Aceita apenas CSV e
XLSX, validados por extensão **e** Content-Type; tamanho máximo configurável
via `MAX_UPLOAD_SIZE_BYTES` (padrão 10 MiB).

**Requisição:**

```bash
curl -X POST http://localhost:8000/api/v1/uploads \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@relatorio.csv;type=text/csv"
```

**Resposta `201`:**

```json
{
  "id": "1a165602-feb3-4001-8336-0fce06f8b59d",
  "original_filename": "relatorio.csv",
  "file_size": 31,
  "mime_type": "text/csv",
  "status": "uploaded",
  "uploaded_at": "2026-07-31T01:33:54.163129Z"
}
```

`status` é sempre `"uploaded"` nesta sprint — os demais valores
(`queued`/`processing`/`processed`/`failed`) existem para o motor ETL da
Sprint 4, que passa a transicioná-los.

**Erros:**

| Status | Situação                                                        |
| ------ | ------------------------------------------------------------------ |
| `401`  | Sem token de acesso válido.                                        |
| `413`  | Arquivo maior que `MAX_UPLOAD_SIZE_BYTES`.                          |
| `415`  | Extensão diferente de `.csv`/`.xlsx`, ou Content-Type incompatível. |
| `422`  | Arquivo sem nome ou vazio.                                          |

---

### `GET /api/v1/uploads`

Lista os uploads do usuário autenticado, do mais recente para o mais antigo.
Sem paginação nesta sprint (ver decisions.md) — busca e ordenação por outros
critérios acontecem no cliente.

**Resposta `200`:**

```json
[
  {
    "id": "1a165602-feb3-4001-8336-0fce06f8b59d",
    "original_filename": "relatorio.csv",
    "file_size": 31,
    "mime_type": "text/csv",
    "status": "uploaded",
    "uploaded_at": "2026-07-31T01:33:54.163129Z"
  }
]
```

---

### `GET /api/v1/uploads/{id}`

Detalhes de um upload do usuário autenticado. Mesmo formato de resposta do
`POST /uploads`.

**Erros:**

| Status | Situação                                                    |
| ------ | ---------------------------------------------------------------- |
| `404`  | Upload inexistente **ou pertencente a outro usuário** (nunca `403` — não revela a quem o `id` pertence). |

---

### `DELETE /api/v1/uploads/{id}`

Remove o arquivo em disco e o registro. **Resposta:** `204 No Content`.

**Erros:**

| Status | Situação                                                    |
| ------ | ---------------------------------------------------------------- |
| `404`  | Upload inexistente ou pertencente a outro usuário.                |

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
