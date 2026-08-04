"""Configurações da aplicação, carregadas de variáveis de ambiente."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["local", "development", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Valor de fábrica de `SECRET_KEY`: aceitável em `local`/`development`, mas
# bloqueado em `production` pelo validador `_forbid_insecure_secret_in_production`.
# Precisa ter pelo menos 32 bytes: PyJWT emite `InsecureKeyLengthWarning` para
# chaves HMAC mais curtas (RFC 7518 §3.2), e a suíte de testes trata warnings
# como erro (`filterwarnings = ["error"]`).
_INSECURE_DEFAULT_SECRET_KEY = "insecure-dev-secret-change-me-in-production"

# backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> raiz
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Configurações da API lidas de variáveis de ambiente e/ou de um arquivo `.env`."""

    model_config = SettingsConfigDict(
        # O `.env` da raiz é o mesmo consumido pelo Docker Compose; um `.env`
        # no diretório atual, se existir, tem precedência. Ambos são opcionais:
        # em contêiner as variáveis chegam pelo ambiente.
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # -- Aplicação ---------------------------------------------------------
    PROJECT_NAME: str = "MarketPulse API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = "local"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: LogLevel = "INFO"

    # -- CORS --------------------------------------------------------------
    # `NoDecode` desliga o parse JSON automático de tipos complexos, para que o
    # validador abaixo receba a string crua e aceite o formato separado por
    # vírgulas — mais natural em `.env` e no Docker Compose.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # -- Banco de dados ----------------------------------------------------
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "marketpulse"
    POSTGRES_DB: str = "marketpulse"
    # `SecretStr` evita que a senha vaze em `repr()`, logs ou `model_dump()`.
    POSTGRES_PASSWORD: SecretStr = SecretStr("marketpulse")

    # Se preenchida, tem precedência sobre as variáveis POSTGRES_* acima.
    DATABASE_URL: SecretStr | None = None

    # -- Autenticação (JWT + refresh token) ---------------------------------
    SECRET_KEY: SecretStr = SecretStr(_INSECURE_DEFAULT_SECRET_KEY)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -- Uploads -------------------------------------------------------------
    # Local, organizado por usuário: `{UPLOAD_STORAGE_DIR}/{user_id}/{stored_filename}`.
    # Sem S3/nuvem nesta sprint (ver decisions.md).
    UPLOAD_STORAGE_DIR: Path = REPO_ROOT / "storage" / "uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MiB

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Aceita `CORS_ORIGINS` como lista JSON ou como string separada por vírgulas."""
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if stripped.startswith("["):
            return json.loads(stripped)
        return [origin.strip() for origin in stripped.split(",") if origin.strip()]

    # As propriedades abaixo são deliberadamente `@property`, e não
    # `@computed_field`: um campo computado entraria em `model_dump()` e
    # exporia a senha do banco em qualquer serialização das settings.
    @property
    def sqlalchemy_database_uri(self) -> str:
        """URL de conexão do SQLAlchemy (driver psycopg 3)."""
        if self.DATABASE_URL is not None:
            return self.DATABASE_URL.get_secret_value()
        dsn = PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
        return str(dsn)

    @property
    def is_production(self) -> bool:
        """Indica se a aplicação está rodando em ambiente produtivo."""
        return self.ENVIRONMENT == "production"

    @model_validator(mode="after")
    def _forbid_insecure_secret_in_production(self) -> "Settings":
        """Impede subir em produção com a `SECRET_KEY` de desenvolvimento.

        Um JWT assinado com uma chave pública (versionada em `config.py`)
        permitiria forjar tokens de acesso de qualquer usuário.
        """
        uses_insecure_secret = self.SECRET_KEY.get_secret_value() == _INSECURE_DEFAULT_SECRET_KEY
        if self.is_production and uses_insecure_secret:
            raise ValueError(
                "SECRET_KEY não pode usar o valor padrão de desenvolvimento em produção. "
                "Defina uma chave forte e única via variável de ambiente."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a instância única (cacheada) das configurações."""
    return Settings()


settings = get_settings()
