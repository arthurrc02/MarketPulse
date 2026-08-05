"""Extractor do formato de exemplo Mercado Livre."""

import pandas as pd

from etl.extractors.base import Extractor
from etl.parsing import FileSource, read_tabular_file
from etl.types import Marketplace


class MercadoLivreExtractor(Extractor):
    """Lê um relatório Mercado Livre (CSV/XLSX) sem nenhuma transformação."""

    marketplace = Marketplace.MERCADO_LIVRE

    def extract(self, source: FileSource) -> pd.DataFrame:
        return read_tabular_file(source)
