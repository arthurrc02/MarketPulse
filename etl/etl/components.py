"""Registro de qual `Extractor`/`Transformer` atende cada marketplace.

Ponto único de montagem do pipeline: quem orquestra (o backend) só sabe o
`Marketplace` detectado — não instancia `ShopeeExtractor`/`ShopeeTransformer`
diretamente, então adicionar um marketplace novo não toca a camada de
orquestração.
"""

from etl.exceptions import UnknownMarketplaceError
from etl.extractors.base import Extractor
from etl.extractors.mercado_livre import MercadoLivreExtractor
from etl.extractors.shopee import ShopeeExtractor
from etl.transformers.base import Transformer
from etl.transformers.mercado_livre import MercadoLivreTransformer
from etl.transformers.shopee import ShopeeTransformer
from etl.types import Marketplace

#: Um par (Extractor, Transformer) por marketplace com implementação nesta
#: sprint. `Marketplace.AMAZON`/`Marketplace.MAGALU` existem no enum (visão
#: de produto) mas não têm entrada aqui ainda — ver decisions.md.
_COMPONENTS: dict[Marketplace, tuple[type[Extractor], type[Transformer]]] = {
    Marketplace.SHOPEE: (ShopeeExtractor, ShopeeTransformer),
    Marketplace.MERCADO_LIVRE: (MercadoLivreExtractor, MercadoLivreTransformer),
}


def get_pipeline_components(marketplace: Marketplace) -> tuple[Extractor, Transformer]:
    """Instancia o par `Extractor`/`Transformer` do marketplace informado.

    Raises:
        UnknownMarketplaceError: marketplace sem implementação ainda (não
            deveria acontecer via `detect_marketplace`, que só devolve
            marketplaces com detector registrado — mas protege chamadas
            diretas, ex.: testes ou uma futura fila que reprocesse por id).
    """
    pair = _COMPONENTS.get(marketplace)
    if pair is None:
        raise UnknownMarketplaceError(
            f"Não há Extractor/Transformer implementados para {marketplace.value!r}."
        )
    extractor_cls, transformer_cls = pair
    return extractor_cls(), transformer_cls()
