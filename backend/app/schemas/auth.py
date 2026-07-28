"""Schemas de autenticação: login, refresh, logout e o par de tokens."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Payload de login."""

    email: EmailStr
    password: str = Field(description="Senha em texto plano; nunca é persistida ou logada.")


class RefreshRequest(BaseModel):
    """Payload de renovação de sessão."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Payload de logout: revoga o refresh token informado."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Par de tokens emitido no login e a cada renovação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Tempo de vida do access token, em segundos.")
