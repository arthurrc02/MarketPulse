"""Ponto de entrada da API do MarketPulse."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Executa a inicialização e o encerramento da aplicação."""
    configure_logging()
    yield


def create_app() -> FastAPI:
    """Cria e configura a instância do FastAPI (application factory)."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        # Documentação interativa fica desabilitada em produção.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # `GET /health` é uma sonda de infraestrutura e fica fora do prefixo
    # versionado. Os endpoints de negócio entram sob `settings.API_V1_PREFIX`
    # a partir da Sprint 1.
    app.include_router(api_router)

    return app


app = create_app()
