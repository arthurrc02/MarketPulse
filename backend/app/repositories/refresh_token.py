"""Repositório de refresh tokens."""

import uuid
from datetime import datetime

from sqlalchemy import select

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository):
    """Acesso a dados de `RefreshToken`. Não abre nem confirma transações."""

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Busca um refresh token pelo seu hash, independentemente do estado."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.session.scalars(stmt).first()

    def create(self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        """Cria e adiciona um novo refresh token à sessão (sem commit)."""
        refresh_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(refresh_token)
        self.session.flush()
        return refresh_token

    def revoke(self, refresh_token: RefreshToken, *, revoked_at: datetime) -> None:
        """Marca `refresh_token` como revogado (idempotente)."""
        if refresh_token.revoked_at is None:
            refresh_token.revoked_at = revoked_at
            self.session.flush()
