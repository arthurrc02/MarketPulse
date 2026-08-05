"""Testes de `ETLPipeline.run`: encadeamento das etapas e tratamento de erro."""

from collections.abc import Callable

import pandas as pd
import pytest

from etl import ETLPipeline, FileSource, Marketplace, PipelineResult, get_pipeline_components
from etl.detectors import detect_marketplace
from etl.exceptions import ExtractionError, LoadError, TransformationError
from etl.loaders.base import Loader
from etl.parsing import peek_headers


class _RecordingLoader(Loader):
    """Loader de teste: guarda o que recebeu, sem tocar em banco algum."""

    def __init__(self) -> None:
        self.received: pd.DataFrame | None = None

    def load(self, standardized: pd.DataFrame) -> int:
        self.received = standardized
        return len(standardized)


class _FailingLoader(Loader):
    def load(self, standardized: pd.DataFrame) -> int:
        raise RuntimeError("falha simulada de persistência")


def _build_pipeline(source: FileSource, loader: Loader) -> tuple[ETLPipeline, Marketplace]:
    marketplace = detect_marketplace(peek_headers(source))
    extractor, transformer = get_pipeline_components(marketplace)
    return (
        ETLPipeline(
            marketplace=marketplace, extractor=extractor, transformer=transformer, loader=loader
        ),
        marketplace,
    )


def test_pipeline_runs_all_stages_end_to_end(shopee_source: FileSource) -> None:
    loader = _RecordingLoader()
    pipeline, marketplace = _build_pipeline(shopee_source, loader)

    result = pipeline.run(shopee_source)

    assert result == PipelineResult(marketplace=marketplace, rows_extracted=1, rows_loaded=1)
    assert loader.received is not None
    assert len(loader.received) == 1


def test_pipeline_wraps_unexpected_extraction_failure(
    make_source: Callable[..., FileSource],
) -> None:
    """Bytes que não são um XLSX válido devem virar `ExtractionError`, não estourar cru."""
    from etl.types import SourceFormat

    source = make_source(b"nao e um xlsx de verdade", source_format=SourceFormat.XLSX)
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)
    pipeline = ETLPipeline(
        marketplace=Marketplace.SHOPEE,
        extractor=extractor,
        transformer=transformer,
        loader=_RecordingLoader(),
    )

    with pytest.raises(ExtractionError):
        pipeline.run(source)


def test_pipeline_wraps_transformation_failure(
    shopee_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> None:
    bad_row = '1001,SKU-A,Camiseta Azul,2,"preco invalido",Concluido,05/08/2026'
    source = make_source(shopee_csv(bad_row))
    pipeline, _ = _build_pipeline(source, _RecordingLoader())

    with pytest.raises(TransformationError):
        pipeline.run(source)


def test_pipeline_propagates_load_failure_without_side_effects(
    shopee_source: FileSource,
) -> None:
    """Uma falha no Loader vira `LoadError` — quem orquestra decide o rollback."""
    pipeline, _ = _build_pipeline(shopee_source, _FailingLoader())

    with pytest.raises(LoadError):
        pipeline.run(shopee_source)


def test_pipeline_result_reflects_row_counts(
    mercado_livre_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> None:
    rows = (
        'V-1,ML-SKU-1,Fone Bluetooth,3,"R$ 199,90","10,5%",Entregue,04/08/2026\n'
        'V-2,ML-SKU-2,Mouse Gamer,1,"R$ 89,00",,Cancelada,03/08/2026'
    )
    source = make_source(mercado_livre_csv(rows))
    pipeline, marketplace = _build_pipeline(source, _RecordingLoader())

    result = pipeline.run(source)

    assert result.rows_extracted == 2
    assert result.rows_loaded == 2
    assert marketplace is Marketplace.MERCADO_LIVRE
