"""Orquestração das etapas do pipeline ETL: Extract → Transform → Validate → Load."""

from dataclasses import dataclass

from etl.exceptions import ETLError, ExtractionError, LoadError, TransformationError
from etl.extractors.base import Extractor
from etl.loaders.base import Loader
from etl.parsing import FileSource
from etl.schema import validate_canonical_schema
from etl.transformers.base import Transformer
from etl.types import Marketplace


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Resumo da execução de um pipeline ETL."""

    marketplace: Marketplace
    rows_extracted: int
    rows_loaded: int


@dataclass(frozen=True, slots=True)
class ETLPipeline:
    """Encadeia extração, transformação, validação e carga para um marketplace.

    As três etapas (mais a validação, comum a todo marketplace — ver
    `etl.schema`) são injetadas, de modo que cada marketplace combine suas
    próprias implementações sem alterar o orquestrador.
    """

    marketplace: Marketplace
    extractor: Extractor
    transformer: Transformer
    loader: Loader

    def run(self, source: FileSource) -> PipelineResult:
        """Executa o pipeline completo sobre ``source``.

        Qualquer exceção não prevista, levantada por uma implementação
        concreta, é reembrulhada na `ETLError` da etapa correspondente — o
        chamador (o orquestrador do backend) só precisa tratar um tipo por
        etapa para decidir a mensagem gravada em `Upload.error_message`.

        Raises:
            ExtractionError: falha ao ler o arquivo.
            TransformationError: falha ao padronizar os dados, ou dados
                padronizados fora do esquema canônico (etapa de validação).
            LoadError: falha ao persistir os dados já validados.
        """
        try:
            raw = self.extractor.extract(source)
        except ETLError:
            raise
        except Exception as exc:
            raise ExtractionError(str(exc)) from exc

        try:
            standardized = self.transformer.transform(raw)
            validate_canonical_schema(standardized)
        except ETLError:
            raise
        except Exception as exc:
            raise TransformationError(str(exc)) from exc

        try:
            rows_loaded = self.loader.load(standardized)
        except ETLError:
            raise
        except Exception as exc:
            raise LoadError(str(exc)) from exc

        return PipelineResult(
            marketplace=self.marketplace,
            rows_extracted=len(raw),
            rows_loaded=rows_loaded,
        )
