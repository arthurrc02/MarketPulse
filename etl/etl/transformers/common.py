"""Regras de normalização compartilhadas pelos transformers.

Centralizadas aqui — como pedido explicitamente no escopo da Sprint 4 — para
que datas, valores monetários, percentuais e identificadores sejam
interpretados da mesma forma em qualquer marketplace, em vez de cada
transformer reimplementar (e arriscar divergir de) o mesmo parsing.
"""

import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from etl.exceptions import TransformationError
from etl.schema import CANONICAL_COLUMNS
from etl.types import OrderStatus


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
    """`"R$ 1.234,56"` → `123456` (centavos).

    Valores monetários viram inteiro em centavos, não `float` — soma de
    ponto flutuante (faturamento, ticket médio, Sprint 5) acumula erro de
    arredondamento; centavos inteiros não.
    """
    text = str(value).strip().replace("R$", "").strip()
    text = text.replace(".", "").replace(",", ".")
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


def parse_date_brazilian(value: object) -> datetime.date:
    """`"05/08/2026"` (dia/mês/ano, formato dos relatórios BR) → `date(2026, 8, 5)`."""
    text = str(value).strip()
    try:
        return datetime.datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError as exc:
        raise TransformationError(f"data inválida: {value!r} (esperado dd/mm/aaaa)") from exc


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
