"""Detector do formato de exemplo Shopee.

Reconhece o relatório pelo conjunto de cabeçalhos — ver
`etl.transformers.shopee` para o significado de cada coluna.
"""

from etl.detectors.base import MarketplaceDetector
from etl.types import Marketplace

REQUIRED_HEADERS: frozenset[str] = frozenset(
    {
        "id_do_pedido",
        "sku",
        "produto",
        "quantidade",
        "preco_unitario",
        "status",
        "data_do_pedido",
    }
)


class ShopeeDetector(MarketplaceDetector):
    marketplace = Marketplace.SHOPEE

    def matches(self, headers: frozenset[str]) -> bool:
        return REQUIRED_HEADERS.issubset(headers)
