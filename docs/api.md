# MarketPulse — API Reference

Referência dos endpoints disponíveis após a Sprint 5 (Analytics Dashboard). A
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

Todos os endpoints exigem `Authorization: Bearer <access_token>`.

### `POST /api/v1/uploads`

Envia um arquivo (`multipart/form-data`, campo `file`). Aceita apenas CSV e
XLSX, validados por extensão **e** Content-Type; tamanho máximo configurável
via `MAX_UPLOAD_SIZE_BYTES` (padrão 10 MiB). **Não processa o arquivo** —
isso é feito por `POST /uploads/{id}/process`, abaixo.

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
  "error_message": null,
  "started_at": null,
  "finished_at": null,
  "uploaded_at": "2026-07-31T01:33:54.163129Z"
}
```

`status` nasce sempre `"uploaded"`. `queued` existe no enum mas não é usado
nesta sprint — o processamento é síncrono, sem fila real (ver
[decisions.md](decisions.md)). `error_message`/`started_at`/`finished_at`
só são preenchidos depois de `POST /uploads/{id}/process`.

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

**Resposta `200`:** array no mesmo formato de `POST /uploads`.

---

### `GET /api/v1/uploads/{id}`

Detalhes de um upload do usuário autenticado. Mesmo formato de resposta do
`POST /uploads`.

**Erros:**

| Status | Situação                                                    |
| ------ | ---------------------------------------------------------------- |
| `404`  | Upload inexistente **ou pertencente a outro usuário** (nunca `403` — não revela a quem o `id` pertence). |

---

### `POST /api/v1/uploads/{id}/process`

Dispara o processamento ETL do upload: detecta o marketplace de origem,
extrai, transforma e persiste os dados em `OrderItem`. **Síncrono nesta
sprint** — a resposta só chega depois que o processamento termina, com
`status` já resolvido para `processed` ou `failed`.

**Requisição:**

```bash
curl -X POST http://localhost:8000/api/v1/uploads/1a165602-feb3-4001-8336-0fce06f8b59d/process \
  -H "Authorization: Bearer <access_token>"
```

**Resposta `200` (sucesso):**

```json
{
  "id": "1a165602-feb3-4001-8336-0fce06f8b59d",
  "original_filename": "relatorio.csv",
  "file_size": 31,
  "mime_type": "text/csv",
  "status": "processed",
  "error_message": null,
  "started_at": "2026-08-05T19:18:16.868523Z",
  "finished_at": "2026-08-05T19:18:16.935008Z",
  "uploaded_at": "2026-07-31T01:33:54.163129Z"
}
```

**Resposta `200` (falha de processamento):** uma falha de processamento —
marketplace não reconhecido, arquivo ilegível, dado inválido após a
transformação — **não é um erro HTTP**. A requisição em si teve sucesso; o
resultado é que o arquivo não pôde ser processado, refletido em `status` e
`error_message`:

```json
{
  "id": "1a165602-feb3-4001-8336-0fce06f8b59d",
  "status": "failed",
  "error_message": "Não foi possível identificar o marketplace de origem a partir dos cabeçalhos do arquivo. Verifique se o arquivo corresponde a um formato suportado (Shopee ou Mercado Livre).",
  "started_at": "2026-08-05T19:18:32.342649Z",
  "finished_at": "2026-08-05T19:18:32.352294Z",
  "...": "..."
}
```

Reprocessar um upload já `processed` (chamar de novo) é **idempotente**: os
itens da tentativa anterior são substituídos, não duplicados.

**Erros (de requisição, não de processamento):**

| Status | Situação                                                    |
| ------ | ---------------------------------------------------------------- |
| `401`  | Sem token de acesso válido.                                       |
| `404`  | Upload inexistente ou pertencente a outro usuário.                |

---

### `DELETE /api/v1/uploads/{id}`

Remove o arquivo em disco e o registro — em cascata, remove também os
`OrderItem` gerados por um processamento anterior. **Resposta:**
`204 No Content`.

**Erros:**

| Status | Situação                                                    |
| ------ | ---------------------------------------------------------------- |
| `404`  | Upload inexistente ou pertencente a outro usuário.                |

---

## Analytics

Todos os endpoints exigem `Authorization: Bearer <access_token>` e
respondem apenas com dados do usuário autenticado — o `user_id` nunca vem
do cliente. Todos aceitam os mesmos três filtros opcionais via query string:

| Parâmetro     | Tipo                                             | Descrição                            |
| ------------- | ------------------------------------------------- | ------------------------------------- |
| `from`        | data ISO (`aaaa-mm-dd`)                            | Início do período (inclusivo).        |
| `to`          | data ISO (`aaaa-mm-dd`)                            | Fim do período (inclusivo).           |
| `marketplace` | `shopee` \| `mercado_livre` \| `amazon` \| `magalu` | Filtra por marketplace de origem.     |

Sem `from`/`to`, considera todo o histórico do usuário. `from` posterior a
`to` responde `422`. Um `marketplace` fora do enum responde `422`
automaticamente (validação do Pydantic).

**"Pedido" em qualquer resposta abaixo é sempre `COUNT(DISTINCT
external_order_id)`, nunca a contagem de `OrderItem`** — um pedido com três
produtos gera três `OrderItem`, mas conta como um pedido só. Exceto em
`orders-by-status`, todo endpoint considera **apenas** `OrderItem` com
`status = "completed"` — ver
[ADR-062](decisions.md#adr-062--kpis-de-analytics-consideram-somente-orderitem-com-status-completed).

### `GET /api/v1/analytics/overview`

Os quatro KPIs principais do Dashboard.

**Requisição:**

```bash
curl "http://localhost:8000/api/v1/analytics/overview?from=2026-07-01&to=2026-07-31&marketplace=shopee" \
  -H "Authorization: Bearer <access_token>"
