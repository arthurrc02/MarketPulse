"""Etapa de extração: lê o arquivo de origem e devolve um ``DataFrame`` bruto."""

from etl.extractors.base import Extractor
from etl.extractors.mercado_livre import MercadoLivreExtractor
from etl.extractors.shopee import ShopeeExtractor

__all__ = ["Extractor", "MercadoLivreExtractor", "ShopeeExtractor"]
