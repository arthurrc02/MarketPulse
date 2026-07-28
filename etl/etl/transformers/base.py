"""Contrato da etapa de transformação."""

from abc import ABC, abstractmethod

import pandas as pd

from etl.types import Marketplace


class Transformer(ABC):
    """Padroniza os dados brutos de um marketplace no modelo canônico.

    Cada marketplace exporta colunas, nomes e formatos diferentes; o
    transformer é o único ponto do sistema que conhece esses detalhes.
    """

    #: Marketplace atendido por esta implementação.
    marketplace: Marketplace

    @abstractmethod
    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Converte ``raw`` para o esquema canônico de pedidos do MarketPulse."""
        raise NotImplementedError
