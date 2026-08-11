"""Hotfix Sprint 4.2 — o `ShopeeTransformer` interpreta o relatório oficial real.

`tests/fixtures/shopee/orders.xlsx` é um relatório real exportado do Seller
Center da Shopee (239 pedidos) — a fonte de verdade do layout oficial (ver
ADR-061 em decisions.md). O Hotfix 4.1 já resolvia a detecção; este arquivo
prova que a extração, transformação, validação e carga completam sem erro
sobre o arquivo real, sem regredir o formato de exemplo (coberto pelos
demais arquivos de teste do pacote).
"""

from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from etl import ETLPipeline, get_pipeline_components
from etl.detectors import detect_marketplace
from etl.loaders.base import Loader
from etl.parsing import FileSource, peek_headers
from etl.schema import validate_canonical_schema
from etl.types import Marketplace, OrderStatus, SourceFormat

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "shopee" / "orders.xlsx"


class _RecordingLoader(Loader):
    def __init__(self) -> None:
        self.received: pd.DataFrame | None = None

    def load(self, standardized: pd.DataFrame) -> int:
        self.received = standardized
        return len(standardized)


@pytest.fixture
def official_fixture_source() -> Iterator[FileSource]:
    with _FIXTURE_PATH.open("rb") as stream:
        yield FileSource(stream=stream, source_format=SourceFormat.XLSX)


def test_fixture_file_exists() -> None:
    """Guarda contra o arquivo de teste ser removido/renomeado por engano."""
    assert _FIXTURE_PATH.is_file()


def test_official_fixture_is_detected_as_shopee(official_fixture_source: FileSource) -> None:
    headers = peek_headers(official_fixture_source)
    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_official_fixture_transforms_all_rows_without_error(
    official_fixture_source: FileSource,
) -> None:
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)

    raw = extractor.extract(official_fixture_source)
    standardized = transformer.transform(raw)

    assert len(raw) == 239
    assert len(standardized) == 239
    validate_canonical_schema(standardized)  # não deve levantar


def test_official_fixture_derives_sku_for_every_row(official_fixture_source: FileSource) -> None:
    """As colunas de SKU do relatório real estão em branco em todas as linhas."""
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)
    standardized = transformer.transform(extractor.extract(official_fixture_source))

    assert (standardized["sku"].str.startswith("AUTO-")).all()


def test_official_fixture_derives_the_same_sku_for_the_same_product(
    official_fixture_source: FileSource,
) -> None:
    """SKU derivado do nome do produto — permite agrupar o mesmo produto entre pedidos.

    O arquivo real tem vários pedidos repetindo o mesmo `product_name`
    (nenhum SKU informado pelo vendedor) — cada grupo deve colapsar para um
    único SKU derivado, nunca um por pedido.
    """
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)
    standardized = transformer.transform(extractor.extract(official_fixture_source))

    sku_per_product = standardized.groupby("product_name")["sku"].nunique()
    assert (sku_per_product == 1).all()
    # E o inverso não vale: produtos diferentes não podem colapsar no mesmo SKU.
    assert standardized["sku"].nunique() == standardized["product_name"].nunique()


def test_official_fixture_status_distribution(official_fixture_source: FileSource) -> None:
    """Cobre os status reais do arquivo, incluindo a família com data embutida (vira UNKNOWN)."""
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)
    standardized = transformer.transform(extractor.extract(official_fixture_source))

    counts = Counter(standardized["status"])
    assert counts[OrderStatus.CANCELLED] == 77
    assert counts[OrderStatus.COMPLETED] == 63
    assert counts[OrderStatus.PENDING] == 83
    # "O comprador pode pedir uma devolução até <data>" — status não mapeado,
    # não interrompe o arquivo (ADR-051).
    assert counts[OrderStatus.UNKNOWN] == 16
    assert sum(counts.values()) == 239


def test_official_fixture_total_price_matches_unit_price_times_quantity(
    official_fixture_source: FileSource,
) -> None:
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)
    standardized = transformer.transform(extractor.extract(official_fixture_source))

    computed = standardized["unit_price_cents"] * standardized["quantity"]
    assert (standardized["total_price_cents"] == computed).all()


def test_official_fixture_runs_through_the_full_pipeline(
    official_fixture_source: FileSource,
) -> None:
    """Extract → Transform → Validação → Load, ponta a ponta, sobre o arquivo real."""
    extractor, transformer = get_pipeline_components(Marketplace.SHOPEE)
    loader = _RecordingLoader()
    pipeline = ETLPipeline(
        marketplace=Marketplace.SHOPEE, extractor=extractor, transformer=transformer, loader=loader
    )

    result = pipeline.run(official_fixture_source)

    assert result.rows_extracted == 239
    assert result.rows_loaded == 239
    assert loader.received is not None
    assert len(loader.received) == 239
