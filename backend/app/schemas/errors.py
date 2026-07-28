"""Schema de erro usado apenas para documentar respostas de falha no OpenAPI."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Formato de erro devolvido pelos exception handlers de `AppError`."""

    detail: str
