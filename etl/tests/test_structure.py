"""Testes estruturais do módulo ETL.

A Sprint 0 não implementa processamento; estes testes apenas garantem que os
contratos do pipeline existem e estão exportados corretamente.
"""

import inspect

import pytest

from etl import ETLPipeline, Marketplace
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


def test_pipeline_run_is_not_implemented_yet() -> None:
    """A execução do pipeline é explicitamente adiada para a Sprint 4."""
    assert ETLPipeline.run.__doc__ is not None
    assert "Sprint 4" in ETLPipeline.run.__doc__
