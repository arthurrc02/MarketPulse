"""Schemas do endpoint de health check."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Resposta do endpoint ``GET /health``."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "service": "MarketPulse API",
                    "version": "0.1.0",
                    "environment": "local",
                }
            ]
        }
    )

    status: Literal["ok"] = Field(description="Estado geral do serviço.")
    service: str = Field(description="Nome do serviço.")
    version: str = Field(description="Versão da API.")
    environment: str = Field(description="Ambiente de execução.")
