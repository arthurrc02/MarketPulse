"""Contrato da detecção de marketplace."""

from abc import ABC, abstractmethod

from etl.types import Marketplace


class MarketplaceDetector(ABC):
    """Reconhece se um conjunto de cabeçalhos pertence a este marketplace.

    Deliberadamente sem IA (ver escopo da Sprint 4 em decisions.md): a
    identificação é baseada só nos nomes de coluna do cabeçalho — nenhum
    dado de conteúdo é inspecionado, então a detecção não abre nem o arquivo
    inteiro (ver `etl.parsing.peek_headers`).
    """

    #: Marketplace que este detector reconhece.
    marketplace: Marketplace

    @abstractmethod
    def matches(self, headers: frozenset[str]) -> bool:
        """`headers` já vêm normalizados (`etl.parsing.normalize_column_name`)."""
        raise NotImplementedError
