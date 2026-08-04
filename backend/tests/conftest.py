"""Fixtures compartilhadas pelos testes do backend.

Por padrão os testes rodam contra um SQLite em memória — rápido e sem
dependência externa. Definir `TEST_DATABASE_URL` (como a CI faz, apontando
para o serviço PostgreSQL) troca o backend para validar o caminho real de
produção (ver ADR-019 em `docs/decisions.md`).
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_upload_service
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app

# Importa os models para que `Base.metadata` os conheça antes do `create_all`.
from app.models import RefreshToken, Upload, User  # noqa: F401
from app.services.upload import UploadService
from app.storage.local import LocalFileStorage


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
def upload_storage_dir(tmp_path: Path) -> Path:
    """Diretório de storage isolado por teste — nunca toca `storage/uploads` real."""
    return tmp_path / "uploads"


@pytest.fixture
def app() -> FastAPI:
    """Instância da aplicação FastAPI usada nos testes."""
    return create_app()


@pytest.fixture
def client(app: FastAPI, db_session: Session, upload_storage_dir: Path) -> Iterator[TestClient]:
    """Cliente HTTP de teste com `get_session`/`get_upload_service` substituídos."""

    def _override_get_session() -> Iterator[Session]:
        yield db_session

    def _override_get_upload_service() -> UploadService:
        storage = LocalFileStorage(upload_storage_dir)
        return UploadService(
            session=db_session,
            storage=storage,
            max_upload_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
        )

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_upload_service] = _override_get_upload_service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
