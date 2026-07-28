"""Testes do endpoint GET /health."""

from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_returns_200(client: TestClient) -> None:
    """O endpoint responde 200."""
    response = client.get("/health")

    assert response.status_code == 200


def test_health_returns_service_metadata(client: TestClient) -> None:
    """O payload traz status, nome, versão e ambiente do serviço."""
    response = client.get("/health")

    assert response.json() == {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


def test_health_does_not_require_database(client: TestClient) -> None:
    """A sonda de liveness responde sem depender de conexão com o banco.

    O engine é criado de forma preguiçosa (lazy), então nenhuma conexão é
    aberta enquanto nenhum endpoint usar `SessionDep`.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
