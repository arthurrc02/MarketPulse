"""Orquestração das etapas do pipeline ETL.

Apenas a estrutura é definida na Sprint 0. A execução real (`ETLPipeline.run`)
é implementada na Sprint 4.
"""

from dataclasses import dataclass
from pathlib import Path

from etl.extractors.base import Extractor
from etl.loaders.base import Loader
from etl.transformers.base import Transformer
from etl.types import Marketplace


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Resumo da execução de um pipeline ETL."""

    marketplace: Marketplace
    source: Path
    rows_extracted: int
    rows_loaded: int


@dataclass(frozen=True, slots=True)
class ETLPipeline:
    """Encadeia extração, transformação e carga para um marketplace.

    As três etapas são injetadas, de modo que cada marketplace combine suas
    próprias implementações sem alterar o orquestrador.
    """

    marketplace: Marketplace
    extractor: Extractor
    transformer: Transformer
    loader: Loader

    def run(self, source: Path) -> PipelineResult:
        """Executa o pipeline completo sobre ``source``.

        Raises:
            NotImplementedError: a execução do pipeline chega na Sprint 4
                (ETL Engine); a Sprint 0 entrega somente a estrutura.
        """
        raise NotImplementedError("O pipeline ETL será implementado na Sprint 4.")
