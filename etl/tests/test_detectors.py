"""Testes da detecção automática de marketplace."""

from collections.abc import Callable

import pytest

from etl.detectors import detect_marketplace
from etl.exceptions import UnknownMarketplaceError
from etl.parsing import FileSource, peek_headers
from etl.types import Marketplace


def test_detects_shopee_from_headers(shopee_source: FileSource) -> None:
    headers = peek_headers(shopee_source)
    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_detects_mercado_livre_from_headers(mercado_livre_source: FileSource) -> None:
    headers = peek_headers(mercado_livre_source)
    assert detect_marketplace(headers) is Marketplace.MERCADO_LIVRE


def test_detection_ignores_column_order(make_source: Callable[..., FileSource]) -> None:
    """A ordem das colunas no arquivo não deve importar — comparação é por conjunto."""
    reordered = b"Status,ID do Pedido,Data do Pedido,SKU,Produto,Preco Unitario,Quantidade\n"
    headers = peek_headers(make_source(reordered))
    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_unknown_headers_raise_unknown_marketplace_error() -> None:
    headers = ["coluna_a", "coluna_b"]
    with pytest.raises(UnknownMarketplaceError):
        detect_marketplace(headers)


def test_partial_shopee_headers_are_not_detected() -> None:
    """Faltar mesmo uma coluna esperada não deve "quase" identificar o marketplace."""
    headers = ["id_do_pedido", "sku", "produto"]
    with pytest.raises(UnknownMarketplaceError):
        detect_marketplace(headers)
