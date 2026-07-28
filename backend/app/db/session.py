"""Engine e factory de sessões do SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine: Engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Iterator[Session]:
    """Fornece uma sessão de banco por requisição, encerrando-a ao final."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
