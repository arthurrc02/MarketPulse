"""Testes dos transformers concretos: normalização de moeda, data, percentual e status."""

import datetime
from collections.abc import Callable

import pytest

from etl.exceptions import TransformationError
from etl.extractors import MercadoLivreExtractor, ShopeeExtractor
from etl.parsing import FileSource
from etl.transformers import MercadoLivreTransformer, ShopeeTransformer
from etl.types import OrderStatus


def test_shopee_transformer_normalizes_currency_date_and_status(
    shopee_source: FileSource,
) -> None:
    raw = ShopeeExtractor().extract(shopee_source)

    standardized = ShopeeTransformer().transform(raw)

    row = standardized.iloc[0]
    assert row["external_order_id"] == "1001"
    assert row["unit_price_cents"] == 4990  # "R$ 49,90"
    assert row["total_price_cents"] == 4990 * 2  # quantidade = 2
    assert row["status"] == OrderStatus.COMPLETED  # "Concluido"
    assert row["order_date"] == datetime.date(2026, 8, 5)
    assert row["discount_percentage"] is None  # Shopee (exemplo) não tem esse campo


def test_mercado_livre_transformer_normalizes_percentage(
    mercado_livre_source: FileSource,
) -> None:
    raw = MercadoLivreExtractor().extract(mercado_livre_source)

    standardized = MercadoLivreTransformer().transform(raw)

    row = standardized.iloc[0]
    assert row["unit_price_cents"] == 19990  # "R$ 199,90"
    assert row["discount_percentage"] == pytest.approx(10.5)
    assert row["status"] == OrderStatus.COMPLETED  # "Entregue"


def test_mercado_livre_transformer_handles_missing_discount(
    mercado_livre_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> None:
    """Percentual de desconto vazio é um campo opcional legítimo, não um erro."""
    row = 'V-2,ML-SKU-2,Mouse Gamer,1,"R$ 89,00",,Cancelada,03/08/2026'
    source = make_source(mercado_livre_csv(row))
    raw = MercadoLivreExtractor().extract(source)

    standardized = MercadoLivreTransformer().transform(raw)

    assert standardized.iloc[0]["discount_percentage"] is None
    assert standardized.iloc[0]["status"] == OrderStatus.CANCELLED


def test_unrecognized_status_becomes_unknown_without_failing(
    shopee_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> None:
    row = '1001,SKU-A,Camiseta Azul,2,"R$ 49,90",StatusNovoQueNaoExiste,05/08/2026'
    source = make_source(shopee_csv(row))
    raw = ShopeeExtractor().extract(source)

    standardized = ShopeeTransformer().transform(raw)

    assert standardized.iloc[0]["status"] == OrderStatus.UNKNOWN


@pytest.mark.parametrize(
    "row",
    [
        '1001,SKU-A,Camiseta Azul,2,"nao e um preco",Concluido,05/08/2026',
        '1001,SKU-A,Camiseta Azul,nao-e-numero,"R$ 49,90",Concluido,05/08/2026',
        '1001,SKU-A,Camiseta Azul,2,"R$ 49,90",Concluido,2026-08-05',
    ],
    ids=["moeda_invalida", "quantidade_invalida", "data_invalida"],
)
def test_transformer_raises_transformation_error_with_row_context(
    row: str, shopee_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> None:
    source = make_source(shopee_csv(row))
    raw = ShopeeExtractor().extract(source)

    with pytest.raises(TransformationError, match="linha 2"):
        ShopeeTransformer().transform(raw)
