"""Agregador dos routers da aplicação."""

from fastapi import APIRouter

from app.api.routes import analytics, auth, health, insights, uploads, users
from app.core.config import settings

api_router = APIRouter()

# `GET /health` é uma sonda de infraestrutura e fica fora do prefixo versionado.
api_router.include_router(health.router)

v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(uploads.router)
v1_router.include_router(analytics.router)
v1_router.include_router(insights.router)
api_router.include_router(v1_router)
