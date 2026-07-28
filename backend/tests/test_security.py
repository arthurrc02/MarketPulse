"""Testes das primitivas de segurança (hash de senha, JWT, refresh token)."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    TokenDecodeError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_password_produces_a_verifiable_but_different_hash_each_time() -> None:
    """O hash muda a cada chamada (salt aleatório), mas ambos verificam a mesma senha."""
    first_hash = hash_password("Sup3rSecret!")
    second_hash = hash_password("Sup3rSecret!")

    assert first_hash != second_hash
    assert verify_password("Sup3rSecret!", first_hash)
    assert verify_password("Sup3rSecret!", second_hash)


def test_verify_password_rejects_wrong_password() -> None:
    """Uma senha incorreta não verifica contra o hash."""
    hashed = hash_password("Sup3rSecret!")

    assert verify_password("wrong-password", hashed) is False


def test_access_token_round_trip() -> None:
    """Um token recém-criado decodifica de volta para o mesmo `user_id`."""
    user_id = uuid.uuid4()

    token, expires_at = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload.user_id == user_id
    assert payload.expires_at == pytest.approx(expires_at, abs=timedelta(seconds=1))


def test_decode_access_token_rejects_garbage() -> None:
    """Uma string qualquer não é um JWT válido."""
    with pytest.raises(TokenDecodeError):
        decode_access_token("not-a-real-token")


def test_decode_access_token_rejects_expired_token() -> None:
    """Um token cujo `exp` já passou é rejeitado."""
    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "iat": now - timedelta(minutes=30),
            "exp": now - timedelta(minutes=1),
        },
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(TokenDecodeError):
        decode_access_token(expired_token)


def test_decode_access_token_rejects_wrong_token_type() -> None:
    """Um JWT válido, mas com `type` diferente de `access`, é rejeitado."""
    now = datetime.now(UTC)
    wrong_type_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(TokenDecodeError):
        decode_access_token(wrong_type_token)


def test_decode_access_token_rejects_wrong_signature() -> None:
    """Um token assinado com outra chave é rejeitado."""
    now = datetime.now(UTC)
    token_signed_elsewhere = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        "a-completely-different-secret-key-value",
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(TokenDecodeError):
        decode_access_token(token_signed_elsewhere)


def test_generate_refresh_token_returns_matching_raw_and_hash() -> None:
    """`generate_refresh_token` devolve um par consistente com `hash_refresh_token`."""
    raw_token, token_hash = generate_refresh_token()

    assert hash_refresh_token(raw_token) == token_hash


def test_generate_refresh_token_is_unique_per_call() -> None:
    """Cada chamada gera um token diferente (alta entropia, sem colisão prática)."""
    first_raw, first_hash = generate_refresh_token()
    second_raw, second_hash = generate_refresh_token()

    assert first_raw != second_raw
    assert first_hash != second_hash
