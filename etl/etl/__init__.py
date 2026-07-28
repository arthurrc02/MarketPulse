"""Motor ETL do MarketPulse.

A Sprint 0 entrega apenas a **estrutura** do módulo: os contratos das três
etapas do pipeline (extract, transform, load) e os tipos compartilhados.
Nenhum processamento é implementado aqui — as implementações concretas por
marketplace chegam na Sprint 4 (ETL Engine).
"""

from etl.exceptions import ETLError, ExtractionError, LoadError, TransformationError
from etl.pipeline import ETLPipeline, PipelineResult
from etl.types import Marketplace

__all__ = [
    "ETLError",
    "ETLPipeline",
    "ExtractionError",
    "LoadError",
    "Marketplace",
    "PipelineResult",
    "TransformationError",
]

__version__ = "0.1.0"
