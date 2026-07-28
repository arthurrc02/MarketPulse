"""Rotas de usuário. Todas protegidas por `get_current_user`."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep
from app.schemas.errors import ErrorResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Usuário autenticado",
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
def read_current_user(current_user: CurrentUserDep) -> UserRead:
    """Retorna os dados do usuário autenticado no token de acesso."""
    return UserRead.model_validate(current_user)
