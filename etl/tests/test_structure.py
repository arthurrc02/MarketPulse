"""Testes estruturais do módulo ETL.

Garante que os contratos do pipeline existem, estão exportados corretamente
e que os dois marketplaces de exemplo da Sprint 4 (Shopee, Mercado Livre)
têm componentes registrados — sem testar o processamento em si, que tem
suíte própria (`test_pipeline.py`, `test_detectors.py`, etc.).
"""

import inspect

import pytest

from etl import Marketplace, get_pipeline_components
from etl.extractors import Extractor
from etl.loaders import Loader
from etl.transformers import Transformer


@pytest.mark.parametrize("contract", [Extractor, Transformer, Loader])
def test_stage_contracts_are_abstract(contract: type) -> None:
    """As três etapas do pipeline são classes abstratas."""
    assert inspect.isabstract(contract)


def test_supported_marketplaces() -> None:
    """Os marketplaces previstos na visão de produto estão declarados."""
    assert {m.value for m in Marketplace} == {
        "shopee",
        "mercado_livre",
        "amazon",
        "magalu",
    }


@pytest.mark.parametrize("marketplace", [Marketplace.SHOPEE, Marketplace.MERCADO_LIVRE])
def test_example_marketplaces_have_pipeline_components(marketplace: Marketplace) -> None:
    """Shopee e Mercado Livre (formatos de exemplo da Sprint 4) têm Extractor/Transformer."""
    extractor, transformer = get_pipeline_components(marketplace)
    assert extractor.marketplace is marketplace
    assert transformer.marketplace is marketplace


@pytest.mark.parametrize("marketplace", [Marketplace.AMAZON, Marketplace.MAGALU])
def test_unimplemented_marketplaces_raise(marketplace: Marketplace) -> None:
    """Amazon/Magalu estão no enum (visão de produto), mas sem implementação ainda."""
    from etl import UnknownMarketplaceError

    with pytest.raises(UnknownMarketplaceError):
        get_pipeline_components(marketplace)
