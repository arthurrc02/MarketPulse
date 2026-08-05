"""Etapa de transformação: converte dados brutos no modelo canônico."""

from etl.transformers.base import Transformer
from etl.transformers.mercado_livre import MercadoLivreTransformer
from etl.transformers.shopee import ShopeeTransformer

__all__ = ["MercadoLivreTransformer", "ShopeeTransformer", "Transformer"]
