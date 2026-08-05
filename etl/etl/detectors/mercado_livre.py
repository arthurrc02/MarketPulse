"""Detector do formato de exemplo Mercado Livre.

Reconhece o relatório pelo conjunto de cabeçalhos — ver
`etl.transformers.mercado_livre` para o significado de cada coluna.
"""

from etl.detectors.base import MarketplaceDetector
from etl.types import Marketplace

REQUIRED_HEADERS: frozenset[str] = frozenset(
    {
        "numero_da_venda",
        "codigo_do_anuncio",
        "titulo_do_anuncio",
        "unidades",
        "valor_unitario",
        "percentual_de_desconto",
        "situacao_da_venda",
        "data_da_venda",
    }
)


class MercadoLivreDetector(MarketplaceDetector):
    marketplace = Marketplace.MERCADO_LIVRE

    def matches(self, headers: frozenset[str]) -> bool:
        return REQUIRED_HEADERS.issubset(headers)
