"""Repositório de usuários."""

import uuid

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Acesso a dados de `User`. Não abre nem confirma transações."""

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Busca um usuário pelo id."""
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Busca um usuário pelo e-mail (já normalizado em minúsculas)."""
        stmt = select(User).where(User.email == email)
        return self.session.scalars(stmt).first()

    def create(self, *, email: str, hashed_password: str) -> User:
        """Cria e adiciona um novo usuário à sessão (sem commit)."""
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        self.session.flush()
        return user
