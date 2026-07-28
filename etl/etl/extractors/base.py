"""Contrato da etapa de extração."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from etl.types import Marketplace


class Extractor(ABC):
    """Lê um arquivo de relatório e devolve seus dados brutos.

    Um extractor é responsável **apenas** por ler o arquivo: nenhuma
    renomeação de coluna, conversão de tipo ou regra de negócio acontece
    aqui — isso é papel do :class:`etl.transformers.base.Transformer`.
    """

    #: Marketplace atendido por esta implementação.
    marketplace: Marketplace

    @abstractmethod
    def extract(self, source: Path) -> pd.DataFrame:
        """Lê ``source`` e devolve o conteúdo bruto, sem transformações."""
        raise NotImplementedError
