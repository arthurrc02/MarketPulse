"""Erros de domínio, desacoplados de HTTP.

Services levantam essas exceções; `app/main.py` registra um exception handler
que as traduz para respostas HTTP. Isso mantém a camada de serviço sem
conhecimento de FastAPI/Starlette (ver ADR-004 em `docs/decisions.md`).
"""

from fastapi import status


class AppError(Exception):
    """Erro de domínio base. Nunca instanciada diretamente."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Erro inesperado."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail is not None:
            self.detail = detail


class EmailAlreadyRegisteredError(AppError):
    """Já existe uma conta cadastrada com o e-mail informado."""

    status_code = status.HTTP_409_CONFLICT
    detail = "Este e-mail já está cadastrado."


class InvalidCredentialsError(AppError):
    """E-mail ou senha não conferem com nenhuma conta ativa."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "E-mail ou senha inválidos."


class InvalidTokenError(AppError):
    """Access ou refresh token ausente, malformado, expirado ou revogado."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Sessão inválida ou expirada. Faça login novamente."


class UserInactiveError(AppError):
    """A conta existe, mas foi desativada."""

    status_code = status.HTTP_403_FORBIDDEN
    detail = "Esta conta está desativada."
