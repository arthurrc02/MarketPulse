"""Dependências compartilhadas pelos endpoints."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.services.health import HealthService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]


def get_health_service(settings: SettingsDep) -> HealthService:
    """Injeta o serviço de health check."""
    return HealthService(settings)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
