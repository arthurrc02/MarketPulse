"""Hotfix Sprint 4.1 — detecção da Shopee por assinatura, não por lista fixa.

Um relatório oficial real (baixado do Seller Center, PT-BR, formato XLSX)
era rejeitado como "marketplace desconhecido": a estratégia anterior exigia
um conjunto fechado de colunas do formato de *exemplo* da Sprint 4, e
nenhum arquivo real usa exatamente esses nomes. Estes testes cobrem a nova
estratégia (`etl.detectors.signature`) contra cabeçalhos reais (CSV e
XLSX), variações de idioma, ordem, colunas extras, ausência de coluna
obrigatória e arquivos alheios.
"""

import io
from collections.abc import Callable

import openpyxl
import pytest

from etl.detectors import detect_marketplace
from etl.detectors.signature import signature_key
from etl.exceptions import UnknownMarketplaceError
from etl.parsing import FileSource, peek_headers
from etl.types import Marketplace, SourceFormat

# Cabeçalho real de um relatório oficial da Shopee (Seller Center, PT-BR),
# conforme reportado no hotfix — inclui colunas que o formato de exemplo da
# Sprint 4 nunca teve (Hot Listing, Cancelar Motivo, pesos, cupons etc.).
OFFICIAL_SHOPEE_PT_BR_HEADER = (
    "ID do pedido,Status do pedido,Hot Listing,Cancelar Motivo,"
    "Status da Devolução / Reembolso,Número de rastreamento,Opção de envio,"
    "Método de envio,Data prevista de envio,Tempo de Envio,"
    "Data de criação do pedido,Hora do pagamento do pedido,"
    "Nº de referência do SKU principal,Nome do Produto,"
    "Número de referência SKU,Nome da variação,Preço original,"
    "Preço acordado,Quantidade,Returned quantity,Subtotal do produto,"
    "Desconto do vendedor,Incentivo Shopee para ação comercial,"
    "Ajuste por participação em ação comercial,Peso total SKU,"
    "Número de produtos pedidos,Peso total do pedido,Código do Cupom,"
    "Cupom do vendedor,Valor Total\n"
)

SHOPEE_EN_HEADER = "Order ID,Order Status,Product Name,Quantity,Total Amount\n"


def _header_only_source(header_line: str, make_source: Callable[..., FileSource]) -> FileSource:
    """Detecção só olha o cabeçalho (`peek_headers`, `nrows=0`) — não precisa de linhas de dado."""
    return make_source(header_line.encode())


def test_official_shopee_report_pt_br_is_detected(
    make_source: Callable[..., FileSource],
) -> None:
    """Reprodução exata do bug do hotfix: o arquivo real não era mais rejeitado."""
    source = _header_only_source(OFFICIAL_SHOPEE_PT_BR_HEADER, make_source)

    headers = peek_headers(source)

    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_official_shopee_report_as_xlsx_is_detected() -> None:
    """O arquivo original do bug era um XLSX (Seller Center), não um CSV."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(OFFICIAL_SHOPEE_PT_BR_HEADER.strip().split(","))
    buffer = io.BytesIO()
    workbook.save(buffer)
    source = FileSource(stream=buffer, source_format=SourceFormat.XLSX)

    headers = peek_headers(source)

    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_shopee_report_in_english_is_detected(
    make_source: Callable[..., FileSource],
) -> None:
    source = _header_only_source(SHOPEE_EN_HEADER, make_source)

    headers = peek_headers(source)

    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_detection_ignores_column_order_in_official_report(
    make_source: Callable[..., FileSource],
) -> None:
    reordered = ",".join(reversed(OFFICIAL_SHOPEE_PT_BR_HEADER.strip().split(","))) + "\n"
    source = _header_only_source(reordered, make_source)

    headers = peek_headers(source)

    assert detect_marketplace(headers) is Marketplace.SHOPEE


def test_minimal_signature_with_unrelated_extra_columns_is_detected(
    make_source: Callable[..., FileSource],
) -> None:
    """Só os 5 conceitos da assinatura + colunas que nada têm a ver com Shopee."""
    header = (
        "ID do pedido,Cor Favorita,Status do pedido,Observações Internas,"
        "Nome do Produto,Quantidade,Valor Total,Comentário Aleatório\n"
    )
    source = _header_only_source(header, make_source)

    headers = peek_headers(source)

    assert detect_marketplace(headers) is Marketplace.SHOPEE


@pytest.mark.parametrize(
    "missing_concept_header",
    [
        "Status do pedido,Nome do Produto,Quantidade,Valor Total\n",  # falta ID do pedido
        "ID do pedido,Nome do Produto,Quantidade,Valor Total\n",  # falta Status
        "ID do pedido,Status do pedido,Quantidade,Valor Total\n",  # falta Nome do Produto
        "ID do pedido,Status do pedido,Nome do Produto,Valor Total\n",  # falta Quantidade
        "ID do pedido,Status do pedido,Nome do Produto,Quantidade\n",  # falta Valor Total
    ],
    ids=["sem_id", "sem_status", "sem_produto", "sem_quantidade", "sem_valor"],
)
def test_missing_one_required_concept_is_not_detected(
    missing_concept_header: str, make_source: Callable[..., FileSource]
) -> None:
    """A assinatura exige os 5 conceitos simultaneamente — faltar um já basta para rejeitar."""
    source = _header_only_source(missing_concept_header, make_source)
    headers = peek_headers(source)

    with pytest.raises(UnknownMarketplaceError):
        detect_marketplace(headers)


def test_unrelated_spreadsheet_is_not_detected_as_shopee(
    make_source: Callable[..., FileSource],
) -> None:
    header = "Nome do Funcionário,Departamento,Salário,Data de Admissão\n"
    source = _header_only_source(header, make_source)
    headers = peek_headers(source)

    with pytest.raises(UnknownMarketplaceError):
        detect_marketplace(headers)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ID do pedido", "iddopedido"),
        ("Id do  Pedido", "iddopedido"),
        ("id do pedido", "iddopedido"),
        ("  ID   do   Pedido  ", "iddopedido"),
        ("id_do_pedido", "iddopedido"),  # já normalizado por peek_headers
        ("Preço acordado", "precoacordado"),
        ("PREÇO ACORDADO", "precoacordado"),
    ],
)
def test_signature_key_normalizes_case_spacing_and_accents(raw: str, expected: str) -> None:
    assert signature_key(raw) == expected
