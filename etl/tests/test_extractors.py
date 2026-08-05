"""Testes dos extractors concretos (Shopee, Mercado Livre)."""

from collections.abc import Callable

from etl.extractors import MercadoLivreExtractor, ShopeeExtractor
from etl.parsing import FileSource
from etl.types import Marketplace


def test_shopee_extractor_reads_normalized_columns(shopee_source: FileSource) -> None:
    extractor = ShopeeExtractor()

    frame = extractor.extract(shopee_source)

    assert extractor.marketplace is Marketplace.SHOPEE
    assert "id_do_pedido" in frame.columns
    assert frame.loc[0, "sku"] == "SKU-A"


def test_mercado_livre_extractor_reads_normalized_columns(
    mercado_livre_source: FileSource,
) -> None:
    extractor = MercadoLivreExtractor()

    frame = extractor.extract(mercado_livre_source)

    assert extractor.marketplace is Marketplace.MERCADO_LIVRE
    assert "numero_da_venda" in frame.columns
    assert frame.loc[0, "codigo_do_anuncio"] == "ML-SKU-1"


def test_shopee_extractor_handles_multiple_rows(
    shopee_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> None:
    rows = (
        '1001,SKU-A,Camiseta Azul,2,"R$ 49,90",Concluido,05/08/2026\n'
        '1002,SKU-B,Bone Preto,1,"R$ 29,90",Pendente,06/08/2026'
    )
    source = make_source(shopee_csv(rows))

    frame = ShopeeExtractor().extract(source)

    assert len(frame) == 2
