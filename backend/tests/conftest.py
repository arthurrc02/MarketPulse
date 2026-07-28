"""Fixtures compartilhadas pelos testes do backend.

Por padrão os testes rodam contra um SQLite em memória — rápido e sem
dependência externa. Definir `TEST_DATABASE_URL` (como a CI faz, apontando
para o serviço PostgreSQL) troca o backend para validar o caminho real de
produção (ver ADR-019 em `docs/decisions.md`).
"""

import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app

# Importa os models para que `Base.metadata` os conheça antes do `create_all`.
from app.models import RefreshToken, User  # noqa: F401


@pytest.fixture
def engine() -> Iterator[Engine]:
    """Engine de banco isolada por teste, com o schema criado do zero."""
    url = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    is_sqlite = url.startswith("sqlite")
    test_engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        poolclass=StaticPool if is_sqlite else None,
    )
    Base.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """Sessão de banco para uso direto nos testes (fora do ciclo HTTP)."""
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app() -> FastAPI:
    """Instância da aplicação FastAPI usada nos testes."""
    return create_app()


@pytest.fixture
def client(app: FastAPI, db_session: Session) -> Iterator[TestClient]:
    """Cliente HTTP de teste com `get_session` substituído pela sessão de teste."""

    def _override_get_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
