"""Testes de integração do fluxo de autenticação (router → service → repo → db)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

VALID_PASSWORD = "Sup3rSecret!"


def _register(
    client: TestClient, *, email: str = "user@example.com", password: str = VALID_PASSWORD
) -> Any:
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def _login(
    client: TestClient, *, email: str = "user@example.com", password: str = VALID_PASSWORD
) -> Any:
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


def test_register_creates_user(client: TestClient) -> None:
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


def test_register_never_exposes_the_password_hash(client: TestClient) -> None:
    response = _register(client)

    assert "hashed_password" not in response.json()
    assert "password" not in response.json()


def test_register_normalizes_email_to_lowercase(client: TestClient) -> None:
    response = _register(client, email="User@Example.COM")

    assert response.json()["email"] == "user@example.com"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    _register(client)

    response = _register(client)

    assert response.status_code == 409
    assert response.json() == {"detail": "Este e-mail já está cadastrado."}


def test_register_rejects_duplicate_email_case_insensitively(client: TestClient) -> None:
    _register(client, email="user@example.com")

    response = _register(client, email="USER@EXAMPLE.COM")

    assert response.status_code == 409


@pytest.mark.parametrize(
    "password",
    [
        "short1A",  # menos de 8 caracteres
        "alllowercase1",  # sem maiúscula
        "ALLUPPERCASE1",  # sem minúscula
        "NoDigitsHere",  # sem dígito
    ],
)
def test_register_rejects_weak_password(client: TestClient, password: str) -> None:
    response = _register(client, password=password)

    assert response.status_code == 422


def test_register_rejects_invalid_email_format(client: TestClient) -> None:
    response = _register(client, email="not-an-email")

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


def test_login_succeeds_with_correct_credentials(client: TestClient) -> None:
    _register(client)

    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert isinstance(body["refresh_token"], str) and body["refresh_token"]
    assert body["expires_in"] == pytest.approx(15 * 60, abs=2)


def test_login_is_case_insensitive_on_email(client: TestClient) -> None:
    _register(client, email="user@example.com")

    response = _login(client, email="USER@EXAMPLE.COM")

    assert response.status_code == 200


def test_login_fails_with_wrong_password(client: TestClient) -> None:
    _register(client)

    response = _login(client, password="WrongPassword1")

    assert response.status_code == 401
    assert response.json() == {"detail": "E-mail ou senha inválidos."}


def test_login_fails_with_unknown_email(client: TestClient) -> None:
    response = _login(client, email="ghost@example.com")

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


def test_refresh_issues_a_new_token_pair(client: TestClient) -> None:
    _register(client)
    tokens = _login(client).json()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_rotates_the_token_and_the_old_one_stops_working(client: TestClient) -> None:
    _register(client)
    tokens = _login(client).json()

    first_refresh = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first_refresh.status_code == 200

    reuse_attempt = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert reuse_attempt.status_code == 401


def test_refresh_fails_with_unknown_token(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Sessão inválida ou expirada. Faça login novamente."}


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


def test_logout_revokes_the_refresh_token(client: TestClient) -> None:
    _register(client)
    tokens = _login(client).json()

    logout_response = client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 204

    refresh_attempt = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_attempt.status_code == 401


def test_logout_is_idempotent_for_unknown_tokens(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout", json={"refresh_token": "never-issued"})

    assert response.status_code == 204


def test_logout_is_idempotent_when_called_twice(client: TestClient) -> None:
    _register(client)
    tokens = _login(client).json()

    first = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    second = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    assert first.status_code == 204
    assert second.status_code == 204


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------


def test_me_returns_the_authenticated_user(client: TestClient) -> None:
    _register(client)
    tokens = _login(client).json()

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_me_fails_without_a_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_me_fails_with_a_garbage_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_fails_with_a_refresh_token_used_as_access_token(client: TestClient) -> None:
    """Um refresh token não deve funcionar como access token (tipos não se misturam)."""
    _register(client)
    tokens = _login(client).json()

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )

    assert response.status_code == 401


def test_me_fails_once_the_user_is_deactivated(client: TestClient, db_session: Session) -> None:
    """Um access token continua com assinatura válida mesmo após a conta ser desativada."""
    _register(client)
    tokens = _login(client).json()

    user = db_session.scalars(select(User).where(User.email == "user@example.com")).one()
    user.is_active = False
    db_session.commit()

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Esta conta está desativada."}
