"""Testes de `etl.parsing`: normalização de cabeçalho e leitura tabular resiliente."""

import io

import pytest

from etl.exceptions import ExtractionError
from etl.parsing import FileSource, normalize_column_name, peek_headers, read_tabular_file
from etl.types import SourceFormat


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Data do Pedido", "data_do_pedido"),
        ("  SKU  ", "sku"),
        ("Preço  Unitário", "preço_unitário"),
        ("ALREADY_NORMALIZED", "already_normalized"),
    ],
)
def test_normalize_column_name(raw: str, expected: str) -> None:
    assert normalize_column_name(raw) == expected


def test_read_tabular_file_is_resilient_to_column_order_and_extra_columns() -> None:
    """Colunas fora de ordem e uma coluna extra não devem quebrar a leitura."""
    content = b"Coluna Extra,Data do Pedido,SKU\nignorar,05/08/2026,SKU-A\n"
    source = FileSource(stream=io.BytesIO(content), source_format=SourceFormat.CSV)

    frame = read_tabular_file(source)

    assert list(frame.columns) == ["coluna_extra", "data_do_pedido", "sku"]
    assert frame.loc[0, "sku"] == "SKU-A"


def test_read_tabular_file_normalizes_spacing_and_capitalization() -> None:
    content = b" ID do Pedido , sku \nX,Y\n"
    source = FileSource(stream=io.BytesIO(content), source_format=SourceFormat.CSV)

    frame = read_tabular_file(source)

    assert list(frame.columns) == ["id_do_pedido", "sku"]


def test_read_tabular_file_keeps_leading_zeros_as_text() -> None:
    """`dtype=str`: um SKU como `007` não vira o inteiro `7`."""
    content = b"sku\n007\n"
    source = FileSource(stream=io.BytesIO(content), source_format=SourceFormat.CSV)

    frame = read_tabular_file(source)

    assert frame.loc[0, "sku"] == "007"


def test_peek_headers_does_not_require_data_rows() -> None:
    content = b"ID do Pedido,SKU\n"
    source = FileSource(stream=io.BytesIO(content), source_format=SourceFormat.CSV)

    assert peek_headers(source) == ["id_do_pedido", "sku"]


def test_peek_headers_leaves_stream_readable_afterwards() -> None:
    """A detecção não pode "consumir" o stream — a extração real lê o mesmo `source` em seguida."""
    content = b"sku\nSKU-A\n"
    source = FileSource(stream=io.BytesIO(content), source_format=SourceFormat.CSV)

    peek_headers(source)
    frame = read_tabular_file(source)

    assert frame.loc[0, "sku"] == "SKU-A"


def test_read_tabular_file_wraps_parser_failures() -> None:
    """Um XLSX corrompido (bytes aleatórios) vira `ExtractionError`, não uma exceção do pandas."""
    source = FileSource(stream=io.BytesIO(b"isto nao e um xlsx"), source_format=SourceFormat.XLSX)

    with pytest.raises(ExtractionError):
        read_tabular_file(source)
