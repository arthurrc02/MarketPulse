"""Contrato da etapa de extração."""

from abc import ABC, abstractmethod

import pandas as pd

from etl.parsing import FileSource
from etl.types import Marketplace


class Extractor(ABC):
    """Lê um arquivo de relatório e devolve seus dados brutos.

    Um extractor é responsável **apenas** por ler o arquivo: nenhuma
    renomeação de coluna, conversão de tipo ou regra de negócio acontece
    aqui — isso é papel do :class:`etl.transformers.base.Transformer`.

    Recebe um :class:`~etl.parsing.FileSource` (stream + formato), não um
    caminho em disco — o motor ETL não sabe (nem deveria saber) se o arquivo
    veio do storage local ou de um provedor de nuvem futuro (ver
    `FileStorage` em `backend/app/storage/`).
    """

    #: Marketplace atendido por esta implementação.
    marketplace: Marketplace

    @abstractmethod
    def extract(self, source: FileSource) -> pd.DataFrame:
        """Lê ``source`` e devolve o conteúdo bruto, sem transformações."""
        raise NotImplementedError
