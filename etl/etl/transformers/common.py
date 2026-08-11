"""Regras de normalização compartilhadas pelos transformers.

Centralizadas aqui — como pedido explicitamente no escopo da Sprint 4 — para
que datas, valores monetários, percentuais e identificadores sejam
interpretados da mesma forma em qualquer marketplace, em vez de cada
transformer reimplementar (e arriscar divergir de) o mesmo parsing.
"""

import datetime
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

import pandas as pd

from etl.detectors.signature import signature_key
from etl.exceptions import TransformationError
from etl.parsing import normalize_column_name
from etl.schema import CANONICAL_COLUMNS
from etl.types import OrderStatus


def find_column(columns: Iterable[str], *readable_aliases: str) -> str | None:
    """Primeira coluna (já normalizada por `read_tabular_file`) que corresponde
    a uma das grafias aceitas — `None` se nenhuma existir.

    Mesma estratégia de aliases do hotfix da detecção (Sprint 4.1,
    `etl.detectors.signature.concept`), aplicada aqui à escolha de qual
    coluna ler para um campo, não a "este arquivo é deste marketplace?". Um
    transformer passa `readable_aliases` em texto legível (`"Nome do
    Produto"`); a normalização (`etl.parsing.normalize_column_name` — a
    mesma que já produziu `columns`) acontece aqui.
    """
    available = set(columns)
    for alias in readable_aliases:
        candidate = normalize_column_name(alias)
        if candidate in available:
            return candidate
    return None


def derive_sku_from_product_name(product_name: str) -> str:
    """Gera um SKU determinístico quando o arquivo não informa nenhum.

    Alguns relatórios reais chegam com as colunas de SKU em branco — o
    vendedor nunca preencheu a referência (caso observado no relatório
    oficial da Shopee, ver ADR-061 em decisions.md). Em vez de rejeitar a
    linha ou gerar um identificador aleatório (que impediria agrupar o
    mesmo produto entre pedidos diferentes na Sprint 5), deriva-se um SKU
    estável a partir do nome do produto — mesmo produto, mesmo SKU
    derivado — prefixado para deixar claro que não veio do arquivo.
    """
    slug = signature_key(product_name).upper()[:60]
    return f"AUTO-{slug}" if slug else "AUTO-PRODUTO-SEM-NOME"


def parse_identifier(value: object) -> str:
    """Normaliza um identificador (nº de pedido, SKU): só remove espaços.

    Nunca converte para número — identificadores podem ter zeros à esquerda
    ou caracteres não numéricos, e um `int()` os corromperia silenciosamente.
    """
    text = str(value).strip()
    if not text:
        raise TransformationError("identificador vazio")
    return text


def parse_text(value: object) -> str:
    """Normaliza um campo de texto livre (nome de produto etc.)."""
    text = str(value).strip()
    if not text:
        raise TransformationError("campo de texto vazio")
    return text


def parse_brl_currency_to_cents(value: object) -> int:
    """`"R$ 1.234,56"` → `123456` (centavos). Também aceita `"145.00"` (sem
    símbolo, ponto decimal — formato de exportações como a da Shopee, ver
    ADR-061 em decisions.md).

    Valores monetários viram inteiro em centavos, não `float` — soma de
    ponto flutuante (faturamento, ticket médio, Sprint 5) acumula erro de
    arredondamento; centavos inteiros não.
    """
    text = str(value).strip().replace("R$", "").strip()
    if "," in text:
        # Formato BR: ponto separa milhar, vírgula separa decimal ("1.234,56").
        text = text.replace(".", "").replace(",", ".")
    # Sem vírgula: já é decimal com ponto ("145.00") — nada a fazer.
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise TransformationError(f"valor monetário inválido: {value!r}") from exc
    return int((amount * 100).to_integral_value())


def parse_percentage(value: object) -> float | None:
    """`"10,5%"` → `10.5`. Texto vazio → `None` (campo opcional)."""
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("%", "").strip().replace(",", ".")
    try:
        percentage = float(text)
    except ValueError as exc:
        raise TransformationError(f"percentual inválido: {value!r}") from exc
    if not 0 <= percentage <= 100:
        raise TransformationError(f"percentual fora de 0-100: {percentage}")
    return percentage


def parse_quantity(value: object) -> int:
    """Normaliza uma quantidade — inteiro, nunca negativo."""
    text = str(value).strip()
    try:
        quantity = int(text)
    except ValueError as exc:
        raise TransformationError(f"quantidade inválida: {value!r}") from exc
    if quantity < 0:
        raise TransformationError(f"quantidade negativa: {quantity}")
    return quantity


# Um formato por layout já suportado — não um parser "flexível" que aceite
# qualquer coisa: `"2026-08-05"` (sem hora) fica de fora de propósito, para
# não passar a aceitar o que os testes de dado inválido verificam que deve
# falhar (ver ADR-061 em decisions.md).
_DATE_FORMATS: tuple[str, ...] = (
    "%d/%m/%Y",  # formato de exemplo (Sprint 4): "05/08/2026"
    "%Y-%m-%d %H:%M",  # relatório oficial Shopee (Seller Center): "2026-07-11 17:53"
)


def parse_date_brazilian(value: object) -> datetime.date:
    """`"05/08/2026"` ou `"2026-07-11 17:53"` → `date(...)` (ver `_DATE_FORMATS`)."""
    text = str(value).strip()
    for date_format in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise TransformationError(f"data inválida: {value!r}")


def map_status(value: object, mapping: dict[str, OrderStatus]) -> OrderStatus:
    """Traduz o status bruto do marketplace para `OrderStatus`.

    Um status não mapeado vira `OrderStatus.UNKNOWN` em vez de interromper o
    processamento do arquivo inteiro — um marketplace pode introduzir um
    status novo (ou grafar um já existente de outro jeito) sem que isso
    derrube a importação inteira (ver ADR em decisions.md).
    """
    normalized = str(value).strip().lower()
    return mapping.get(normalized, OrderStatus.UNKNOWN)


def build_canonical_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Monta o `DataFrame` canônico a partir das linhas já normalizadas.

    Não valida nada — isso é responsabilidade de
    `etl.schema.validate_canonical_schema`, chamada pelo `ETLPipeline` logo
    em seguida.
    """
    if not rows:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS), dtype=object)
    # `dtype=object`: sem isso, uma coluna que mistura `None` e `float`
    # (`discount_percentage`) é promovida para `float64` e cada `None` vira
    # `NaN` — mesmo reatribuindo `None` depois, um `float64` não consegue
    # guardar `None` de volta, só `NaN`. O Loader gravaria um `NaN` literal
    # no banco em vez de um `NULL` de verdade.
    return pd.DataFrame(rows, columns=list(CANONICAL_COLUMNS), dtype=object)
