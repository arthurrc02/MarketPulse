"""Tipos compartilhados pelo pipeline ETL."""

from enum import StrEnum


class Marketplace(StrEnum):
    """Marketplaces suportados pelo MarketPulse.

    Os quatro valores refletem a visão de produto; a Sprint 4 implementa
    detector/extractor/transformer apenas para `SHOPEE` e `MERCADO_LIVRE` —
    ver decisions.md sobre a redução de escopo. `AMAZON` e `MAGALU`
    permanecem declarados para não exigir uma migration de enum quando os
    detectores correspondentes forem adicionados.
    """

    SHOPEE = "shopee"
    MERCADO_LIVRE = "mercado_livre"
    AMAZON = "amazon"
    MAGALU = "magalu"


class SourceFormat(StrEnum):
    """Formatos de arquivo aceitos na importação."""

    CSV = "csv"
    XLSX = "xlsx"


class OrderStatus(StrEnum):
    """Status canônico de um item de pedido, após a transformação.

    Cada marketplace tem seu próprio vocabulário de status (ver
    `etl.transformers.common`); os transformers mapeiam para este conjunto
    fechado. Um status não reconhecido vira `UNKNOWN` — não interrompe o
    processamento do arquivo (ver ADR correspondente em decisions.md).
    """

    COMPLETED = "completed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    UNKNOWN = "unknown"
