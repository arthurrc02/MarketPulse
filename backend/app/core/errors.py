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


class InvalidUploadError(AppError):
    """O arquivo enviado é inválido (sem nome, vazio etc.)."""

    # `HTTP_422_UNPROCESSABLE_ENTITY` é o nome antigo (RFC 4918/WebDAV) e está
    # depreciado no Starlette em favor de `HTTP_422_UNPROCESSABLE_CONTENT`
    # (RFC 9110) — mesmo caso do 413 em `FileTooLargeError` abaixo.
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Arquivo inválido."


class UnsupportedFileTypeError(AppError):
    """A extensão ou o Content-Type do arquivo não é CSV nem XLSX."""

    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    detail = "Tipo de arquivo não suportado. Envie um arquivo CSV ou XLSX."


class FileTooLargeError(AppError):
    """O arquivo excede `settings.MAX_UPLOAD_SIZE_BYTES`."""

    # `HTTP_413_REQUEST_ENTITY_TOO_LARGE` é o nome antigo (RFC 7231) e está
    # depreciado no Starlette em favor de `HTTP_413_CONTENT_TOO_LARGE` (RFC
    # 9110) — usar o antigo emitiria um warning, tratado como erro pela suíte
    # de testes (`filterwarnings = ["error"]`).
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    detail = "Arquivo excede o tamanho máximo permitido."


class UploadNotFoundError(AppError):
    """Upload inexistente ou pertencente a outro usuário.

    Sempre 404 — nunca 403 — para não revelar a um usuário que um `id` de
    upload existe e pertence a outra pessoa.
    """

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Upload não encontrado."
