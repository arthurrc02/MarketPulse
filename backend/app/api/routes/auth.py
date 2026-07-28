"""Rotas de autenticação: cadastro, login, renovação e logout."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.schemas.errors import ErrorResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo usuário",
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
def register(data: UserCreate, auth_service: AuthServiceDep) -> UserRead:
    """Cria uma nova conta. Não autentica automaticamente — faça login em seguida."""
    user = auth_service.register(data)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar e obter um par de tokens",
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
def login(data: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    """Valida e-mail e senha, emitindo um access token e um refresh token."""
    return auth_service.authenticate(email=data.email, password=data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar a sessão",
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
def refresh(data: RefreshRequest, auth_service: AuthServiceDep) -> TokenResponse:
    """Troca um refresh token válido por um novo par de tokens (rotação)."""
    return auth_service.refresh(data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar a sessão",
)
def logout(data: LogoutRequest, auth_service: AuthServiceDep) -> None:
    """Revoga o refresh token informado. Idempotente: sempre responde 204."""
    auth_service.logout(data.refresh_token)
