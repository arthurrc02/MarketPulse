"""Dependências compartilhadas pelos endpoints."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import InvalidTokenError
from app.core.security import TokenDecodeError, decode_access_token
from app.db.session import get_session
from app.models.user import User
from app.services.analytics import AnalyticsService
from app.services.auth import AuthService
from app.services.etl_processor import ETLProcessorService
from app.services.health import HealthService
from app.services.upload import UploadService
from app.storage.local import LocalFileStorage

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]


def get_health_service(settings: SettingsDep) -> HealthService:
    """Injeta o serviço de health check."""
    return HealthService(settings)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]


def get_auth_service(session: SessionDep) -> AuthService:
    """Injeta o serviço de autenticação."""
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

# `auto_error=False`: sem isso, a ausência do header `Authorization` gera um
# 403 do próprio Starlette em vez do 401 (com `WWW-Authenticate: Bearer`) que
# `get_current_user` produz abaixo — 401 é a resposta semanticamente correta
# para "não autenticado".
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """Resolve o usuário autenticado a partir do header `Authorization: Bearer`.

    Usado por toda rota protegida. Raises `InvalidTokenError`/`UserInactiveError`
    (traduzidos para HTTP pelo exception handler em `app.main`).
    """
    if credentials is None:
        raise InvalidTokenError("Token de acesso ausente.")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenDecodeError as exc:
        raise InvalidTokenError(str(exc)) from exc

    return auth_service.get_active_user(payload.user_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_upload_service(session: SessionDep, settings: SettingsDep) -> UploadService:
    """Injeta o serviço de upload, com o storage local apontando para `UPLOAD_STORAGE_DIR`."""
    storage = LocalFileStorage(settings.UPLOAD_STORAGE_DIR)
    return UploadService(
        session=session, storage=storage, max_upload_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES
    )


UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]


def get_etl_processor_service(session: SessionDep, settings: SettingsDep) -> ETLProcessorService:
    """Injeta o serviço de processamento ETL, com o mesmo storage do upload."""
    storage = LocalFileStorage(settings.UPLOAD_STORAGE_DIR)
    return ETLProcessorService(session=session, storage=storage)


ETLProcessorServiceDep = Annotated[ETLProcessorService, Depends(get_etl_processor_service)]


def get_analytics_service(session: SessionDep) -> AnalyticsService:
    """Injeta o serviço de Analytics. Sem storage — só leitura agregada do banco."""
    return AnalyticsService(session)


AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
