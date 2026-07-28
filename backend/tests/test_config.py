"""Testes das configurações da aplicação."""

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Impede que um `.env` do desenvolvedor interfira nos casos de teste."""
    for name in ("CORS_ORIGINS", "DATABASE_URL", "POSTGRES_HOST", "POSTGRES_PORT", "SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_cors_origins_accepts_comma_separated_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """`CORS_ORIGINS` pode vir como lista separada por vírgulas (formato do .env)."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://app.marketpulse.dev")

    settings = Settings(_env_file=None)

    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "https://app.marketpulse.dev",
    ]


def test_cors_origins_accepts_json_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """`CORS_ORIGINS` também aceita uma lista em JSON."""
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:5173"]')

    settings = Settings(_env_file=None)

    assert settings.CORS_ORIGINS == ["http://localhost:5173"]


def test_database_uri_is_built_from_postgres_settings() -> None:
    """A URL do SQLAlchemy é montada com o driver psycopg 3."""
    settings = Settings(
        _env_file=None,
        POSTGRES_HOST="db",
        POSTGRES_PORT=5432,
        POSTGRES_USER="user",
        POSTGRES_PASSWORD=SecretStr("secret"),
        POSTGRES_DB="marketpulse",
    )

    assert (
        settings.sqlalchemy_database_uri == "postgresql+psycopg://user:secret@db:5432/marketpulse"
    )


def test_database_url_overrides_postgres_settings() -> None:
    """`DATABASE_URL`, quando definida, tem precedência sobre as variáveis POSTGRES_*."""
    settings = Settings(
        _env_file=None,
        DATABASE_URL=SecretStr("postgresql+psycopg://other:pwd@remote:6543/other_db"),
        POSTGRES_HOST="ignored",
    )

    assert settings.sqlalchemy_database_uri == "postgresql+psycopg://other:pwd@remote:6543/other_db"


def test_credentials_are_not_exposed_when_settings_are_serialized() -> None:
    """Senha e URL de conexão não vazam em `repr()` nem em `model_dump()`."""
    settings = Settings(
        _env_file=None,
        POSTGRES_PASSWORD=SecretStr("super-secret"),
        DATABASE_URL=SecretStr("postgresql+psycopg://u:super-secret@h:5432/db"),
    )

    assert "super-secret" not in repr(settings)
    assert "super-secret" not in str(settings.model_dump())
    assert "sqlalchemy_database_uri" not in settings.model_dump()


def test_invalid_log_level_is_rejected() -> None:
    """Um `LOG_LEVEL` inválido falha no carregamento, e não no startup do logging."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOG_LEVEL="VERBOSE")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("environment", "expected"),
    [("local", False), ("development", False), ("staging", False), ("production", True)],
)
def test_is_production(environment: str, expected: bool) -> None:
    """`is_production` só é verdadeiro no ambiente produtivo."""
    # Uma SECRET_KEY customizada evita o validador de produção (testado à
    # parte abaixo) e mantém este teste focado só em `is_production`.
    settings = Settings(
        _env_file=None,
        ENVIRONMENT=environment,  # type: ignore[arg-type]
        SECRET_KEY=SecretStr("a-real-production-secret-key-value"),
    )

    assert settings.is_production is expected


def test_default_secret_key_is_rejected_in_production() -> None:
    """A `SECRET_KEY` padrão de desenvolvimento não pode subir em produção.

    Um JWT assinado com uma chave pública (versionada no repositório)
    permitiria forjar tokens de acesso de qualquer usuário.
    """
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="production")


@pytest.mark.parametrize("environment", ["local", "development", "staging"])
def test_default_secret_key_is_allowed_outside_production(environment: str) -> None:
    """Fora de produção, a `SECRET_KEY` padrão é aceita (conveniência de dev)."""
    settings = Settings(_env_file=None, ENVIRONMENT=environment)  # type: ignore[arg-type]

    assert settings.SECRET_KEY.get_secret_value() == "insecure-dev-secret-change-me-in-production"


def test_custom_secret_key_is_allowed_in_production() -> None:
    """Uma `SECRET_KEY` customizada permite subir em produção normalmente."""
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SECRET_KEY=SecretStr("a-real-production-secret"),
    )

    assert settings.SECRET_KEY.get_secret_value() == "a-real-production-secret"
