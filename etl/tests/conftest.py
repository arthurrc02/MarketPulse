"""Fixtures compartilhadas pelos testes do módulo ETL.

Os builders de CSV de exemplo são expostos como *fixtures que retornam uma
função* (não como funções importáveis de um módulo comum): dois diretórios
`tests/` no mesmo repositório (`backend/tests`, `etl/tests`) formam um
namespace package compartilhado (ver ADR-012 em `docs/decisions.md`) — um
`from .helpers import ...` entre arquivos de teste resolveria de forma
ambígua. Fixtures não têm esse problema: o pytest as injeta pelo nome do
parâmetro, sem passar por um `import`.
"""

import io
from collections.abc import Callable

import pytest

from etl.parsing import FileSource
from etl.types import SourceFormat

_SHOPEE_HEADER = "ID do Pedido,SKU,Produto,Quantidade,Preco Unitario,Status,Data do Pedido"
_SHOPEE_DEFAULT_ROW = '1001,SKU-A,Camiseta Azul,2,"R$ 49,90",Concluido,05/08/2026'

_MERCADO_LIVRE_HEADER = (
    "Numero da Venda,Codigo do Anuncio,Titulo do Anuncio,Unidades,Valor Unitario,"
    "Percentual de Desconto,Situacao da Venda,Data da Venda"
)
_MERCADO_LIVRE_DEFAULT_ROW = 'V-1,ML-SKU-1,Fone Bluetooth,3,"R$ 199,90","10,5%",Entregue,04/08/2026'


@pytest.fixture
def shopee_csv() -> Callable[[str], bytes]:
    """Fábrica de CSV Shopee de exemplo; aceita linhas de dados customizadas."""

    def _build(rows: str = _SHOPEE_DEFAULT_ROW) -> bytes:
        return f"{_SHOPEE_HEADER}\n{rows}\n".encode()

    return _build


@pytest.fixture
def mercado_livre_csv() -> Callable[[str], bytes]:
    """Fábrica de CSV Mercado Livre de exemplo; aceita linhas de dados customizadas."""

    def _build(rows: str = _MERCADO_LIVRE_DEFAULT_ROW) -> bytes:
        return f"{_MERCADO_LIVRE_HEADER}\n{rows}\n".encode()

    return _build


@pytest.fixture
def make_source() -> Callable[..., FileSource]:
    """Fábrica de `FileSource` a partir de bytes crus (CSV por padrão)."""

    def _build(content: bytes, source_format: SourceFormat = SourceFormat.CSV) -> FileSource:
        return FileSource(stream=io.BytesIO(content), source_format=source_format)

    return _build


@pytest.fixture
def shopee_source(
    shopee_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> FileSource:
    return make_source(shopee_csv())


@pytest.fixture
def mercado_livre_source(
    mercado_livre_csv: Callable[[str], bytes], make_source: Callable[..., FileSource]
) -> FileSource:
    return make_source(mercado_livre_csv())
