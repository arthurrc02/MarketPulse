"""Motor ETL do MarketPulse.

Extract → Transform → Validate → Load. A Sprint 4 implementa dois formatos de
exemplo (Shopee e Mercado Livre) — ver `docs/decisions.md` sobre por que o
escopo foi propositalmente reduzido de "todos os marketplaces" para "a
arquitetura pronta para adicionar mais um facilmente".
"""

from etl.components import get_pipeline_components
from etl.detectors import detect_marketplace
from etl.exceptions import (
    ETLError,
    ExtractionError,
    LoadError,
    TransformationError,
    UnknownMarketplaceError,
)
from etl.parsing import FileSource
from etl.pipeline import ETLPipeline, PipelineResult
from etl.types import Marketplace, OrderStatus, SourceFormat

__all__ = [
    "ETLError",
    "ETLPipeline",
    "ExtractionError",
    "FileSource",
    "LoadError",
    "Marketplace",
    "OrderStatus",
    "PipelineResult",
    "SourceFormat",
    "TransformationError",
    "UnknownMarketplaceError",
    "detect_marketplace",
    "get_pipeline_components",
]

__version__ = "0.2.0"
