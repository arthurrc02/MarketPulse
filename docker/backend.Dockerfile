# syntax=docker/dockerfile:1.7
#
# Imagem do backend (FastAPI). O contexto de build é a RAIZ do repositório,
# porque o backend depende do pacote `etl` via workspace do uv.

# ---------------------------------------------------------------------------
# base — runtime Python + uv
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

# ---------------------------------------------------------------------------
# deps — resolve dependências antes de copiar o código (camada cacheável)
# ---------------------------------------------------------------------------
FROM base AS deps

COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY etl/pyproject.toml etl/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace

# ---------------------------------------------------------------------------
# development — hot reload, dependências de dev incluídas
# ---------------------------------------------------------------------------
FROM deps AS development

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# production — somente dependências de runtime, processo sem privilégios
# ---------------------------------------------------------------------------
FROM deps AS production

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# O processo roda sem privilégios e sem posse do código: `/app` e `/opt/venv`
# seguem pertencendo ao root com permissão de leitura/execução para todos, de
# modo que a aplicação não consiga alterar os próprios arquivos em runtime.
#
# `/app/storage` é a única exceção: os uploads (Sprint 3) são gravados ali em
# runtime, então precisa pertencer ao usuário da aplicação — sem isso,
# `UploadService` falharia com `PermissionError` ao tentar criar o diretório
# do usuário dentro de `storage/uploads/`.
RUN useradd --create-home --uid 1000 marketpulse \
    && chown -R marketpulse:marketpulse /app/storage

USER marketpulse
WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
