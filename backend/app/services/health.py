"""Serviço de health check."""

from app.core.config import Settings
from app.schemas.health import HealthResponse


class HealthService:
    """Monta o retorno de liveness da API.

    Intencionalmente não toca no banco de dados: ``GET /health`` é uma sonda de
    *liveness*, usada por Docker/CI para saber se o processo está de pé. Um
    check de *readiness* que valide dependências externas será adicionado
    quando houver dependências de fato (ver `docs/decisions.md`).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check(self) -> HealthResponse:
        """Retorna o estado atual do serviço."""
        return HealthResponse(
            status="ok",
            service=self._settings.PROJECT_NAME,
            version=self._settings.VERSION,
            environment=self._settings.ENVIRONMENT,
        )
