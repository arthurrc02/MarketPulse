"""Fixtures compartilhadas pelos testes do backend."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Instância da aplicação FastAPI usada nos testes."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Cliente HTTP de teste com o ciclo de lifespan da aplicação ativo."""
    with TestClient(app) as test_client:
        yield test_client
