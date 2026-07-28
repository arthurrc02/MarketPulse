"""Schemas de usuário."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_BYTES = 72  # limite do bcrypt; ver app.core.security.

_LOWERCASE_RE = re.compile(r"[a-z]")
_UPPERCASE_RE = re.compile(r"[A-Z]")
_DIGIT_RE = re.compile(r"\d")


def _validate_password_strength(value: str) -> str:
    """Aplica a política de senha comum a cadastro e (futura) troca de senha."""
    if len(value) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"A senha deve ter pelo menos {_PASSWORD_MIN_LENGTH} caracteres.")
    if len(value.encode("utf-8")) > _PASSWORD_MAX_BYTES:
        raise ValueError(f"A senha deve ter no máximo {_PASSWORD_MAX_BYTES} bytes.")
    if not _LOWERCASE_RE.search(value):
        raise ValueError("A senha deve conter ao menos uma letra minúscula.")
    if not _UPPERCASE_RE.search(value):
        raise ValueError("A senha deve conter ao menos uma letra maiúscula.")
    if not _DIGIT_RE.search(value):
        raise ValueError("A senha deve conter ao menos um dígito.")
    return value


class UserCreate(BaseModel):
    """Payload de cadastro de um novo usuário."""

    email: EmailStr = Field(description="E-mail único do usuário.")
    password: str = Field(description="Senha em texto plano; nunca é persistida ou logada.")

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserRead(BaseModel):
    """Representação pública de um usuário — nunca inclui `hashed_password`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime
