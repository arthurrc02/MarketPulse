"""Endpoint de health check."""

from fastapi import APIRouter, status

from app.api.deps import HealthServiceDep
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Verifica se a API está no ar e retorna metadados básicos do serviço.",
)
def health(service: HealthServiceDep) -> HealthResponse:
    """Retorna o estado do serviço."""
    return service.check()
