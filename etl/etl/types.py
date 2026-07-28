"""Tipos compartilhados pelo pipeline ETL."""

from enum import StrEnum


class Marketplace(StrEnum):
    """Marketplaces suportados pelo MarketPulse."""

    SHOPEE = "shopee"
    MERCADO_LIVRE = "mercado_livre"
    AMAZON = "amazon"
    MAGALU = "magalu"


class SourceFormat(StrEnum):
    """Formatos de arquivo aceitos na importação."""

    CSV = "csv"
    XLSX = "xlsx"
