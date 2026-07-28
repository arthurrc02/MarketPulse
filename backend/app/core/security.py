"""Primitivas de segurança: hash de senha, JWT e tokens de atualização opacos.

O access token é um JWT assinado (stateless, de curta duração). O refresh
token é uma string aleatória opaca — **não** um JWT — cujo hash é armazenado
em `refresh_tokens` (ver `app/models/refresh_token.py`). Essa escolha permite
revogação real (logout) e rotação a cada uso, o que um refresh token
puramente stateless não ofereceria (ver ADR-018 em `docs/decisions.md`).
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# bcrypt ignora silenciosamente bytes além do 72º; validamos isso explicitamente
# no schema de entrada (`app.schemas.user`) para não confiar no truncamento.
_BCRYPT_MAX_PASSWORD_BYTES = 72

REFRESH_TOKEN_BYTES = 32


class TokenType(StrEnum):
    """Tipo declarado no claim `type` do JWT, evitando reuso indevido entre fins."""

    ACCESS = "access"


class TokenDecodeError(Exception):
    """O token é malformado, tem assinatura inválida ou expirou."""


@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    """Claims decodificados de um access token válido."""

    user_id: uuid.UUID
    expires_at: datetime


def hash_password(password: str) -> str:
    """Gera o hash bcrypt de `password`.

    Assume que o comprimento em bytes já foi validado (ver
    `_BCRYPT_MAX_PASSWORD_BYTES`); chamado apenas a partir de schemas validados.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica `password` contra um hash bcrypt previamente gerado."""
    password_bytes = password.encode("utf-8")[:_BCRYPT_MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        # Hash malformado (não deveria ocorrer com dados gerados por hash_password).
        return False


def create_access_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    """Cria um access token JWT para `user_id`. Retorna o token e sua expiração."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": TokenType.ACCESS.value,
        "iat": now,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
    }
    secret_key = settings.SECRET_KEY.get_secret_value()
    token = jwt.encode(payload, secret_key, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> AccessTokenPayload:
    """Decodifica e valida um access token.

    Raises:
        TokenDecodeError: assinatura inválida, token expirado, claims
            ausentes ou `type` diferente de `access`.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise TokenDecodeError("Token inválido ou expirado.") from exc

    if payload.get("type") != TokenType.ACCESS.value:
        raise TokenDecodeError("Tipo de token inesperado.")

    try:
        user_id = uuid.UUID(str(payload["sub"]))
        expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=UTC)
    except (KeyError, ValueError) as exc:
        raise TokenDecodeError("Claims do token ausentes ou inválidos.") from exc

    return AccessTokenPayload(user_id=user_id, expires_at=expires_at)


def generate_refresh_token() -> tuple[str, str]:
    """Gera um refresh token opaco. Retorna `(token_bruto, hash_para_persistir)`.

    Apenas o hash é armazenado em banco; o valor bruto é devolvido ao cliente
    uma única vez, no momento da emissão.
    """
    raw_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    return raw_token, hash_refresh_token(raw_token)


def hash_refresh_token(raw_token: str) -> str:
    """Calcula o hash determinístico usado para localizar o token em banco.

    SHA-256 (e não bcrypt) é adequado aqui: o valor já é aleatório de alta
    entropia, não uma senha escolhida por humano — não há necessidade de um
    hash lento nem de salt por registro.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    """Data de expiração de um novo refresh token, a partir de agora."""
    return datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def ensure_aware_utc(value: datetime) -> datetime:
    """Normaliza `value` para um datetime aware em UTC.

    O SQLite (usado nos testes) não preserva timezone em colunas
    `DateTime(timezone=True)` — os valores voltam do banco *naive*. O
    PostgreSQL de produção já devolve datetimes aware. Sem essa normalização,
    comparar os dois lança `TypeError: can't compare offset-naive and
    offset-aware datetimes` dependendo do backend em uso.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