```

**Resposta `200`:**

```json
{
  "revenue": 10697.0,
  "orders": 63,
  "average_order_value": 169.79,
  "active_products": 5,
  "has_data": true
}
```

| Campo                 | Cálculo                                                                 |
| ---------------------- | ------------------------------------------------------------------------ |
| `revenue`              | Soma de `total_price_cents / 100` dos itens `completed`.                 |
| `orders`                | Pedidos distintos `completed`.                                           |
| `average_order_value`   | `revenue / orders`; `0` se `orders` for `0` (nunca divide por zero).     |
| `active_products`       | SKUs distintos entre os itens `completed`.                               |
| `has_data`               | `true` se o usuário tem **qualquer** `OrderItem`, ignorando filtro e status — distingue "nunca importei nada" de "esse filtro não bateu com nada" (ver [ADR-063](decisions.md#adr-063--campo-has_data-para-distinguir-sem-dados-de-filtro-sem-resultado)). |

---

### `GET /api/v1/analytics/sales-over-time`

Faturamento e pedidos `completed`, agregados por dia — a agregação acontece
inteiramente no PostgreSQL (`GROUP BY order_date`); nenhum `OrderItem` é
enviado ao cliente para ele calcular.

**Resposta `200`:**

```json
[
  { "date": "2026-07-13", "revenue": 1344.0, "orders": 8 },
  { "date": "2026-07-14", "revenue": 939.0, "orders": 6 }
]
```

Dias sem nenhum item `completed` simplesmente não aparecem na lista (não são
preenchidos com zero).

---

### `GET /api/v1/analytics/orders-by-status`

Distribuição de pedidos entre **todos** os status canônicos — o único
endpoint de Analytics que não filtra por `completed` (é o próprio propósito
dele). Assume um status por pedido (todos os itens de um mesmo pedido
compartilham o status) — ver
[ADR-064](decisions.md#adr-064--orders-by-status-assume-um-status-por-pedido).

**Resposta `200`:**

```json
[
  { "status": "completed", "count": 63, "percentage": 26.4 },
  { "status": "cancelled", "count": 77, "percentage": 32.2 },
  { "status": "pending", "count": 83, "percentage": 34.7 },
  { "status": "unknown", "count": 16, "percentage": 6.7 }
]
```

Só aparecem status com pelo menos um pedido; `refunded` não aparece na
resposta acima porque não houve nenhum.

---

### `GET /api/v1/analytics/top-products`

Produtos com maior faturamento, já ordenados e limitados pelo backend.

**Parâmetro adicional:** `limit` (padrão `10`, mínimo `1`, máximo `50`).

**Resposta `200`:**

```json
[
  {
    "product_name": "1Banqueta alta com encosto. suporta até 200Kg",
    "sku": "AUTO-1BANQUETAALTACOMENCOSTOSUPORTAATE200KG",
    "quantity": 49,
    "revenue": 8137.0,
    "orders": 49
  }
]
```

**Erros comuns aos quatro endpoints:**

| Status | Situação                                              |
| ------ | -------------------------------------------------------- |
| `401`  | Sem token de acesso válido.                               |
| `422`  | `from` posterior a `to`, `marketplace` inválido, ou `limit` fora de 1–50 (só `top-products`). |

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
