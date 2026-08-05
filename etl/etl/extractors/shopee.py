"""Extractor do formato de exemplo Shopee."""

import pandas as pd

from etl.extractors.base import Extractor
from etl.parsing import FileSource, read_tabular_file
from etl.types import Marketplace


class ShopeeExtractor(Extractor):
    """Lê um relatório Shopee (CSV/XLSX) sem nenhuma transformação.

    A leitura em si é idêntica à de qualquer outro marketplace tabular (ver
    `read_tabular_file`) — a classe existe para que uma eventual
    particularidade da Shopee (ex.: linhas de rodapé, múltiplas planilhas)
    tenha onde entrar sem afetar outros marketplaces.
    """

    marketplace = Marketplace.SHOPEE

    def extract(self, source: FileSource) -> pd.DataFrame:
        return read_tabular_file(source)
