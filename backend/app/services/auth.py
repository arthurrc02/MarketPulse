"""Serviço de autenticação: cadastro, login, renovação e revogação de sessão."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserInactiveError,
)
from app.core.security import (
    create_access_token,
    ensure_aware_utc,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate


@dataclass(frozen=True, slots=True)
class _IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    """Regras de negócio de autenticação.

    Controla o limite transacional: cada método público faz `commit` ao
    final do caminho de sucesso (ou deixa o `rollback` implícito da sessão de
    requisição acontecer, se uma exceção subir primeiro).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._refresh_tokens = RefreshTokenRepository(session)

    def register(self, data: UserCreate) -> User:
        """Cria um novo usuário com senha em hash.

        Raises:
            EmailAlreadyRegisteredError: já existe conta com esse e-mail.
        """
        if self._users.get_by_email(data.email) is not None:
            raise EmailAlreadyRegisteredError()

        try:
            user = self._users.create(
                email=data.email, hashed_password=hash_password(data.password)
            )
            self._session.commit()
        except IntegrityError as exc:
            # Corrida entre a checagem acima e o INSERT: outra requisição
            # cadastrou o mesmo e-mail nesse meio-tempo. A constraint UNIQUE
            # do banco é a garantia real; a checagem prévia é só uma resposta
            # rápida no caso comum.
            self._session.rollback()
            raise EmailAlreadyRegisteredError() from exc

        self._session.refresh(user)
        return user

    def authenticate(self, *, email: str, password: str) -> TokenResponse:
        """Valida credenciais e emite um novo par de tokens.

        Raises:
            InvalidCredentialsError: e-mail não cadastrado ou senha incorreta.
            UserInactiveError: a conta existe, mas está desativada.
        """
        user = self._users.get_by_email(email.strip().lower())
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise UserInactiveError()

        tokens = self._issue_tokens(user.id)
        self._session.commit()
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )

    def refresh(self, raw_refresh_token: str) -> TokenResponse:
        """Rotaciona um refresh token válido, emitindo um novo par de tokens.

        O token informado é revogado mesmo em caso de sucesso (rotação): um
        refresh token só pode ser usado uma vez.

        Raises:
            InvalidTokenError: token inexistente, revogado ou expirado.
            UserInactiveError: a conta do token foi desativada.
        """
        record = self._refresh_tokens.get_by_hash(hash_refresh_token(raw_refresh_token))
        now = datetime.now(UTC)
        if (
            record is None
            or record.revoked_at is not None
            or ensure_aware_utc(record.expires_at) < now
        ):
            raise InvalidTokenError()

        user = self._users.get_by_id(record.user_id)
        if user is None:
            raise InvalidTokenError()
        if not user.is_active:
            raise UserInactiveError()

        self._refresh_tokens.revoke(record, revoked_at=now)
        tokens = self._issue_tokens(user.id)
        self._session.commit()
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )

    def logout(self, raw_refresh_token: str) -> None:
        """Revoga um refresh token.

        Idempotente por design: um token inexistente ou já revogado não é um
        erro — o objetivo final (token não utilizável) já está satisfeito.
        """
        record = self._refresh_tokens.get_by_hash(hash_refresh_token(raw_refresh_token))
        if record is not None:
            self._refresh_tokens.revoke(record, revoked_at=datetime.now(UTC))
            self._session.commit()

    def get_active_user(self, user_id: uuid.UUID) -> User:
        """Busca um usuário ativo pelo id, para uso por `get_current_user`.

        Raises:
            InvalidTokenError: usuário inexistente (conta pode ter sido
                removida após o token ser emitido).
            UserInactiveError: a conta existe, mas está desativada.
        """
        user = self._users.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError()
        if not user.is_active:
            raise UserInactiveError()
        return user

    def _issue_tokens(self, user_id: uuid.UUID) -> _IssuedTokens:
        access_token, expires_at = create_access_token(user_id)
        raw_refresh_token, token_hash = generate_refresh_token()
        self._refresh_tokens.create(
            user_id=user_id, token_hash=token_hash, expires_at=refresh_token_expiry()
        )
        expires_in = int((expires_at - datetime.now(UTC)).total_seconds())
        return _IssuedTokens(
            access_token=access_token, refresh_token=raw_refresh_token, expires_in=expires_in
        )
